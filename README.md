![OpenSAGE](/art/opensage-logo.png)
============================================================

[![Build Status](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/actions/workflows/ci.yml)
[![Discord Chat](https://img.shields.io/discord/398393968234332161.svg?logo=discord)](https://discord.gg/G2FhZUT)
[![codecov](https://codecov.io/gh/OpenSAGE/OpenSAGE.BlenderPlugin/branch/master/graph/badge.svg)](https://codecov.io/gh/OpenSAGE/OpenSAGE.BlenderPlugin)

![Sample](/art/AotR_Umbar_Buildings.jpg)

**OpenSAGE.BlenderPlugin**: a free, open source blender plugin for the [Westwood](https://de.wikipedia.org/wiki/Westwood_Studios) 3D
format used in Command & Conquer™: Generals and other RTS titles from Westwood Studios and EA Pacific.

## Installing and activating

Please see [Installing the plugin](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Installing-the-Plugin)

Supported Blender versions are 2.93 up to 5.2. On Blender 4.2 and newer the released `io_mesh_w3d.zip`
can be dropped into Blender to install it as an extension, older versions install it as a legacy add-on
via *Edit > Preferences > Add-ons > Install*.

## BfMe Tools

The add-on also ships the BfMe modding tools (originally a separate add-on by Brechstange), found in the
3D viewport sidebar (press *N*) under the *BfMe* tab. They cover asset search paths and `.big` extraction,
a `.w3d` model browser with previews, finding animations that fit a skeleton, build-up and destroy
animation generators, UV/structure/collision-geometry/bone helpers and a simplified export panel.

## Setting up for development

Please see [Setting up for development](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Development-Setup)

## Note

The plugin is still in beta and the behaviour may change between releases. Also bugs might still occur, which we'll try to fix as soon as possible. So feel free to report bugs and issues in the #w3d-blender-plugin channel on [OpenSAGE Discord](https://discord.gg/G2FhZUT). Also see [Troubleshoting](https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Troubleshooting) for more information.

## Legal disclaimers

* This project is not affiliated with or endorsed by EA in any way. Command & Conquer is a trademark of Electronic Arts.
* This project is non-commercial. The source code is available for free and always will be.
* If you want to contribute to this repository, your contribution must be either your own original code, or open source code with a
  clear acknowledgement of its origin. No code that was acquired through reverse engineering executable binaries will be accepted.
* No assets from the original games are included in this repo.

## Community

We have a growing [OpenSAGE Discord](https://discord.gg/G2FhZUT) community. If you have questions about the project or can't get it working,
there's usually someone there who can help out.
