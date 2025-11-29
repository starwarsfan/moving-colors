![Version](https://img.shields.io/github/v/release/starwarsfan/moving-colors?style=for-the-badge)

![logo](/images/logo.svg#gh-light-mode-only)
![logo](/images/dark_logo.svg#gh-dark-mode-only)

# Moving Colors

**A Home Assistant integration to randomize rgb lights.**

Gehe zur [deutschen Version](/README.de.md) oder <a href="https://coff.ee/starwarsfan" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

## Table of content

* [What it does](#what-it-does)
* [Installation](#installation)
* [Configuration](#configuration)



# What it does

**Moving Colors** is a Home Assistant integration that allows you to randomize the colors of your RGB lights. It is designed to be easy to use and highly customizable, making it perfect for anyone who wants to add some fun and variety to their home lighting.

The integration can be configured with one or more light entities, and it will randomly change the colors of those lights at a specified interval and step size. This change is not a hard switch, but rather a gradual transition to the new color, creating a smooth and visually appealing effect. As soon as the minimum or maximum color is reached, the integration will change the transition direction, ensuring that the colors keep changing without abrupt stops. So the transition will move like a pendulum in between the minimum and maximum colors. Additionally, it is possible to let the integration choose random minimum and maximum colors for each transition, adding even more variety to the lighting effects.



# Installation

**Moving Colors** is a default HACS integration, so you can install the integration by searching for it within HACS. After that, restart Home-Assistant and add the integration.



# Configuration
