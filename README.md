# Blender KN5 Exporter


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

1. Download kn5exporter.zip
2. Start Blender
3. File -> User Preferences -> Addons
4. Click "Install from File..."  and select the downloaded zip file
5. Enable addon "Assetto Corsa (.kn5)"


## Usage

1. File -> Export -> Assetto Corsa (.kn5)
2. Select target folder to save the track. Make sure that a valid settings.json file exists.
3. Copy the created file to the target track folder in your Assetto Corsa install folder.


## Notes

This repository was initially created from the Blender 2.76 addon distributed as [_kn5exporter.zip_ on Thomas Hagnhofer's website](https://site.hagn.io/assettocorsa/blender-kn5-exporter).

Please visit that site for a downloadable example track, and more information on the original implementation.
