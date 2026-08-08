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

from io_mesh_w3d.bfme import cache, dependencies
from tests.utils import TestCase


def write_big_archive(path, entries):
    """Write a minimal BIG4 archive containing the given {name: bytes}.

    Built by hand rather than through pyBIG so the tests exercise the index
    against the real on-disk layout without depending on the writer.
    """
    names = list(entries)

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


def w3d_chunk(chunk_type, payload, has_sub_chunks=False):
    size = len(payload) | (0x80000000 if has_sub_chunks else 0)
    return struct.pack('<II', chunk_type, size) + payload


def w3d_texture(name):
    """A texture chunk wrapping a texture name chunk, as a real .w3d nests them."""
    return w3d_chunk(0x00000031, w3d_chunk(0x00000032, name.encode() + b'\x00'), has_sub_chunks=True)


def w3d_hlod_header(hierarchy_name, model_name='model'):
    payload = (struct.pack('<II', 0x00040001, 1)
               + model_name.encode().ljust(16, b'\x00')
               + hierarchy_name.encode().ljust(16, b'\x00'))
    return w3d_chunk(0x00000701, payload)


def w3d_shader_property(name, value, prop_type=1):
    """A shader material property chunk: type, name length, name, value length, value."""
    payload = struct.pack('<ii', prop_type, len(name) + 1) + name.encode() + b'\x00'
    if prop_type == 1:
        payload += struct.pack('<i', len(value) + 1) + value.encode() + b'\x00'
    else:
        payload += struct.pack('<f', value)
    return w3d_chunk(0x00000053, payload)


def w3d_shader_material(properties):
    """The nesting a real shader material model uses: 0x50 > 0x51 > 0x53."""
    material = b''.join(w3d_shader_property(name, value) for name, value in properties)
    inner = w3d_chunk(0x00000051, material, has_sub_chunks=True)
    return w3d_chunk(0x00000050, inner, has_sub_chunks=True)


def w3d_model(hierarchy_name=None, textures=(), shader_textures=()):
    data = b''
    if hierarchy_name is not None:
        data += w3d_chunk(0x00000700, w3d_hlod_header(hierarchy_name), has_sub_chunks=True)
    for texture in textures:
        data += w3d_texture(texture)
    if shader_textures:
        data += w3d_shader_material(shader_textures)
    return data


class TestDependencyScanning(CacheTestCase):
    def test_texture_names_are_found(self):
        names = dependencies.referenced_names(w3d_model(textures=['Skin.dds', 'Cloth.tga']))

        self.assertEqual({'skin', 'cloth'}, names)

    def test_the_hierarchy_name_is_found(self):
        names = dependencies.referenced_names(w3d_model(hierarchy_name='HERO_SKL'))

        self.assertEqual({'hero_skl'}, names)

    def test_shader_material_textures_are_found(self):
        """Most BfMe II era models are shader material models, which name their
        textures in a string property rather than in a texture chunk.
        """
        data = w3d_model(shader_textures=[
            ('DiffuseTexture', 'ARiceclifftall.tga'),
            ('NormalMap', 'ARiceclifftall_NM.tga')])

        names = dependencies.referenced_names(data)

        self.assertEqual({'ariceclifftall', 'ariceclifftall_nm'}, names)

    def test_non_string_shader_properties_are_ignored(self):
        material = (w3d_shader_property('DiffuseTexture', 'skin.tga')
                    + w3d_shader_property('BumpScale', 1.5, prop_type=2))
        data = w3d_chunk(0x00000050, w3d_chunk(0x00000051, material, has_sub_chunks=True),
                         has_sub_chunks=True)

        self.assertEqual({'skin'}, dependencies.referenced_names(data))

    def test_a_model_with_no_references(self):
        self.assertEqual(set(), dependencies.referenced_names(w3d_model()))

    def test_garbage_is_not_mistaken_for_references(self):
        self.assertEqual(set(), dependencies.referenced_names(b'not a w3d file at all'))

    def test_a_truncated_model_does_not_raise(self):
        data = w3d_model(hierarchy_name='HERO_SKL', textures=['Skin.dds'])

        self.assertEqual(set(), dependencies.referenced_names(data[:6]))
        dependencies.referenced_names(data[:len(data) // 2])

    def test_dependency_keys_follows_a_skeleton(self):
        archive = self.archive('assets.big', {
            'model.w3d': w3d_model(hierarchy_name='hero_skl', textures=['skin.dds']),
            'hero_skl.w3d': w3d_model(textures=['bones.dds']),
            'skin.dds': b'SKIN',
            'bones.dds': b'BONES'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual({'hero_skl', 'skin', 'bones'}, cache.dependency_keys(index, 'model'))

    def test_dependency_keys_ignores_names_that_are_not_indexed(self):
        archive = self.archive('assets.big', {
            'model.w3d': w3d_model(textures=['present.dds', 'absent.dds']),
            'present.dds': b'X'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual({'present'}, cache.dependency_keys(index, 'model'))

    def test_dependency_keys_survives_a_reference_cycle(self):
        archive = self.archive('assets.big', {
            'a.w3d': w3d_model(hierarchy_name='b'),
            'b.w3d': w3d_model(hierarchy_name='a')})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        self.assertEqual({'b'}, cache.dependency_keys(index, 'a'))


class TestStagingForImport(CacheTestCase):
    def test_an_archived_model_brings_its_skeleton_and_textures_along(self):
        archive = self.archive('assets.big', {
            'art/model.w3d': w3d_model(hierarchy_name='hero_skl', textures=['skin.dds']),
            'art/hero_skl.w3d': w3d_model(),
            'art/skin.dds': b'SKIN'})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        path = cache.stage_for_import(index, 'model')

        # the importer looks these up by name next to the file it is given
        self.assertEqual(cache.BIG_CACHE_DIR, os.path.dirname(path))
        self.assertEqual(['hero_skl.w3d', 'model.w3d', 'skin.dds'],
                         sorted(os.listdir(cache.BIG_CACHE_DIR)))

    def test_unrelated_archive_entries_are_left_alone(self):
        archive = self.archive('assets.big', {
            'model.w3d': w3d_model(textures=['skin.dds']),
            'skin.dds': b'SKIN',
            'unrelated.dds': b'NOPE',
            'other.w3d': w3d_model()})
        index = cache.build_asset_index([archive], [], cache.CACHE_EXTENSIONS)

        cache.stage_for_import(index, 'model')

        self.assertEqual(['model.w3d', 'skin.dds'], sorted(os.listdir(cache.BIG_CACHE_DIR)))

    def test_a_loose_model_whose_dependencies_sit_beside_it_is_not_copied(self):
        self.loose('model.w3d', w3d_model(hierarchy_name='hero_skl', textures=['skin.dds']))
        self.loose('hero_skl.w3d', w3d_model())
        self.loose('skin.dds', b'SKIN')
        index = cache.build_asset_index([], [self.loose_dir], cache.CACHE_EXTENSIONS)

        path = cache.stage_for_import(index, 'model')

        self.assertEqual(self.loose_dir, os.path.dirname(path))
        self.assertFalse(os.path.isdir(cache.BIG_CACHE_DIR))

    def test_a_loose_model_is_staged_when_a_dependency_is_in_an_archive(self):
        archive = self.archive('assets.big', {'skin.dds': b'SKIN'})
        self.loose('model.w3d', w3d_model(textures=['skin.dds']))
        index = cache.build_asset_index([archive], [self.loose_dir], cache.CACHE_EXTENSIONS)

        path = cache.stage_for_import(index, 'model')

        self.assertEqual(cache.BIG_CACHE_DIR, os.path.dirname(path))
        self.assertEqual(['model.w3d', 'skin.dds'], sorted(os.listdir(cache.BIG_CACHE_DIR)))

    def test_a_loose_model_is_staged_when_a_dependency_is_in_another_folder(self):
        self.loose('model.w3d', w3d_model(textures=['skin.dds']))
        self.loose('skin.dds', b'SKIN', subdirectory='elsewhere')
        index = cache.build_asset_index(
            [], [self.loose_dir, os.path.join(self.directory, 'elsewhere')], cache.CACHE_EXTENSIONS)

        path = cache.stage_for_import(index, 'model')

        self.assertEqual(cache.BIG_CACHE_DIR, os.path.dirname(path))

    def test_a_texture_is_found_under_a_different_extension(self):
        """Models routinely ask for a .tga that ships as a .dds; the index is keyed
        by name without extension, and the importer tries every extension it knows.
        """
        self.loose('model.w3d', w3d_model(shader_textures=[('DiffuseTexture', 'skin.tga')]))
        self.loose('skin.dds', b'SKIN', subdirectory='textures')
        index = cache.build_asset_index(
            [], [self.loose_dir, os.path.join(self.directory, 'textures')], cache.CACHE_EXTENSIONS)

        cache.stage_for_import(index, 'model')

        self.assertEqual(['model.w3d', 'skin.dds'], sorted(os.listdir(cache.BIG_CACHE_DIR)))

    def test_staging_an_unknown_key(self):
        self.assertIsNone(cache.stage_for_import({}, 'missing'))


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
