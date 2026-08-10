# Version History

## v0.8.0

* Bugfix: exporting a mesh with vertices bound to two bones could leave the two weights not
  summing to 100%, or occasionally drop a small (e.g. 1%) secondary weight entirely, turning a
  two-bone vertex into a rigidly single-bone one. Blender stores vertex group weights as
  float32, so an intended weight like 42% is actually stored as 0.41999998; writing that out
  by truncating (`int(weight * 100)`) rounded it down to 41, silently losing up to a whole
  percentage point on each side independently. The game blends a multi-bone vertex as
  `weight0 * position0 + weight1 * position1`, with each position stored in its own bone's
  local space, so a missing percentage point under-scaled the result - harmless at bind pose,
  but once the affected bone rotated away from it during animation this became a visibly large
  offset, while single-bone vertices (100%/0%, no rounding boundary to lose) were unaffected.
  The second weight is now written as the exact complement of the first, which always sums to
  100% by construction
* the 'Existing Animations' tab is now 'Bindings and Animation', with two sub-tabs:
  * 'Existing Animations' is the previous animation search, its results list can now be
    collapsed
  * 'Bindings' adds an 'Auto-Bind' button: pick an armature, and every mesh in the scene
    that has no Armature modifier yet gets one, with every vertex weighted to its nearest
    deforming bone(s). This was calibrated against several real exported assets (both
    hard-surface armor/weapons and organic creatures/characters): a vertex is bound
    rigidly (100%) to its single nearest bone unless a second one is nearly as close, in
    which case both contribute, favouring whichever is closer rather than an even split.
    No pure distance rule reproduces hand weight-painting exactly - real riggers use body
    topology a geometric measure cannot see - so this favours staying rigid unless a
    vertex is clearly near a joint, since a wrongly blended hard-surface part is more
    visibly wrong than a joint vertex left rigid. A 'Show Weights' toggle bakes the
    result into a vertex color layer, gives each bone a distinct color, a small colored
    marker sphere and a visible name (a W3D hierarchy's pivot bones are usually near
    zero length and otherwise easy to miss entirely), switches every 3D viewport to
    solid shading with vertex colors and the wireframe overlay on, and puts the armature
    into Pose Mode (bone colors only render in Edit/Pose Mode). Any vertex whose weights
    do not sum to ~100%, however many bones they are spread over, is shown in white
    instead of blending in
* Bugfix: a model whose texture happened to share a base name with an unrelated
  .w3d file (e.g. a 'pfence01' texture next to an unrelated 'pfence01.w3d' prop
  model, both real BfMe II assets) could import or preview without that texture.
  The asset index only kept one reference per name, so the model silently shadowed
  the texture depending on which .big got scanned first. Textures and .w3d files
  are now kept in their own lookup so a model's dependencies always resolve to the
  right kind of asset regardless of what else happens to share its name
* the W3D Tools sub-panels (asset search paths, .big extraction, model browser, animation
  finder, build-up/destroy animation, export settings) are now collapsed by default, matching
  the outer 'W3D Tools' panel, instead of all expanding on every install
* the W3D Model Browser scans once per Blender session on its own, so the list is populated
  without pressing 'Scan W3D Models' first. That and the button are the only two things that
  ever scan; there is no periodic rescan competing with the UI. The scan runs in a worker
  thread and its results are inserted in small batches spread over several timer ticks, so a
  full install's worth of models (tens of thousands) never stalls Blender for the single
  frame it would take to insert them at once. Press the button to pick up assets that changed
  on disk since Blender started
* search paths are now indexed in parallel with .big archives instead of after them
  sequentially, using the same thread pool
* the model list no longer does any work per redraw. Blender calls a UIList's filter_items()
  for every redraw, including every frame of a scroll, so with a full install's worth of
  models the list could not be scrolled smoothly: sorting them there cost ~15 ms per redraw,
  more than a 60 fps frame budget on its own, and handing Blender a 21k entry reorder array
  made it redo that mapping every redraw too. Both scan paths now insert the models in sorted
  order, so the list needs no reordering at all, and matching against the filter text is
  cached until the list or the text changes. A redraw went from ~15 ms to ~0.01 ms
* filling the list only redraws the sidebar region it lives in, once, rather than tagging
  every area and forcing a full 3D viewport redraw per batch
* the scan starts a few seconds after Blender rather than immediately, so reading every
  archive header with a cold file cache does not compete with Blender's own startup I/O
* looking up the cached asset index no longer waits on the index lock, so importing or
  previewing a model while a background rescan happens to be running does not stall
* Bugfix: importing through File > Import > Westwood W3D produced shinier looking materials than
  importing the same file through the BfMe model browser. The model browser zeroed out the
  Principled BSDF's specular input after calling the core import operator (W3D materials do not
  carry one; the importer's shininess value does not correspond to it), but the core operator
  itself did not, so the two paths disagreed. The fix now lives in the core import operator, so
  every caller gets it, and the BfMe tools' now-redundant copy of it is gone
* integrated the BfMe Tools (by Brechstange) into the 'W3D Tools' tab in the 3D viewport sidebar
  (N-panel), alongside the existing geometry/bone-volume export panel; they are no longer a
  separate add-on: asset search paths and .big extraction, a .w3d model browser with previews, an
  animation finder, build-up and destroy animation generators, UV/structure/collision-geometry/
  bone helpers and a simplified export panel
* the tools now call the W3D importer and exporter directly instead of searching `bpy.ops` for
  something that looks like a W3D operator
* Bugfix: the tools did not work on Blender 4.2+ at all in several places, `Action.fcurves`,
  `Material.shadow_method` and the EEVEE `use_bloom`/`use_ssr` settings were all removed
* Bugfix: the texture and model scans mutated Blender data from worker threads, which is not
  thread safe, they now only do file system work off the main thread
* Bugfix: preview generation crashed when every imported object was hidden, and could leave the
  window on a scene that was about to be deleted
* Bugfix: an animation search no longer reads whole .w3d files into memory
* several hot paths are now vectorised (collision geometry analysis, bone placement, scene
  height) or use the right data structure (UV island flood fill, per-bone lookups), the model
  list no longer re-copies itself on every UI tick
* W3D/W3X import now merges materials that are identical in every property this add-on writes,
  instead of creating one material per mesh that happens to use it. Meshes are keyed by
  `<mesh name>.<material name>` when they're created, so a kitbashed model built from many
  meshes that share one texture used to end up with one duplicate material per mesh; those are
  now merged into a single material datablock once the whole file is imported
* the asset cache is now an index of *references* instead of a copy of everything. Loose files in
  a search path are used straight from where they are and never copied at all; entries inside a
  .big are referenced by their byte range and only written out when something actually opens them,
  which Blender needs because it cannot read from inside an archive. Measured against a full
  BfMe II + RotWK install (223 archives, 10 GB): indexing all 32808 assets takes 0.4 s and writes
  nothing to disk, where the previous implementation copied 6267 MB into %TEMP% before the model
  list could be shown. The per-search-path 'Load to cache' switch is gone with it, since there is
  no longer anything to opt into. Importing or previewing a model brings its skeleton and its
  textures along, because the W3D importer resolves those by name next to the file it is given;
  this covers both classic texture chunks and the shader material properties most BfMe II era
  models use, and finds a texture even when the model asks for a .tga that ships as a .dds
* Bugfix: importing a second animation onto the same skeleton from 'Existing Animations' mixed
  its keyframes into whatever animation the skeleton already had, instead of replacing it -
  `keyframe_insert()` adds to the currently assigned action rather than starting a fresh one.
  The target's existing action is now detached before importing and only actually removed once
  the import has succeeded, so a failed import doesn't lose the previous animation either

## v0.7.4

* adapt to API changes in Blender 5.2
* the add-on can now be installed as an extension (Blender 4.2+), the release archive works for both
  the extension and the legacy add-on install
* replaced deprecated API usage: `Material.blend_method` -> `Material.surface_render_method`,
  `Material.show_transparent_back` -> `Material.use_transparency_overlap`, `Material.use_nodes`,
  `Mesh.vertex_colors` -> `Mesh.color_attributes` and `MeshUVLoopLayer.data` -> `MeshUVLoopLayer.uv`
* transparency of imported materials is applied again in EEVEE Next (Blender 4.2+)
* Bugfix: import no longer fails on Blender 4.1 (`Mesh.use_auto_smooth` was removed there, not in 4.2)
* Bugfix: do not rely on the deprecated truth value of xml elements when writing w3x files

## v0.7.3

* adapt to API changes in Blender 5.1+

## v0.7.2 (01.05.25)

* adapt to API changes in Blender 4.2+
* adapt to API changes in Blender 4.4+

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
