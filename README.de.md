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
  * [Instanzname](#instanzname)
  * [Licht-Entitäten](#licht-entitäten)
  * [Moving Colors aktivieren](#moving-colors-aktivieren)
  * [Startwert](#startwert)
  * [Minimalwert](#minimalwert)
  * [Maximalwert](#maximalwert)
  * [Schrittweite](#schrittweite)
  * [Trigger-Intervall](#trigger-intervall)
  * [Zufallsgrenzen](#zufallsgrenzen)
  * [Standardwert](#startwert)
  * [Standardmodus aktivieren](#standardmodus-aktivieren)
  * [Farbwert von aktueller Position starten](#farbwert-von-aktueller-position-starten)
  * [Schritte zum Standardwert](#schritte-zum-standardwert)
  * [Debug-Modus](#debug-modus)



# Einführung

**Moving Colors** ist eine Home Assistant Integration, mit der sich die Farben einer RGB-Beleuchtung zufällig ändern lassen. Sie ist einfach zu bedienen und sehr anpassbar, perfekt für alle, die mehr Spaß und Abwechslung in ihre Beleuchtung bringen möchten.

Die Integration kann mit einer oder mehreren Licht-Entitäten konfiguriert werden und ändert die Farben dieser Entitäten in konfigurierbaren Intervallen und mit einstellbarer Schrittweite. Die Änderung erfolgt nicht abrupt, sondern als sanfter Übergang, was einen fließenden und ansprechenden Effekt erzeugt. Sobald die minimale oder maximale Farbe erreicht ist, ändert die Integration die Übergangsrichtung, sodass die Farben sich ohne abrupte Stopps weiter verändern. Der Übergang bewegt sich also wie ein Pendel zwischen den minimalen und maximalen Werten. Zusätzlich ist es möglich, bei jedem Richtungswechsel die neue minimale resp. maximale Grenze zufällig setzen zu lassen, was noch mehr Abwechslung in die Lichteffekte bringt.

Es können sowohl einfache, dimmbare Light-Entitäten, RGB-Light-Entitäten sowie RGBW-Light-Entitäten konfiguriert werden. Werden mehrere Entitäten gleichzeitig verwendet, sollten diese alle vom gleichen Typ sein. Für die interne Konfiguration sowie das Startverhalten werden die Werte der ersten konfigurierten Leuchte verwendet. Alle weiteren Leuchten werden mit den gleichen Werten lediglich gesteuert. Bei RGBW-Leuchten wird der W-Anteil fix auf 0 gesetzt.



# Installation

**Moving Colors** ist eine Default-Integration in HACS. Zur Installation genügt es also, in HACS danach zu suchen, die Integration hinzuzufügen und Home-Assistant neu zu starten. Im Anschluss kann die Integration unter _Einstellungen > Geräte und Dienste_ hinzugefügt werden.



# Konfiguration

## Instanzname
(yaml: `name`)

Eindeutiger Name dieser Moving Colors Instanz. Eine bereinigte Version dieses Namens wird zur Kennzeichnung der Log-Einträge in der Home Assistant Logdatei sowie als Präfix für die von der Integration erstellten Status- und Options-Entitäten verwendet.

Beispiel:
1. Die Instanz wird "LED-Band Wohnraum" genannt
2. Der bereinigte Name ist daraufhin `led_band_wohnraum`
3. Log-Einträge beginnen mit `[moving_colors.led_band_wohnraum]`
4. Status-Entitäten heissen bspw. `sensor.led_band_wohnraum_aktuelles_blau` für den Blau-Anteil bei einer RGB-Leuchte

## Licht-Entitäten
(yaml: `target_light_entity`)

Eine oder mehrere Licht-Entitäten, welche mit dieser Moving Colors Instanz gesteuert werden sollen. Diese müssen innerhalb einer **Moving Colors** Instanz vom gleichen Typ sein.

Im yaml ist die Listen-Syntax zu verwenden:
```yaml
    target_light_entity:
      - light.led_band_wohnraum
      - light.led_band_essbereich
```

## Moving Colors aktivieren
(yaml: `enabled_manual: true|false` u/o `enabled_entity: <entity>`)

De-/Aktivieren der Moving Colors Instanz. Standardwert: aus

## Startwert
(yaml: `start_value_manual: <Wert>` u/o `start_value_entity: <entity>`)

Bei welchem Farbwert soll die Moving Colors Instanz starten.

## Minimalwert
(yaml: `min_value_manual: <Wert>` u/o `min_value_entity: <entity>`)

Minimaler Farbwert, bei welchem die Moving Colors Instanz starten soll.

## Maximalwert
(yaml: `max_value_manual: <Wert>` u/o `max_value_entity: <entity>`)

Maximaler Farbwert, bis zu welchem die Moving Colors Instanz gehen soll.

## Schrittweite
(yaml: `stepping_manual: <Wert>` u/o `stepping_entity: <entity>`)

Schrittweite, um welchen der Farbwert pro Durchlauf erhöht oder verringert werden soll.

## Trigger-Intervall
(yaml: `trigger_interval_manual: <Wert>` u/o `trigger_interval_entity: <entity>`)

Intervall in Sekunden, in welchem die Moving Colors Instanz den Farbwert aktualisieren soll.

## Zufallsgrenzen
(yaml: `random_limits_manual: true|false` u/o `random_limits_entity: <entity>`)

Verwendung zufälliger Grenzen aktivieren.

## Standardwert
(yaml: `default_value_manual: <Wert>` u/o `default_value_entity: <entity>`)

Standardwert beim Beenden des Farbwechsels.

## Standardmodus aktivieren
(yaml: `default_mode_enabled_manual: true|false` u/o `default_mode_enabled_entity: <entity>`)

Verwendung des Standardmodus aktivieren.

## Farbwert von aktueller Position starten
(yaml: `start_from_current_position_manual: true|false` u/o `start_from_current_position_entity: <entity>`)

Wenn aktiviert, wird der Farbverlauf von der jeweils gerade aktiven Farb-Position gestartet.

## Schritte zum Standardwert
(yaml: `steps_to_default_manual: <Wert>` u/o `steps_to_default_entity: <entity>`)

Schritte bis zum Standardwert, wenn der Standardmodus aktiviert ist und der Farbwechsel deaktiviert wird.

## Debug-Modus
(yaml: `debug_enabled`)

Debug-Logs für diese Instanz aktivieren.




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
