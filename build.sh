#!/bin/bash

# This file can be used to build the addon zip file without using blender 4.2.0

name=SKkeeper
version=v1.8.1
folder=./SKkeeper

mkdir "$folder"
cp __init__.py "$folder"
zip -r "${name}_${version}.zip" "$folder"
rm -r "$folder"
