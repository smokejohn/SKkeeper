#!/bin/bash

name=SKkeeper
version=v1.4
folder=./SKkeeper

mkdir "$folder"
cp __init__.py "$folder"
zip -r "${name}_${version}.zip" "$folder"
rm -r "$folder"
