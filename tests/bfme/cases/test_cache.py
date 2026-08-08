# <pep8 compliant>
# Tests for the BfMe asset index.
#
# These run against the real bpy inside Blender like the rest of the suite. The
# original bfme tests installed a MagicMock as sys.modules['bpy'], which would have
# replaced bpy for every other test sharing this process.

import os
import shutil
import struct
import tempfile

from io_mesh_w3d.bfme import cache
from tests.utils import TestCase


def write_big_archive(path, entries):
    """Write a minimal BIG4 archive containing the given {name: bytes}.

    Built by hand rather than through pyBIG so the tests exercise the index
    against the real on-disk layout without depending on the writer.
    """
    names = list(entries)

    header_size = 4 + 4 + 8
    index_size = sum(8 + len(name) + 1 for name in names)
    first_entry = 20
    for name in names:
        first_entry += len(name) + 1 + 8

    positions = {}
    offset = first_entry
    for name in names:
        positions[name] = offset
        offset += len(entries[name])

    with open(path, 'wb') as file:
        file.write(b'BIG4')
        file.write(struct.pack('<I', offset))
        file.write(struct.pack('>II', len(names), index_size))
        for name in names:
            file.write(struct.pack('>II', positions[name], len(entries[name])))
            file.write(name.encode('latin-1') + b'\x00')

        file.write(b'\x00' * (first_entry - file.tell()))
        for name in names:
            file.write(entries[name])

    return path


class CacheTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp(prefix='bfme-cache-')

        self._original_cache_dir = cache.BIG_CACHE_DIR
        cache.BIG_CACHE_DIR = os.path.join(self.directory, 'materialised')
        cache.invalidate_asset_index()

    def tearDown(self):
        cache.BIG_CACHE_DIR = self._original_cache_dir
        cache.invalidate_asset_index()
        shutil.rmtree(self.directory, ignore_errors=True)
        super().tearDown()

    def loose(self, name, content=b'data', subdirectory='loose'):
        path = os.path.join(self.directory, subdirectory, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as file:
            file.write(content)
        return path

    @property
    def loose_dir(self):
        return os.path.join(self.directory, 'loose')

    def archive(self, name, entries):
        return write_big_archive(os.path.join(self.directory, name), entries)


class TestAssetKeys(CacheTestCase):
    def test_asset_key_strips_directory_and_extension(self):
        self.assertEqual('texture', cache.asset_key('art/textures/Texture.DDS'))

    def test_gather_big_filepaths(self):
        self.archive('one.big', {'a.w3d': b'x'})
        self.archive('two.BIG', {'b.w3d': b'x'})
        self.loose('ignored.txt', b'x')

        found = sorted(os.path.basename(p) for p in cache.gather_big_filepaths(self.directory))

        self.assertEqual(['one.big', 'two.BIG'], found)

    def test_gather_big_filepaths_of_missing_directory(self):
        self.assertEqual([], cache.gather_big_filepaths(os.path.join(self.directory, 'nope')))

    def test_path_signature_is_stable_and_ordered(self):
        first = self.loose('a.w3d', b'1234')
        second = self.loose('b.w3d', b'12345678')

        signature = cache.path_signature([second, first])

        self.assertEqual([first, second], [entry[0] for entry in signature])
        self.assertEqual(signature, cache.path_signature([first, second]))

    def test_path_signature_skips_missing_files(self):
        self.assertEqual((), cache.path_signature([os.path.join(self.directory, 'gone.big')]))


class TestAssetIndex(CacheTestCase):
    def test_loose_files_are_referenced_where_they_are(self):
        path = self.loose('texture.dds')

        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertEqual([cache.REF_FILE, path], index['texture'])

    def test_indexing_loose_files_copies_nothing(self):
        self.loose('texture.dds')

        cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))

    def test_archive_entries_are_referenced_by_byte_range(self):
        archive = self.archive('assets.big', {'art/w3d/model.w3d': b'MODELDATA'})

        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        kind, path, entry, position, size = index['model']
        self.assertEqual(cache.REF_BIG, kind)
        self.assertEqual(archive, path)
        self.assertEqual('art/w3d/model.w3d', entry)
        self.assertEqual(len(b'MODELDATA'), size)
        self.assertGreater(position, 0)

    def test_indexing_an_archive_extracts_nothing(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})

        cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))

    def test_unwanted_extensions_are_skipped(self):
        archive = self.archive('assets.big', {'model.w3d': b'x', 'script.lua': b'x'})

        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual(['model'], list(index))

    def test_first_archive_wins_a_shared_name(self):
        first = self.archive('first.big', {'model.w3d': b'FIRST'})
        second = self.archive('second.big', {'model.w3d': b'SECOND'})

        index = cache.build_asset_index([first, second], [], cache.CACHE_EXTENSIONS)

        self.assertEqual(first, index['model'][1])

    def test_loose_files_override_archives(self):
        archive = self.archive('assets.big', {'model.w3d': b'FROM ARCHIVE'})
        path = self.loose('model.w3d', b'FROM DISK')

        index = cache.build_asset_index([archive], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertEqual([cache.REF_FILE, path], index['model'])

    def test_index_is_reused_until_the_inputs_change(self):
        self.loose('texture.dds')

        first = cache.asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertIs(first, cache.asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS))

    def test_index_is_rebuilt_when_forced(self):
        self.loose('texture.dds')
        first = cache.asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        second = cache.asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS, force_refresh=True)

        self.assertIsNot(first, second)
        self.assertEqual(first, second)

    def test_index_is_rebuilt_when_an_archive_changes(self):
        archive = self.archive('assets.big', {'a.w3d': b'x'})
        cache.asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.archive('assets.big', {'a.w3d': b'x', 'b.w3d': b'y'})
        index = cache.asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual(['a', 'b'], sorted(index))

    def test_cached_asset_index_does_not_build_one(self):
        self.loose('texture.dds')

        self.assertEqual({}, cache.cached_asset_index())


class TestReadingAssets(CacheTestCase):
    def test_read_a_loose_asset(self):
        self.loose('texture.dds', b'PAYLOAD')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertEqual(b'PAYLOAD', cache.read_asset(index['texture']))

    def test_read_an_archive_asset(self):
        archive = self.archive('assets.big', {'a.w3d': b'FIRST', 'b.w3d': b'SECOND ENTRY'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual(b'FIRST', cache.read_asset(index['a']))
        self.assertEqual(b'SECOND ENTRY', cache.read_asset(index['b']))

    def test_read_an_archive_asset_does_not_bleed_into_the_next_entry(self):
        archive = self.archive('assets.big', {'a.w3d': b'AAAA', 'b.w3d': b'BBBB'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual(b'AAAA', cache.read_asset(index['a']))

    def test_asset_contains_finds_a_match_in_an_archive_entry(self):
        archive = self.archive('assets.big', {'a.w3d': b'head SKELETON tail'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertTrue(cache.asset_contains(index['a'], b'SKELETON'))

    def test_asset_contains_reports_a_miss(self):
        archive = self.archive('assets.big', {'a.w3d': b'nothing here'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertFalse(cache.asset_contains(index['a'], b'SKELETON'))

    def test_asset_contains_finds_a_match_across_a_chunk_boundary(self):
        needle = b'SKELETON_NAME'
        archive = self.archive('assets.big', {'a.w3d': b'a' * 9 + needle + b'b' * 10})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertTrue(cache.asset_contains(index['a'], needle, chunk_size=10))

    def test_asset_contains_of_a_loose_file(self):
        self.loose('a.w3d', b'head SKELETON tail')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertTrue(cache.asset_contains(index['a'], b'SKELETON'))

    def test_searching_an_archive_materialises_nothing(self):
        archive = self.archive('assets.big', {'a.w3d': b'head SKELETON tail'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        cache.asset_contains(index['a'], b'SKELETON')

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))


class TestResolving(CacheTestCase):
    def test_a_loose_asset_resolves_to_its_own_path(self):
        path = self.loose('texture.dds')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        self.assertEqual(path, cache.resolve(index['texture']))

    def test_resolving_a_loose_asset_copies_nothing(self):
        self.loose('texture.dds')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        cache.resolve(index['texture'])

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))

    def test_a_missing_loose_asset_resolves_to_nothing(self):
        path = self.loose('texture.dds')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)
        os.remove(path)

        self.assertIsNone(cache.resolve(index['texture']))

    def test_an_archive_asset_is_materialised_on_demand(self):
        archive = self.archive('assets.big', {'art/model.w3d': b'MODELDATA'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        path = cache.resolve(index['model'])

        self.assertEqual(os.path.join(cache.BIG_CACHE_DIR, 'model.w3d'), path)
        with open(path, 'rb') as file:
            self.assertEqual(b'MODELDATA', file.read())

    def test_only_the_resolved_asset_is_materialised(self):
        archive = self.archive('assets.big', {'a.w3d': b'A', 'b.w3d': b'B', 'c.w3d': b'C'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        cache.resolve(index['b'])

        self.assertEqual(['b.w3d'], sorted(os.listdir(cache.BIG_CACHE_DIR)))

    def test_resolving_twice_reuses_the_materialised_file(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        path = cache.resolve(index['model'])
        marker = os.path.getmtime(path)

        self.assertEqual(path, cache.resolve(index['model']))
        self.assertEqual(marker, os.path.getmtime(path))

    def test_a_truncated_materialised_file_is_rewritten(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)
        path = cache.resolve(index['model'])

        with open(path, 'wb') as file:
            file.write(b'CUT')

        self.assertEqual(path, cache.resolve(index['model']))
        with open(path, 'rb') as file:
            self.assertEqual(b'MODELDATA', file.read())

    def test_a_materialised_file_of_the_right_size_is_taken_at_face_value(self):
        """Reuse is decided on size alone. Hashing every materialised file would
        undo the point of not copying in the first place, and the cache directory
        is ours, so same-size tampering is out of scope.
        """
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)
        path = cache.resolve(index['model'])

        with open(path, 'wb') as file:
            file.write(b'TRUNCATED')  # same length as MODELDATA

        cache.resolve(index['model'])

        with open(path, 'rb') as file:
            self.assertEqual(b'TRUNCATED', file.read())

    def test_resolve_of_nothing(self):
        self.assertIsNone(cache.resolve(None))

    def test_resolve_key(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertIsNotNone(cache.resolve_key(index, 'model'))
        self.assertIsNone(cache.resolve_key(index, 'missing'))


class TestMaintenance(CacheTestCase):
    def test_clear_removes_materialised_files_and_the_index(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})
        index = cache.asset_index([archive], [], cache.CACHE_EXTENSIONS)
        cache.resolve(index['model'])

        cache.clear()

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))
        self.assertEqual({}, cache.cached_asset_index())

    def test_clear_leaves_the_source_archive_alone(self):
        archive = self.archive('assets.big', {'model.w3d': b'MODELDATA'})

        cache.clear()

        self.assertTrue(os.path.exists(archive))

    def test_cache_stats(self):
        archive = self.archive('assets.big', {'a.w3d': b'A', 'b.w3d': b'B'})
        index = cache.asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual((2, 0), cache.cache_stats())

        cache.resolve(index['a'])

        self.assertEqual((2, 1), cache.cache_stats())
