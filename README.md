# Blender KN5 Exporter

[![CI](https://github.com/moppius/blender-assetto-corsa-tools/actions/workflows/ci.yaml/badge.svg)](https://github.com/moppius/blender-assetto-corsa-tools/actions/workflows/ci.yaml)

## Features

* File format version 5
* Blender mesh objects as kn5 geometry
* Blender image textures as kn5 textures
* Set material and object settings with JSON
* Texture mapping with UV maps or flat mapping
* Multiple materials per object


## Current Bugs & Limitations

* No support for skinned meshes (needed for animations)
* No support for AI
* Only geometry of mesh objects will be exported
* Only textures of type "Image" supported


## Requirements
This addon is made for the latest Blender version (currently 3.0.0), others may work but are not supported.


## Install

1. Download the _assetto_corsa_tools.zip_ from the [latest Release](https://github.com/moppius/blender-assetto-corsa-tools/releases/latest).
2. Start Blender
3. Go to _Edit -> Preferences -> Addons_
4. Click "Install..." in the top right and browse to the downloaded zip file
5. Enable the **"Assetto Corsa (.kn5)"** addon


## Usage

1. Set up a track scene with geometry and helpers
2. Go to _File -> Export -> Assetto Corsa (.kn5)_
3. Select target folder to save the track. Make sure that a valid _settings.json_ file exists


## Notes

This repository was initially created from the Blender 2.76 addon distributed as [_kn5exporter.zip_ on Thomas Hagnhofer's website](https://site.hagn.io/assettocorsa/blender-kn5-exporter).

Please visit that site for a downloadable example track, and more information on the original implementation.
