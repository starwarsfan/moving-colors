# Changes

## 0.4.0
### New features
* New option `startup_brightness_manual` / `startup_brightness_entity` (default: 100%) to control the brightness applied once when an RGB/RGBW light turns on from off. Previously, brightness was forced to 100% on every single color transition step, overriding any manual brightness adjustment made while the loop was active. Brightness is now only touched once, when the light turns on from off - manual adjustments during an active transition are preserved. (https://github.com/starwarsfan/moving-colors/issues/77)

## 0.3.0
### Fixes
* Update CI test matrix and minimum required Python version to 3.13, matching current Home Assistant version requirements (https://github.com/starwarsfan/shadow-control/issues/136)

## 0.2.0
### Fixes
* Internal error handling updated
* Improved documentation

## 0.1.0
* Initial release
* Automated release creation using GitHub Actions
* Migrated functionality from Edomi-LBS into Home Assistant custom integration
* Fully configurable using
  * Home Assistant ConfigFlow
  * YAML import
