# <pep8 compliant>
# Tests for the BfMe asset cache.
#
# These run against the real bpy inside Blender like the rest of the suite. The
# original bfme tests installed a MagicMock as sys.modules['bpy'], which would have
# replaced bpy for every other test sharing this process.

import os
import shutil
import tempfile

from io_mesh_w3d.bfme import cache
from tests.utils import TestCase


class TestCacheHelpers(TestCase):
    def setUp(self):
        super().setUp()
        self.cache_dir = tempfile.mkdtemp(prefix='bfme-cache-')
        self.index_file = os.path.join(self.cache_dir, 'index.json')

        self._original_dir = cache.BIG_CACHE_DIR
        self._original_index = cache.CACHE_INDEX_FILE
        cache.BIG_CACHE_DIR = os.path.join(self.cache_dir, 'files')
        cache.CACHE_INDEX_FILE = self.index_file
        os.makedirs(cache.BIG_CACHE_DIR, exist_ok=True)

        cache.invalidate_cache_index()
        cache.invalidate_cached_file_sizes()

    def tearDown(self):
        cache.BIG_CACHE_DIR = self._original_dir
        cache.CACHE_INDEX_FILE = self._original_index
        cache.invalidate_cache_index()
        cache.invalidate_cached_file_sizes()
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        super().tearDown()

    def write(self, name, content, directory=None):
        path = os.path.join(directory or cache.BIG_CACHE_DIR, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as file:
            file.write(content)
        return path

    def test_cached_file_sizes_of_empty_directory(self):
        self.assertEqual({}, cache.get_cached_file_sizes())

    def test_cached_file_sizes_reports_actual_sizes(self):
        self.write('a.dds', b'1234')
        self.write('b.tga', b'123456789')
        cache.invalidate_cached_file_sizes()

        sizes = cache.get_cached_file_sizes()

        self.assertEqual(4, sizes['a.dds'])
        self.assertEqual(9, sizes['b.tga'])

    def test_cached_file_sizes_has_no_bookkeeping_entries(self):
        self.write('a.dds', b'1234')
        cache.invalidate_cached_file_sizes()

        # the modification time is tracked next to the data, never inside it
        self.assertEqual(['a.dds'], list(cache.get_cached_file_sizes().keys()))

    def test_cached_file_sizes_are_reused(self):
        self.write('a.dds', b'1234')
        cache.invalidate_cached_file_sizes()
        first = cache.get_cached_file_sizes()

        self.assertIs(first, cache.get_cached_file_sizes())

    def test_invalidate_cached_file_sizes(self):
        self.write('a.dds', b'1234')
        cache.invalidate_cached_file_sizes()
        first = cache.get_cached_file_sizes()

        cache.invalidate_cached_file_sizes()

        self.assertIsNot(first, cache.get_cached_file_sizes())

    def test_missing_cache_directory_yields_no_sizes(self):
        shutil.rmtree(cache.BIG_CACHE_DIR)
        cache.invalidate_cached_file_sizes()

        self.assertEqual({}, cache.get_cached_file_sizes())

    def test_cache_index_roundtrip(self):
        cache.save_cache_index({'files': {'a': 'b'}, 'big_signature': []})
        cache.invalidate_cache_index()

        self.assertEqual({'a': 'b'}, cache.load_cache_index()['files'])

    def test_missing_cache_index_is_empty(self):
        self.assertEqual({}, cache.load_cache_index())

    def test_corrupted_cache_index_is_empty(self):
        with open(cache.CACHE_INDEX_FILE, 'w') as file:
            file.write('{ not json')
        cache.invalidate_cache_index()

        self.assertEqual({}, cache.load_cache_index())

    def test_hash_file(self):
        path = self.write('a.dds', b'hello world')

        self.assertEqual(cache.hash_file(path), cache.hash_file(path))
        self.assertNotEqual(cache.hash_file(path), cache.hash_file(self.write('b.dds', b'other')))

    def test_copy_file_with_hash(self):
        source = self.write('source.dds', b'payload', directory=self.cache_dir)
        destination = os.path.join(cache.BIG_CACHE_DIR, 'copied.dds')

        digest = cache.copy_file_with_hash(source, destination)

        self.assertTrue(os.path.exists(destination))
        self.assertEqual(cache.hash_file(source), digest)
        with open(destination, 'rb') as file:
            self.assertEqual(b'payload', file.read())

    def test_copy_file_with_hash_leaves_no_temp_file_on_failure(self):
        missing = os.path.join(self.cache_dir, 'does-not-exist.dds')
        destination = os.path.join(cache.BIG_CACHE_DIR, 'copied.dds')

        with self.assertRaises(OSError):
            cache.copy_file_with_hash(missing, destination)

        self.assertFalse(os.path.exists(destination + '.tmp'))

    def test_path_signature_is_stable_and_ordered(self):
        first = self.write('a.big', b'1234', directory=self.cache_dir)
        second = self.write('b.big', b'12345678', directory=self.cache_dir)

        signature = cache.path_signature([second, first])

        self.assertEqual([first, second], [entry[0] for entry in signature])
        self.assertEqual([4, 8], [entry[2] for entry in signature])
        self.assertEqual(signature, cache.path_signature([first, second]))

    def test_path_signature_skips_missing_files(self):
        self.assertEqual([], cache.path_signature([os.path.join(self.cache_dir, 'gone.big')]))

    def test_gather_big_filepaths(self):
        self.write('nested/deep/one.big', b'x', directory=self.cache_dir)
        self.write('two.BIG', b'x', directory=self.cache_dir)
        self.write('ignored.txt', b'x', directory=self.cache_dir)

        found = sorted(os.path.basename(path) for path in cache.gather_big_filepaths(self.cache_dir))

        self.assertEqual(['one.big', 'two.BIG'], found)

    def test_gather_big_filepaths_of_missing_directory(self):
        self.assertEqual([], cache.gather_big_filepaths(os.path.join(self.cache_dir, 'nope')))


class TestSearchPathCaching(TestCacheHelpers):
    def setUp(self):
        super().setUp()
        self.source_dir = os.path.join(self.cache_dir, 'source')
        os.makedirs(self.source_dir, exist_ok=True)

    def source(self, name, content):
        return self.write(name, content, directory=self.source_dir)

    def test_copies_new_files_into_the_cache(self):
        self.source('texture.dds', b'texture data')

        index = cache.cache_search_path_files([self.source_dir])

        self.assertIn('texture', index)
        self.assertTrue(os.path.exists(index['texture']))

    def test_only_cacheable_extensions_are_copied(self):
        self.source('model.w3d', b'model')
        self.source('notes.txt', b'notes')

        index = cache.cache_search_path_files([self.source_dir])

        self.assertEqual(['model'], list(index))

    def test_unchanged_file_is_not_copied_again(self):
        self.source('texture.dds', b'texture data')
        cache.cache_search_path_files([self.source_dir])

        destination = os.path.join(cache.BIG_CACHE_DIR, 'texture.dds')
        marker = os.path.getmtime(destination)

        cache.invalidate_cached_file_sizes()
        cache.cache_search_path_files([self.source_dir], force_refresh=True)

        self.assertEqual(marker, os.path.getmtime(destination))

    def test_changed_content_of_equal_size_is_copied_again(self):
        self.source('texture.dds', b'aaaa')
        cache.cache_search_path_files([self.source_dir])

        # same size, so only the content hash can tell these apart
        self.source('texture.dds', b'bbbb')
        cache.invalidate_cached_file_sizes()
        cache.cache_search_path_files([self.source_dir], force_refresh=True)

        with open(os.path.join(cache.BIG_CACHE_DIR, 'texture.dds'), 'rb') as file:
            self.assertEqual(b'bbbb', file.read())

    def test_changed_size_is_copied_again(self):
        self.source('texture.dds', b'aaaa')
        cache.cache_search_path_files([self.source_dir])

        self.source('texture.dds', b'much longer content')
        cache.invalidate_cached_file_sizes()
        cache.cache_search_path_files([self.source_dir], force_refresh=True)

        with open(os.path.join(cache.BIG_CACHE_DIR, 'texture.dds'), 'rb') as file:
            self.assertEqual(b'much longer content', file.read())

    def test_second_run_is_served_from_the_index(self):
        self.source('texture.dds', b'texture data')
        first = cache.cache_search_path_files([self.source_dir])

        self.assertEqual(first, cache.cache_search_path_files([self.source_dir]))

    def test_no_search_paths(self):
        self.assertEqual({}, cache.cache_search_path_files([]))

    def test_progress_is_reported(self):
        for index in range(250):
            self.source(f'texture_{index}.dds', b'x' * index)

        seen = []
        cache.cache_search_path_files([self.source_dir], progress=lambda done, total: seen.append((done, total)))

        self.assertTrue(seen)
        self.assertEqual([250] * len(seen), [total for _, total in seen])

    def test_clear_removes_directory_and_index(self):
        self.source('texture.dds', b'texture data')
        cache.cache_search_path_files([self.source_dir])

        cache.clear()

        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))
        self.assertFalse(os.path.exists(cache.CACHE_INDEX_FILE))
        self.assertEqual({}, cache.load_cache_index())

    def test_cache_stats(self):
        self.source('texture.dds', b'texture data')
        cache.cache_search_path_files([self.source_dir])

        big_files, search_files = cache.cache_stats()

        self.assertEqual(0, big_files)
        self.assertEqual(1, search_files)
