# Blender Addon - SKkeeper
![SKkeeper Logo splash](images/skkeeper_splash.png)
This Addon automates the process of collapsing down modifiers on a mesh with shapekeys while keeping the shapekeys intact.

## How to Install

Download the zipfile from the [Releases page](https://github.com/smokejohn/SKkeeper/releases) and install via Blenders Addon-Preferences

Edit > Preferences > Add-ons > Install... > Select SKkeeper.zip

## How to Use

This Addon adds 3 new operators which can be found in the 3DViews Object Menu:

<img style="margin-right: 30px;" align="left" src="images/bl_gui_3DVIEW_MT_object.png"/>

* **Sk: Apply All Modifiers (Keep Shapekeys)**
  * Applies all modifiers on the object
* **Sk: Apply Subdivision (Keep Shapekeys)**
  * Applies only the top most subdivision modifier and keeps the others
* **Sk: Apply Chosen Modifiers (Keep Shapekeys)**
  * Shows a popup with all modifiers on the object and only applies those you select
  * Might lead to unexpected behaviour if you choose to apply modifiers that aren't at the top of the modifier stack

Select the Object you want to apply modifiers to and select one of the options.

you can also search for the operators via the Quick Search floater (**Hotkey: F3**) and typing "shapekey" or other keywords in the names of the operators.
