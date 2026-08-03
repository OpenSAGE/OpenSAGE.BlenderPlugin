# <pep8 compliant>
"""Asset cache for the BfMe tools.

Extracts textures and models from .big archives and from user configured search
paths into a cache directory, so they can be found by name later on.

This module deliberately contains no 'bpy' access at all: the operators snapshot
whatever they need from the scene on the main thread and hand plain data in here.
The Blender API is not thread safe, so everything that runs in a worker thread has
to stay on this side of the fence.
"""

import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice

from .vendor.pyBIG import InDiskArchive

SUPPORTED_EXTENSIONS = {'.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp'}
CACHE_EXTENSIONS = {'.dds', '.tga', '.w3d'}

BIG_CACHE_DIR = os.path.join(tempfile.gettempdir(), 'bfme_big_cache')
CACHE_INDEX_FILE = os.path.join(tempfile.gettempdir(), 'bfme_cache_index.json')

MAX_WORKERS = 4
HASH_CHUNK_SIZE = 1024 * 1024

# how many entries of a cached index are sampled to verify it still matches the disk
CACHE_SAMPLE_SIZE = 100

_index_lock = threading.Lock()
_global_cache_index = None

_file_sizes_lock = threading.Lock()
# (directory mtime, {filename: size}), the mtime is kept next to the data instead of
# inside it so a file called '__mtime__' cannot collide with the bookkeeping
_cached_file_sizes = (None, {})


##########################################################################
# cache index
##########################################################################


def load_cache_index():
    global _global_cache_index

    with _index_lock:
        if _global_cache_index is not None:
            return _global_cache_index

        try:
            with open(CACHE_INDEX_FILE, 'r') as file:
                _global_cache_index = json.load(file)
        except (OSError, ValueError):
            _global_cache_index = {}
        return _global_cache_index


def save_cache_index(index):
    global _global_cache_index

    with _index_lock:
        _global_cache_index = index
        try:
            with open(CACHE_INDEX_FILE, 'w') as file:
                json.dump(index, file)
        except OSError:
            pass


def invalidate_cache_index():
    global _global_cache_index

    with _index_lock:
        _global_cache_index = None


##########################################################################
# cache directory bookkeeping
##########################################################################


def ensure_cache_dir():
    try:
        os.makedirs(BIG_CACHE_DIR, exist_ok=True)
    except OSError:
        pass


def get_cached_file_sizes():
    """Map of filename -> size for everything in the cache directory.

    Built with a single scandir pass, which carries the size along with the
    directory entry, instead of an exists() plus getsize() call per file. The
    result is reused until the directory itself changes.
    """
    global _cached_file_sizes

    with _file_sizes_lock:
        try:
            dir_mtime = os.path.getmtime(BIG_CACHE_DIR)
        except OSError:
            _cached_file_sizes = (None, {})
            return {}

        cached_mtime, sizes = _cached_file_sizes
        if cached_mtime == dir_mtime:
            return sizes

        sizes = {}
        try:
            with os.scandir(BIG_CACHE_DIR) as entries:
                for entry in entries:
                    try:
                        if entry.is_file():
                            sizes[entry.name] = entry.stat().st_size
                    except OSError:
                        continue
        except OSError:
            _cached_file_sizes = (None, {})
            return {}

        _cached_file_sizes = (dir_mtime, sizes)
        return sizes


def invalidate_cached_file_sizes():
    global _cached_file_sizes

    with _file_sizes_lock:
        _cached_file_sizes = (None, {})


def _sample_still_on_disk(paths):
    return all(os.path.exists(path) for path in islice(paths, CACHE_SAMPLE_SIZE))


##########################################################################
# hashing
##########################################################################


def hash_file(filepath, chunk_size=HASH_CHUNK_SIZE):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_file_with_hash(src_path, dst_path, chunk_size=HASH_CHUNK_SIZE):
    """Copy and hash in one pass, so the source is only read once."""
    hasher = hashlib.sha1()
    temp_path = dst_path + '.tmp'
    try:
        with open(src_path, 'rb') as src, open(temp_path, 'wb') as dst:
            for chunk in iter(lambda: src.read(chunk_size), b''):
                hasher.update(chunk)
                dst.write(chunk)
        try:
            shutil.copystat(src_path, temp_path)
        except OSError:
            pass
        os.replace(temp_path, dst_path)
        return hasher.hexdigest()
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


##########################################################################
# .big archives
##########################################################################


def gather_big_filepaths(root_path):
    bigs = []
    if not root_path or not os.path.isdir(root_path):
        return bigs
    for directory, _, files in os.walk(root_path):
        for file in files:
            if file.lower().endswith('.big'):
                bigs.append(os.path.join(directory, file))
    return bigs


def path_signature(filepaths):
    """(path, mtime, size) triples used to detect that the inputs changed."""
    signature = []
    for filepath in filepaths:
        try:
            stat = os.stat(filepath)
        except OSError:
            continue
        signature.append([filepath, stat.st_mtime, stat.st_size])
    signature.sort()
    return signature


def _extract_from_single_big(big_path, wanted_exts, cached_file_sizes):
    """Extract the wanted entries of one archive, skipping what is already cached.

    'cached_file_sizes' is read only here, every worker reports what it wrote back
    through its return value instead of mutating shared state.
    """
    index = {}
    written = {}
    extracted = 0
    skipped = 0

    try:
        archive = InDiskArchive(big_path)
    except Exception as error:
        print(f'[BFME_CACHE] could not open {os.path.basename(big_path)}: {error}')
        return index, written

    try:
        for entry_name, entry in archive.entries.items():
            if os.path.splitext(entry_name)[1].lower() not in wanted_exts:
                continue

            out_filename = os.path.basename(entry_name)
            out_path = os.path.join(BIG_CACHE_DIR, out_filename)

            expected_size = getattr(entry, 'size', None)
            cached_size = written.get(out_filename, cached_file_sizes.get(out_filename))

            if cached_size is not None and expected_size is not None and cached_size == expected_size:
                skipped += 1
            else:
                try:
                    data = archive.read_file(entry_name)
                    temp_path = out_path + '.tmp'
                    with open(temp_path, 'wb') as file:
                        file.write(data)
                    os.replace(temp_path, out_path)
                    written[out_filename] = len(data)
                    extracted += 1
                except Exception:
                    continue

            index.setdefault(os.path.splitext(out_filename)[0].lower(), out_path)
    finally:
        close = getattr(archive, 'close', None)
        if close is not None:
            try:
                close()
            except Exception:
                pass

    if extracted or skipped:
        print(f'[BFME_CACHE] {os.path.basename(big_path)}: {extracted} extracted, {skipped} already cached')
    return index, written


def extract_bigs(big_paths, wanted_exts, force_refresh=False):
    """Extract 'wanted_exts' out of the given archives, returns basename -> path."""
    if not big_paths:
        return {}

    ensure_cache_dir()

    cache_index = load_cache_index()
    signature = path_signature(big_paths)

    if not force_refresh and signature == cache_index.get('big_signature') and 'files' in cache_index:
        cached_files = cache_index['files']
        if _sample_still_on_disk(cached_files.values()):
            print(f'[BFME_CACHE] using cached .big extraction ({len(cached_files)} files)')
            return cached_files

    print(f'[BFME_CACHE] extracting from {len(big_paths)} .big files using {MAX_WORKERS} threads')

    cached_file_sizes = get_cached_file_sizes()
    combined = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(_extract_from_single_big, big_path, wanted_exts, cached_file_sizes)
            for big_path in big_paths]

        for future in as_completed(futures):
            try:
                index, _ = future.result()
            except Exception as error:
                print(f'[BFME_CACHE] extraction thread failed: {error}')
                continue
            # first archive that provides a name wins, the caller ordered them by priority
            for key, value in index.items():
                combined.setdefault(key, value)

    invalidate_cached_file_sizes()

    new_index = dict(load_cache_index())
    new_index['big_signature'] = signature
    new_index['files'] = combined
    new_index['timestamp'] = time.time()
    save_cache_index(new_index)

    print(f'[BFME_CACHE] extraction complete: {len(combined)} files cached')
    return combined


##########################################################################
# search paths
##########################################################################


def _process_search_path_file(src_path, filename, cached_file_sizes, previous_meta):
    """Copy one source file into the cache unless an identical copy is already there.

    Size and mtime are checked first because they are free, the content hash is only
    computed when those are inconclusive.
    """
    dst_path = os.path.join(BIG_CACHE_DIR, filename)
    try:
        stat = os.stat(src_path)
    except OSError:
        return ('error', filename, dst_path, None)

    src_size = stat.st_size
    src_mtime = stat.st_mtime

    cached_size = cached_file_sizes.get(filename)
    meta = previous_meta.get(filename) or {}

    if cached_size is not None and cached_size == src_size:
        cached_hash = meta.get('hash')
        cached_cache_mtime = meta.get('cache_mtime')

        # unchanged source and untouched cache copy, nothing to verify
        if cached_hash and meta.get('mtime') == src_mtime:
            try:
                current_cache_mtime = os.path.getmtime(dst_path)
            except OSError:
                current_cache_mtime = None
            if cached_cache_mtime is None or current_cache_mtime == cached_cache_mtime:
                return ('skipped', filename, dst_path, {
                    'size': src_size,
                    'mtime': src_mtime,
                    'hash': cached_hash,
                    'cache_mtime': cached_cache_mtime or current_cache_mtime})

        # same size but the timestamps disagree, fall back to comparing content
        try:
            src_hash = hash_file(src_path)
        except OSError:
            src_hash = None

        if src_hash is not None:
            if not cached_hash:
                try:
                    cached_hash = hash_file(dst_path)
                except OSError:
                    cached_hash = None

            if cached_hash == src_hash:
                try:
                    cache_mtime = os.path.getmtime(dst_path)
                except OSError:
                    cache_mtime = None
                return ('skipped', filename, dst_path, {
                    'size': src_size,
                    'mtime': src_mtime,
                    'hash': src_hash,
                    'cache_mtime': cache_mtime})

    try:
        src_hash = copy_file_with_hash(src_path, dst_path)
    except Exception:
        return ('error', filename, dst_path, {'size': src_size, 'mtime': src_mtime})

    try:
        cache_mtime = os.path.getmtime(dst_path)
    except OSError:
        cache_mtime = src_mtime

    return ('copied', filename, dst_path, {
        'size': src_size,
        'mtime': src_mtime,
        'hash': src_hash,
        'cache_mtime': cache_mtime})


def cache_search_path_files(search_paths, force_refresh=False, progress=None):
    """Copy cacheable files from the given directories into the cache."""
    if not search_paths:
        return {}

    ensure_cache_dir()

    full_index = load_cache_index()
    signature = path_signature(search_paths)

    if (not force_refresh and signature == full_index.get('search_paths_signature')
            and 'search_path_files' in full_index):
        cached_files = full_index['search_path_files']
        if _sample_still_on_disk(cached_files.values()):
            print(f'[BFME_CACHE] using cached search path files ({len(cached_files)} files)')
            return cached_files
        print('[BFME_CACHE] cached search path files are missing, re-caching')

    # last source wins per filename, matching the previous behaviour
    file_map = {}
    for root_path in search_paths:
        for directory, _, files in os.walk(root_path):
            for filename in files:
                if os.path.splitext(filename)[1].lower() in CACHE_EXTENSIONS:
                    file_map[filename] = os.path.join(directory, filename)

    if not file_map:
        return {}

    cached_file_sizes = get_cached_file_sizes()
    previous_meta = full_index.get('search_path_file_meta') or {}
    if not isinstance(previous_meta, dict):
        previous_meta = {}

    index = {}
    new_meta = {}
    counts = {'copied': 0, 'skipped': 0, 'error': 0}
    total = len(file_map)
    processed = 0

    def handle(result):
        nonlocal processed
        processed += 1
        if progress is not None and processed % 100 == 0:
            progress(processed, total)
        if result is None:
            return
        action, filename, dst_path, meta = result
        index[os.path.splitext(filename)[0].lower()] = dst_path
        if meta is not None:
            new_meta[filename] = meta
        counts[action] = counts.get(action, 0) + 1

    workers = min(MAX_WORKERS, total)
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(_process_search_path_file, src_path, filename, cached_file_sizes, previous_meta)
                for filename, src_path in file_map.items()]
            for future in as_completed(futures):
                try:
                    handle(future.result())
                except Exception:
                    handle(None)
    else:
        for filename, src_path in file_map.items():
            handle(_process_search_path_file(src_path, filename, cached_file_sizes, previous_meta))

    invalidate_cached_file_sizes()

    new_index = dict(load_cache_index())
    new_index['search_paths_signature'] = signature
    new_index['search_path_files'] = index
    new_index['search_path_file_meta'] = new_meta
    save_cache_index(new_index)

    print(f'[BFME_CACHE] search paths: {counts["copied"]} copied, {counts["skipped"]} already cached')
    return index


##########################################################################
# maintenance
##########################################################################


def clear(extra_dirs=(), extra_files=()):
    """Remove the cache directory, the index and any extra paths handed in."""
    for directory in (BIG_CACHE_DIR, *extra_dirs):
        if directory and os.path.isdir(directory):
            shutil.rmtree(directory, ignore_errors=True)

    for filepath in (CACHE_INDEX_FILE, *extra_files):
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    invalidate_cache_index()
    invalidate_cached_file_sizes()


def cache_stats():
    index = load_cache_index()
    return len(index.get('files', {})), len(index.get('search_path_files', {}))
