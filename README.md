![logo](/images/logo.svg#gh-light-mode-only)
![logo](/images/dark_logo.svg#gh-dark-mode-only)

# Moving Colors

**A Home Assistant integration to randomize rgb lights.**

![Version](https://img.shields.io/github/v/release/starwarsfan/moving-colors?style=for-the-badge) 
[![Tests][tests-badge]][tests]
[![Coverage][coverage-badge]][coverage]
[![hacs_badge][hacsbadge]][hacs] 
[![github][ghsbadge]][ghs] 
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee] 
[![PayPal][paypalbadge]][paypal] 
[![hainstall][hainstallbadge]][hainstall]

Gehe zur [deutschen Version](/README.de.md) der Dokumentation.

## Table of content

* [What it does](#what-it-does)
* [Installation](#installation)
* [Configuration](#configuration)
  * [Instance name](#instance-name)
  * [Light entities](#light-entities)
  * [Enable Moving Colors](#enable-moving-colors)
  * [Start value](#start-value)
  * [Minimum value](#minimum-value)
  * [Maximum value](#maximum-value)
  * [Step value](#step-value)
  * [Trigger intervall](#trigger-intervall)
  * [Random limits](#random-limits)
  * [Start color value from current position](#start-color-value-from-current-position)
  * [Activate default mode](#activate-default-mode)
  * [Default value](#default-value)
  * [Steps to default value](#steps-to-default-value)
  * [Debug mode](#debug-mode)
* [Configuration by YAML](#configuration-by-yaml)
  * [Example YAML configuration](#example-yaml-configuration)



# What it does

**Moving Colors** is a Home Assistant integration that allows you to randomize the colors of your RGB lights. It is designed to be easy to use and highly customizable, making it perfect for anyone who wants to add some fun and variety to their home lighting.

The integration can be configured with one or more light entities, and it will randomly change the colors of those lights at a specified interval and step size. This change is not a hard switch, but rather a gradual transition to the new color, creating a smooth and visually appealing effect. As soon as the minimum or maximum color is reached, the integration will change the transition direction, ensuring that the colors keep changing without abrupt stops. So the transition will move like a pendulum in between the minimum and maximum colors. Additionally, it is possible to let the integration choose random minimum and maximum colors for each transition, adding even more variety to the lighting effects.

The integration can handle simple dimmable light entities, RGB light entities as well as RGBW light entities. If there are multiple entities configured, all of them should be from the same type. The internal configuration will use the values and features from the first configured entity. All others will simply be driven with the same values. If using RGBW entities, the white part will be set to zero all the time. 



# Installation

**Moving Colors** is a default HACS integration, so you can install the integration by searching for it within HACS. After that, restart Home-Assistant and add the integration.



# Configuration

## Instance name
(yaml: `name`)

A descriptive and unique name for this Moving Colors instance. A sanitized version of this name will be used to mark corresponding log entries of this instance within the Home Assistant main log file as well as prefix for the created entities.

Example:
1. The instance is named "Dining room LED strip"
2. The sanitized name will be "dining_room_led_strip"
3. Log entries start with `[moving_colors.dining_room_led_strip]`
4. Entities will be named e.g. like `sensor.dining_room_led_strip_current_blue` for the blue part of an RGB entity

## Light entities
(yaml: `target_light_entity`)

Light entity, which should be handled by this Moving Colors instance. All of then should be from the same type within one instance of **Moving Colors**.

Within yaml you need to use the list syntax:
```yaml
    target_light_entity:
      - light.dining_room_led_strip
      - light.living_room_led_strip
```

## Enable Moving Colors
(yaml: `enabled_manual: true|false` u/o `enabled_entity: <entity>`)

Enable Moving Colors for this instance. Default: off

## Start value
(yaml: `start_value_manual: <Wert>` u/o `start_value_entity: <entity>`)

Start value for the color transition.

## Minimum value
(yaml: `min_value_manual: <Wert>` u/o `min_value_entity: <entity>`)

Minimum value for the color transition.

## Maximum value
(yaml: `max_value_manual: <Wert>` u/o `max_value_entity: <entity>`)

Maximum value for the color transition.

## Step value
(yaml: `stepping_manual: <Wert>` u/o `stepping_entity: <entity>`)

Step value for the color transition.

## Trigger intervall
(yaml: `trigger_interval_manual: <Wert>` u/o `trigger_interval_entity: <entity>`)

Trigger interval in seconds for the color transition.

## Random limits
(yaml: `random_limits_manual: true|false` u/o `random_limits_entity: <entity>`)

Enable or disable the use of random limits.

By default, random limits are used. This means that the limits for changing direction are chosen randomly. When a limit is reached, the opposite limit is randomly determined within the range between the minimum and maximum value. The integration will, for the first run, go up to the max value. When this value is reached, a new random min value is chosen between the min and max, and the direction is reversed. When the min value is reached, a new random max value is chosen between the current min and max, and the direction is reversed again. This results in different limits and a unique dimming curve for each run.

If random behavior is disabled, the dimming will always oscillate between the min and max values.

## Start color value from current position
(yaml: `start_from_current_position_manual: true|false` u/o `start_from_current_position_entity: <entity>`)

If enabled, the color transition will start from the currently active color position.

## Activate default mode
(yaml: `default_mode_enabled_manual: true|false` u/o `default_mode_enabled_entity: <entity>`)

Enable the use of default mode. Default: off

If the instance is disabled and this option is active, the [default value](#default-value) will be reached using the number of steps specified in [steps to default value](#steps-to-default-value). Otherwise, the color animation will simply stop at the last position.

## Default value
(yaml: `default_value_manual: <Wert>` u/o `default_value_entity: <entity>`)

Default value when ending the color transition.

The value configured here will be reached using the number of steps specified in [steps to default value](#steps-to-default-value) when the instance is disabled and [default mode](#activate-default-mode) is enabled.

## Steps to default value
(yaml: `steps_to_default_manual: <Wert>` u/o `steps_to_default_entity: <entity>`)

Number of steps to reach the default value when default mode is enabled and the color transition is disabled.

## Debug mode
(yaml: `debug_enabled`)

Enable debug logs for this instance.

# Configuration by YAML

It is possible to configure **Moving Colors** instances using YAML. To do so, you need to add the corresponding configuration to `configuration.yaml` and restart Home Assistant. After that, the YAML configuration will be loaded and **Moving Colors** will create the corresponding instances. These instances can then be modified using Home Assistant ConfigFlow. Changes made directly to the YAML configuration will not be applied, as the entire configuration is managed via Home Assistant ConfigFlow. To reload the YAML configuration, you need to remove the existing **Moving Colors** instances and restart Home Assistant.

## Example YAML configuration

The entries within the configuration follow the mentioned keywords within the documentation above. Unused keywords must be commented (disabled) or removed.

```yaml
moving_colors:
  - name: "MC Dummy 2"
    target_light_entity:
      - light.licht_buro_2
    #debug_enabled: false
    #enabled_manual: false
    #enabled_entity:
    #start_value_manual: 125
    #start_value_entity:
    #min_value_manual: 0
    #min_value_entity:
    #max_value_manual: 255
    #max_value_entity:
    #stepping_manual: 3
    #stepping_entity:
    #trigger_interval_manual: 3
    #trigger_interval_entity:
    #random_limits_manual: true
    #random_limits_entity:
    #default_mode_enabled_manual: false
    #default_mode_enabled_entity:
    #default_value_manual: 125
    #default_value_entity:
    #steps_to_default_manual: 10
    #steps_to_default_entity:
```



[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-blue?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[ghs]: https://github.com/sponsors/starwarsfan
[ghsbadge]: https://img.shields.io/github/sponsors/starwarsfan?style=for-the-badge&logo=github&logoColor=ccc&link=https%3A%2F%2Fgithub.com%2Fsponsors%2Fstarwarsfan&label=Sponsors

[buymecoffee]: https://www.buymeacoffee.com/starwarsfan
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a-coffee-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[paypal]: https://paypal.me/ysswf
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc

[hainstall]: https://my.home-assistant.io/redirect/config_flow_start/?domain=moving_colors
[hainstallbadge]: https://img.shields.io/badge/dynamic/json?style=for-the-badge&logo=home-assistant&logoColor=ccc&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.moving_colors.total

[tests]: https://github.com/starwarsfan/moving-colors/actions/workflows/test.yml
[tests-badge]: https://img.shields.io/github/actions/workflow/status/starwarsfan/moving-colors/test.yml?style=for-the-badge&logo=github&logoColor=ccc&label=Tests

[coverage]: https://app.codecov.io/github/starwarsfan/moving-colors
[coverage-badge]: https://img.shields.io/codecov/c/github/starwarsfan/moving-colors?style=for-the-badge&logo=codecov&logoColor=ccc&label=Coverage
