# Version History

## v0.7.2 (28.09.24)

* adapt to API changes in Blender 4.2+

## v0.7.1 (29.01.24)

* adapt to API changes in Blender 4.0+

## v0.7.0 (09.09.23)

* delete base sphere object and mesh after hierarchy import
* fix face distance calculation to match 3DS max exporter
* multi-texture / multi-material support by @nkx111 thx!

## v0.6.9 (06.04.23)

* fixed export of materials with normal maps

## v0.6.8 (29.12.21)

* fixed issues with api changes in blender 3.0
* export texture names always with '.tga' extension

## v0.6.7 (22.10.21)

* added auto updater
* adaptions for python 3.9 used in blender 2.93 and later
* Bugfix: pivot and vertex groups are compared all lowercase

## v0.6.6 (24.7.21)

* display valid vertex color layer names if layer name is invalid
* display actual bone weights if they do not add up to 100%
* inform user on animation import that armature might have been hidden due to visibility channels
* do not crash on animation import if channels reference non existing bones but inform user instead
* inform user on export if a mesh has no vertices and skip it
* Bugfix: read scale as float instead of short in 'AdaptiveDeltaAnimationChannel'
* Bugfix: do not crash if mesh has more shader structs than vertex materials

## v0.6.5 (26.3.21)

* cancel export if a mesh and a bone share the same name and mesh is not configured properly
* inform user if both vertex bone weights do not add up to 100%
* Bugfix: handling of specular and emission color
* Bugfix: use proper file extension for loaded textures
* Bugfix: split vertices with n uv-coords into n vertices

## v0.6.4 (23.2.21)

* support mesh property 'two sided'
* cancel export if vertices are not rigged to any bone
* cancel export if vertices are rigged to more than 2 bones
* added vertex material info mapping attributes
* Bugfix: uv corrdinates are correct for meshes where invalid triangles are removed on import
* Bugfix: no negative values for bounding box extend
* Bugfix: proper vertex material args handling
* Bugfix: normalize quaternions on animation export

## v0.6.3 (17.1.20)

* geometry data can now be exported to xml and ini

## v0.6.2 (01.12.20)

* support for floats in xml files with ',' and '.'
* support more collision box properties (type, collision_type)

## v0.6.0 (28.7.20)

* export dummy shade indices (they are needed for the mod SDK (at least for W3X))
* support for mesh sorting levels
* only display appropriate custom object properties
* support mesh flags 'cast_shadow', 'camera oriented' and 'camera aligned'
* import prelit vertex material as basic vertex material for now
* support for per face surface types via face maps
* added support for vertex colors
* Bugfix: fix import of visibility channels of armature
* Bugfix: handle multiple hlod, hierarchy and animation chunks
* Bugfix: fix export when bones are not in tree order
* Bugfix: fix export of time coded animations
* Bugfix: set hierarchy name always uppercase

## v0.5.0 (10.06.20)

* use proper enums for vertex material shader properties
* create pivots for meshes on export if they have no parent bone
* create a bone for each hierarchy pivot on import (otherwise pivot order can not be maintained on roundtrip)
* reduced export time for meshes (O(n*n) -> O(n))
* handle empty/invalid/default materials correctly on export
* Bugfix: texture name got falsely '.dds' appended on export
* Bugfix: export proper opacity value of material (fixes invisible objects in W3DViewer)
* Bugfix: do not export uv coordinates if no texutre is used by the material
* Bugfix: fixed mesh triangulation on export
* Bugfix: use proper hierarchy name for animation and hlod on export

## v0.4.7 (26.04.20)

* Bugfix: fixed installation issue

## v0.4.6 (24.04.20)

* apply modifiers to meshes on export
* handle export of 'multi-user' meshes
* default material type is now 'VERTEX_MATERIAL'
* Bugfix: handle free vertices correctly
* Bugfix: handle already applied file extensions by user
* Bugfix: check for referenced armature case insensitive

## v0.4.5 (11.03.20)

* split vertices with multiple uv coordinates on export
* use actual mesh normals on import
* export tangents and bitangents
* custom floating point visibility property for bones
* create armature for roottransform pivot
* Bugfix: parenting issue
* Bugfix: triangle distances
* Bugfix: proper bool string export

## v0.4.4 (19.02.20)

* limit decimal digits in w3x files to 6
* Bugfix: use armature name as hierarchy ID
* Bugfix: create includes on export

## v0.4.3 (13.02.20)

* create only required keyframes on animation import
* support more texture file formats
* Bugfix: bone visibility channels
* Bugfix: do not crash on missing float vector entries

## v0.4.2 (04.02.20)

* switched to ElementTree for xml stuff
* Bugfix: write boolean values as lower in w3x
* Bugfix: loading of animations without include for corresponding hierarchy

## v0.4.1 (01.02.20)

* support splitted w3x files
* support w3x single mesh imports
* Bugfix: do not crash on missing attributes

## v0.4.0 (31.01.20)

* support for w3x files

## v0.3.0 (05.01.20)

* support multiple levels of detail in HLod chunks
* Bugfix: fix rigging issues with C&C Generals and C&C Renegade models

## v0.2.1 (13.11.19)

* support for basic uncompressd and timecoded animation export
* added multiple custom properties in order to reduce data loss on roundtrips
* Bugfix: exported files now work in W3DViewer 6.0 and the recent revora version
* Bugfix: hierarchy pivots are now in correct order on exported
