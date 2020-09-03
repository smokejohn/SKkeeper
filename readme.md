# Blender Addon - Apply modifiers without losing shapekeys
This Addon automates the process of collapsing down modifiers on a mesh with shapekeys while keeping the shapekeys intact.

## How to Install

Download the zipfile from the [Releases page](https://github.com/smokejohn/bl_apply_mods_shapekey/releases) and install via Blenders Addon-Preferences

Edit > Preferences > Add-ons > Install... > Select apply_mods_sk.zip

## How to Use

This Addon adds 3 new operators which can be found in via the Quick Search floater (**Hotkey: F3 or Space**) and typing "Apply" or anything else in the names listed below:
* **Ef: Apply All Modifiers (Keep Shapekeys)**
  * Applies all modifiers on the object
* **Ef: Apply Subdivision (Keep Shapekeys)**
  * Applies only the top most subdivision modifier and keeps the others
* **Ef: Apply Chosen Modifiers (Keep Shapekeys)**
  * Shows a popup with all modifiers on the object and only applies those you select
  * Might lead to unexpected behaviour if you choose to apply modifiers that aren't at the top of the modifier stack



Select the Object you want to apply modifiers to and select one of the options.
