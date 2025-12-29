![logo](/images/logo.svg#gh-light-mode-only)
![logo](/images/dark_logo.svg#gh-dark-mode-only)

# Moving Colors

**Eine Home Assistant Integration zur zufälligen Änderung von RGB-Beleuchtung.**

![Version](https://img.shields.io/github/v/release/starwarsfan/moving-colors?style=for-the-badge) 
[![Tests][tests-badge]][tests]
[![Coverage][coverage-badge]][coverage]
[![hacs_badge][hacsbadge]][hacs] 
[![github][ghsbadge]][ghs] 
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee] 
[![PayPal][paypalbadge]][paypal] 
[![hainstall][hainstallbadge]][hainstall]

Go to the [English version](/README.md) version of the documentation.

## Inhaltsverzeichnis

* [Einführung](#einführung)
* [Installation](#installation)
* [Konfiguration](#konfiguration)



# Einführung

**Moving Colors** ist eine Home Assistant Integration, mit der sich die Farben einer RGB-Beleuchtung zufällig ändern lassen. Sie ist einfach zu bedienen und sehr anpassbar, perfekt für alle, die mehr Spaß und Abwechslung in ihre Beleuchtung bringen möchten.

Die Integration kann mit einer oder mehreren Licht-Entitäten konfiguriert werden und ändert die Farben dieser Entitäten in konfigurierbaren Intervallen und mit einstellbarer Schrittweite. Die Änderung erfolgt nicht abrupt, sondern als sanfter Übergang, was einen fließenden und ansprechenden Effekt erzeugt. Sobald die minimale oder maximale Farbe erreicht ist, ändert die Integration die Übergangsrichtung, sodass die Farben sich ohne abrupte Stopps weiter verändern. Der Übergang bewegt sich also wie ein Pendel zwischen den minimalen und maximalen Werten. Zusätzlich ist es möglich, bei jedem Richtungswechsel die neue minimale resp. maximale Grenze zufällig setzen zu lassen, was noch mehr Abwechslung in die Lichteffekte bringt.



# Installation

**Moving Colors** ist eine Default-Integration in HACS. Zur Installation genügt es also, in HACS danach zu suchen, die Integration hinzuzufügen und Home-Assistant neu zu starten. Im Anschluss kann die Integration unter _Einstellungen > Geräte und Dienste_ hinzugefügt werden.



# Konfiguration

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

[coverage]: https://codecov.io/gh/starwarsfan/moving-colors
[coverage-badge]: https://img.shields.io/codecov/c/github/starwarsfan/moving-colors?style=for-the-badge&logo=codecov&logoColor=ccc&label=Coverage

[ruff]: https://github.com/astral-sh/ruff
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge
