# <pep8 compliant>
"""Asset index for the BfMe tools.

Assets live either as loose files in a user configured search path, or as entries
inside a .big archive. Rather than copying everything into a cache directory up
front, this module builds an index of *references* to where each asset actually
is, and only materialises an asset on disk when something really needs a file.

A reference is one of:

    ['file', path]                              a loose file, used directly
    ['big', archive, entry, position, size]     an entry inside a .big archive

Loose files are never copied at all. Archive entries carry the byte range of the
entry, so materialising one is a plain seek and read, without re-parsing the
archive. Blender cannot read from inside a .big, which is the only reason
anything gets written to the cache directory at all.

This module deliberately contains no 'bpy' access: the operators snapshot
whatever they need from the scene on the main thread and hand plain data in here.
The Blender API is not thread safe, so everything that runs in a worker thread has
to stay on this side of the fence.
"""

import os
import shutil
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

from . import dependencies
from .vendor.pyBIG import InDiskArchive

SUPPORTED_EXTENSIONS = {'.dds', '.tga', '.jpg', '.jpeg', '.png', '.bmp'}
CACHE_EXTENSIONS = {'.dds', '.tga', '.w3d'}

BIG_CACHE_DIR = os.path.join(tempfile.gettempdir(), 'bfme_big_cache')
# only removed by clear(), the previous implementation used it to remember which
# files it had copied where
LEGACY_CACHE_INDEX_FILE = os.path.join(tempfile.gettempdir(), 'bfme_cache_index.json')

MAX_WORKERS = 4
READ_CHUNK_SIZE = 256 * 1024

REF_FILE = 'file'
REF_BIG = 'big'

_index_lock = threading.RLock()
# (signature, {key: ref}), rebuilt when the inputs change. Kept in memory only:
# rebuilding takes well under a second even for a full BfMe install, which is not
# worth the staleness bugs a persisted copy would bring
_asset_index = (None, {})

_materialise_lock = threading.Lock()


##########################################################################
# discovery
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
        signature.append((filepath, stat.st_mtime, stat.st_size))
    signature.sort()
    return tuple(signature)


def asset_key(name):
    """Assets are looked up by file name without extension, case insensitively."""
    return os.path.splitext(os.path.basename(name))[0].lower()


##########################################################################
# index building
##########################################################################


def _is_model_extension(ext):
    return ext == '.w3d'


def _index_archive(big_path, wanted_exts):
    """Reference every wanted entry of one archive, without reading any file data.

    Opening an archive only parses its entry table, so this stays cheap even for
    multi gigabyte archives. Returns (all references, models only, textures only):
    a texture and an unrelated .w3d file can share a base name (a 'pfence01'
    texture next to an unrelated 'pfence01.w3d' prop model, for instance), and if
    they were merged into one dict here already, whichever came first would
    silently win before the caller ever gets a chance to keep both.
    """
    references = {}
    model_references = {}
    texture_references = {}
    try:
        archive = InDiskArchive(big_path)
    except Exception as error:
        print(f'[BFME_CACHE] could not open {os.path.basename(big_path)}: {error}')
        return references, model_references, texture_references

    for entry_name, entry in archive.entries.items():
        ext = os.path.splitext(entry_name)[1].lower()
        if ext not in wanted_exts:
            continue
        key = asset_key(entry_name)
        reference = [REF_BIG, big_path, entry_name, entry.position, entry.size]
        references.setdefault(key, reference)
        bucket = model_references if _is_model_extension(ext) else texture_references
        bucket.setdefault(key, reference)

    return references, model_references, texture_references


def _index_search_path(root_path, wanted_exts):
    """Reference every wanted loose file below a search path. Nothing is copied.

    Returns (all references, models only, textures only), see _index_archive().
    """
    references = {}
    model_references = {}
    texture_references = {}
    for directory, _, files in os.walk(root_path):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in wanted_exts:
                continue
            key = asset_key(filename)
            reference = [REF_FILE, os.path.join(directory, filename)]
            references[key] = reference
            bucket = model_references if _is_model_extension(ext) else texture_references
            bucket[key] = reference
    return references, model_references, texture_references


class AssetIndex(dict):
    """A flat asset key -> reference map, plus same-name texture/model buckets.

    A texture and an unrelated .w3d file can share a base name in the real asset
    libraries (a 'pfence01' texture next to an unrelated 'pfence01.w3d' prop
    model, for instance). The flat mapping only keeps one of the two - whichever
    wins the same priority order as everything else - so dependency resolution
    looks names up in 'textures' or 'models' instead, which cannot shadow one
    another. Behaves exactly like a plain dict otherwise.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textures = {}
        self.models = {}


def build_asset_index(big_paths, search_paths, wanted_exts, progress=None):
    """Map asset key -> reference for everything reachable, copying nothing.

    Archives are indexed in the order they are handed in, first one to provide a
    name wins. Loose search path files are applied afterwards and override the
    archives, matching how the caches used to be layered. Archives and search
    paths are all walked in one shared thread pool so the (I/O bound) work runs
    concurrently; the merge order below is what keeps the result deterministic,
    not the order threads happen to finish in.
    """
    index = AssetIndex()
    valid_search_paths = [path for path in search_paths if os.path.isdir(path)]

    if not big_paths and not valid_search_paths:
        return index

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        archive_futures = [executor.submit(_index_archive, big_path, wanted_exts)
                            for big_path in big_paths]
        search_futures = [executor.submit(_index_search_path, path, wanted_exts)
                           for path in valid_search_paths]

        # results are merged in submission order rather than completion order, so
        # which archive wins a name does not depend on thread scheduling
        for done, future in enumerate(archive_futures, start=1):
            try:
                references, model_references, texture_references = future.result()
            except Exception as error:
                print(f'[BFME_CACHE] indexing thread failed: {error}')
                continue
            for key, reference in references.items():
                index.setdefault(key, reference)
            for key, reference in model_references.items():
                index.models.setdefault(key, reference)
            for key, reference in texture_references.items():
                index.textures.setdefault(key, reference)
            if progress is not None:
                progress(done, len(archive_futures))

        # loose files override archives; later search paths override earlier ones,
        # same priority order the sequential version used
        for future in search_futures:
            try:
                references, model_references, texture_references = future.result()
            except Exception as error:
                print(f'[BFME_CACHE] indexing thread failed: {error}')
                continue
            index.update(references)
            index.models.update(model_references)
            index.textures.update(texture_references)

    return index


def asset_index(big_paths, search_paths, wanted_exts, force_refresh=False, progress=None):
    """Cached wrapper around build_asset_index, rebuilt when the inputs change."""
    global _asset_index

    signature = (path_signature(big_paths), path_signature(search_paths), tuple(sorted(wanted_exts)))

    with _index_lock:
        cached_signature, index = _asset_index
        if not force_refresh and cached_signature == signature:
            return index

        index = build_asset_index(big_paths, search_paths, wanted_exts, progress=progress)
        _asset_index = (signature, index)

        archives = sum(1 for ref in index.values() if ref[0] == REF_BIG)
        print(f'[BFME_CACHE] indexed {len(index)} assets '
              f'({archives} in archives, {len(index) - archives} loose)')
        return index


def invalidate_asset_index():
    global _asset_index

    with _index_lock:
        _asset_index = (None, {})


def cached_asset_index():
    """The index as it currently stands, without building one.

    Deliberately does not take _index_lock: a background rebuild holds that lock
    for as long as the rebuild takes, and this is called from the main thread on
    import and preview, where blocking on it is a visible freeze. _asset_index is
    only ever replaced by a single tuple assignment, which is atomic, so reading
    it without the lock yields either the old index or the new one, never a torn
    one.
    """
    return _asset_index[1]


##########################################################################
# reading and materialising
##########################################################################


def ensure_cache_dir():
    try:
        os.makedirs(BIG_CACHE_DIR, exist_ok=True)
    except OSError:
        pass


def asset_name(reference):
    """The file name an asset would have on disk."""
    if reference[0] == REF_FILE:
        return os.path.basename(reference[1])
    return os.path.basename(reference[2])


def asset_size(reference):
    if reference[0] == REF_BIG:
        return reference[4]
    try:
        return os.path.getsize(reference[1])
    except OSError:
        return None


def iter_asset_chunks(reference, chunk_size=READ_CHUNK_SIZE):
    """Yield the asset's bytes without materialising it on disk."""
    if reference[0] == REF_FILE:
        try:
            with open(reference[1], 'rb') as file:
                for chunk in iter(lambda: file.read(chunk_size), b''):
                    yield chunk
        except OSError:
            return
        return

    _, archive_path, _, position, size = reference
    try:
        with open(archive_path, 'rb') as file:
            file.seek(position)
            remaining = size
            while remaining > 0:
                chunk = file.read(min(chunk_size, remaining))
                if not chunk:
                    return
                remaining -= len(chunk)
                yield chunk
    except OSError:
        return


def read_asset(reference):
    """The asset's full contents, without materialising it on disk."""
    return b''.join(iter_asset_chunks(reference))


def asset_contains(reference, needle, chunk_size=READ_CHUNK_SIZE):
    """Whether the asset contains the byte string, streamed rather than read whole.

    The tail of each chunk is carried over so a match spanning a chunk boundary is
    still found.
    """
    overlap = len(needle) - 1
    if overlap < 0:
        return True

    tail = b''
    for chunk in iter_asset_chunks(reference, chunk_size):
        buffer = tail + chunk
        if needle in buffer:
            return True
        tail = buffer[-overlap:] if overlap else b''
    return False


def materialise(reference):
    """Write the asset into the cache directory and return its path.

    Reused when a copy of the right size is already there, so repeated imports of
    the same model do not rewrite it.
    """
    target = os.path.join(BIG_CACHE_DIR, asset_name(reference))
    size = asset_size(reference)

    try:
        if os.path.getsize(target) == size:
            return target
    except OSError:
        pass

    ensure_cache_dir()

    # serialised so two threads materialising the same asset cannot interleave
    # their writes; the work itself is a seek and a read, so the lock is held briefly
    with _materialise_lock:
        try:
            if os.path.getsize(target) == size:
                return target
        except OSError:
            pass

        temp_path = f'{target}.{os.getpid()}.{threading.get_ident()}.tmp'
        try:
            with open(temp_path, 'wb') as file:
                for chunk in iter_asset_chunks(reference):
                    file.write(chunk)
            os.replace(temp_path, target)
        except OSError as error:
            print(f'[BFME_CACHE] could not materialise {asset_name(reference)}: {error}')
            try:
                os.remove(temp_path)
            except OSError:
                pass
            return None

    return target


def resolve(reference):
    """A real filesystem path for the asset, extracting it only if it has to be.

    Loose files are returned as they are, nothing is copied. Archive entries are
    written into the cache directory once and reused afterwards, so that Blender,
    which cannot read from inside a .big, has a file to open.
    """
    if reference is None:
        return None

    if reference[0] == REF_FILE:
        path = reference[1]
        return path if os.path.exists(path) else None

    return materialise(reference)


def resolve_key(index, key):
    return resolve(index.get(key))


MAX_DEPENDENCY_DEPTH = 4


def dependency_keys(index, key):
    """Every asset the given model pulls in, transitively, as {name: reference}.

    A model names its skeleton and its textures; a skeleton can in turn name
    further files, so references are followed until nothing new turns up.
    Texture and hierarchy names are looked up in their own bucket rather than
    the flat index: a texture and an unrelated .w3d file can share a base name
    in the real asset libraries, and the flat index only keeps one of the two.
    """
    models = getattr(index, 'models', index)
    textures = getattr(index, 'textures', index)

    collected = {}
    pending = {key}

    for _ in range(MAX_DEPENDENCY_DEPTH):
        texture_names = set()
        hierarchy_names = set()
        for current in pending:
            # only w3d files reference anything, textures are leaves
            reference = models.get(current)
            if reference is not None:
                found_textures, found_hierarchies = dependencies.referenced_names_by_kind(read_asset(reference))
                texture_names |= found_textures
                hierarchy_names |= found_hierarchies

        pending = set()
        for name in hierarchy_names:
            if name == key or name in collected:
                continue
            reference = models.get(name)
            if reference is not None:
                collected[name] = reference
                pending.add(name)  # only hierarchies can reference anything further
        for name in texture_names:
            if name == key or name in collected:
                continue
            reference = textures.get(name)
            if reference is not None:
                collected[name] = reference

        if not pending:
            break

    return collected


def stage_for_import(index, key):
    """Put a model and everything it needs in one directory, and return its path.

    The W3D importer resolves a model's skeleton and textures by name relative to
    the file it is importing, so they have to sit next to it. A loose model whose
    dependencies are already beside it is imported where it lies and nothing is
    copied; otherwise the model and its dependencies are gathered in the cache
    directory, which is the only case where anything gets written.
    """
    reference = index.get(key)
    if reference is None:
        return None

    needed = dependency_keys(index, key)

    if reference[0] == REF_FILE:
        directory = os.path.dirname(reference[1])
        if all(_sits_in(dep_reference, directory) for dep_reference in needed.values()):
            return resolve(reference)

    path = materialise(reference)
    if path is None:
        return None

    for dep_reference in needed.values():
        materialise(dep_reference)

    return path


def _sits_in(reference, directory):
    """Whether the asset is already a loose file in the given directory."""
    return (reference is not None
            and reference[0] == REF_FILE
            and os.path.dirname(reference[1]) == directory
            and os.path.exists(reference[1]))


##########################################################################
# maintenance
##########################################################################


def clear(extra_dirs=(), extra_files=()):
    """Remove everything that was materialised, plus any extra paths handed in."""
    for directory in (BIG_CACHE_DIR, *extra_dirs):
        if directory and os.path.isdir(directory):
            shutil.rmtree(directory, ignore_errors=True)

    for filepath in (LEGACY_CACHE_INDEX_FILE, *extra_files):
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    invalidate_asset_index()


def materialised_count():
    try:
        with os.scandir(BIG_CACHE_DIR) as entries:
            return sum(1 for entry in entries if entry.is_file())
    except OSError:
        return 0


def cache_stats():
    """(indexed assets, files actually materialised on disk), cheap enough to draw."""
    return len(cached_asset_index()), materialised_count()
