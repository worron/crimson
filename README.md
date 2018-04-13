## Crimson
Simple minimalistic grub2 theme with customizable colors. No background included, just use your favorite one.

#### Example
[![](https://i.imgur.com/FjwUFtB.png)](https://imgur.com/a/SSdHd)

#### Build
Use `build.py` script to create theme with given colors and background. New generated theme  will be placed into `crimson` folder.  Check `build --help` for more info.

WARNING: script doesn't verify input data and result. Check the theme with 'grub2-theme-preview' utility or some virtual machine to be safe.

#### Known issues
Somehow console background theming doesn't work for me. Still console background image can be set directly by grub config, see `custom.cfg`.