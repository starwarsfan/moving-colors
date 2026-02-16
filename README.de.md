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
  * [Farbwert von aktueller Position starten](#farbwert-von-aktueller-position-starten)
  * [Standardmodus aktivieren](#standardmodus-aktivieren)
  * [Standardwert](#startwert)
  * [Schritte zum Standardwert](#schritte-zum-standardwert)
  * [Debug-Modus](#debug-modus)
* [Konfiguration via yaml](#konfiguration-via-yaml)
  * [yaml Beispielkonfiguration](#yaml-beispielkonfiguration)



# Einführung

**Moving Colors** ist eine Home Assistant Integration, mit der sich die Farben einer RGB-Beleuchtung zufällig ändern lassen. Sie ist einfach zu bedienen und sehr anpassbar, perfekt für alle, die mehr Spaß und Abwechslung in ihre Beleuchtung bringen möchten.

Die Integration kann mit einer oder mehreren Licht-Entitäten konfiguriert werden und ändert die Farben dieser Entitäten in konfigurierbaren Intervallen und mit einstellbarer Schrittweite. Die Änderung erfolgt nicht abrupt, sondern als sanfter Übergang, was einen fließenden und ansprechenden Effekt erzeugt. Sobald die minimale oder maximale Farbe erreicht ist, ändert die Integration die Übergangsrichtung, sodass die Farben sich ohne abrupte Stopps weiter verändern. Der Übergang bewegt sich also wie ein Pendel zwischen den minimalen und maximalen Werten. Zusätzlich ist es möglich, bei jedem Richtungswechsel die neue minimale resp. maximale Grenze zufällig setzen zu lassen, was noch mehr Abwechslung in die Lichteffekte bringt.

Es können sowohl einfache, dimmbare Light-Entitäten, RGB-Light-Entitäten sowie RGBW-Light-Entitäten konfiguriert werden. Werden mehrere Entitäten gleichzeitig verwendet, sollten diese alle vom gleichen Typ sein. Für die interne Konfiguration sowie das Startverhalten werden die Werte der ersten konfigurierten Leuchte verwendet. Alle weiteren Leuchten werden mit den gleichen Werten lediglich gesteuert. Bei RGBW-Leuchten wird der W-Anteil fix auf 0 gesetzt.



# Installation

**Moving Colors** ist eine Default-Integration in HACS. Zur Installation genügt es also, in HACS danach zu suchen, die Integration hinzuzufügen und Home-Assistant neu zu starten. Im Anschluss kann die Integration unter _Einstellungen > Geräte und Dienste_ hinzugefügt werden.



# Konfiguration

## Instanzname
(yaml: `name`)

Eindeutiger Name dieser **Moving Colors** Instanz. Eine bereinigte Version dieses Namens wird zur Kennzeichnung der Log-Einträge in der Home Assistant Logdatei sowie als Präfix für die von der Integration erstellten Status- und Options-Entitäten verwendet.

Beispiel:
1. Die Instanz wird "LED-Band Wohnraum" genannt
2. Der bereinigte Name ist daraufhin `led_band_wohnraum`
3. Log-Einträge beginnen mit `[moving_colors.led_band_wohnraum]`
4. Status-Entitäten heissen bspw. `sensor.led_band_wohnraum_aktuelles_blau` für den Blau-Anteil bei einer RGB-Leuchte

## Licht-Entitäten
(yaml: `target_light_entity`)

Eine oder mehrere Licht-Entitäten, welche mit dieser **Moving Colors** Instanz gesteuert werden sollen. Diese müssen innerhalb einer **Moving Colors** Instanz vom gleichen Typ sein.

Im yaml ist die Listen-Syntax zu verwenden:
```yaml
    target_light_entity:
      - light.led_band_wohnraum
      - light.led_band_essbereich
```

## Moving Colors aktivieren
(yaml: `enabled_manual: true|false` u/o `enabled_entity: <entity>`)

De-/Aktivieren der **Moving Colors** Instanz. Standardwert: aus

Sobald diese Option auf "on" gesetzt wird, startet die **Moving Colors** Instanz mit dem Farbverlauf.

## Startwert
(yaml: `start_value_manual: <Wert>` u/o `start_value_entity: <entity>`)

Bei welchem (Farb-)wert soll die **Moving Colors** Instanz starten.

## Minimalwert
(yaml: `min_value_manual: <Wert>` u/o `min_value_entity: <entity>`)

Minimaler (Farb-)wert, bis zu welchem die **Moving Colors** Instanz herunter dimmen soll.

## Maximalwert
(yaml: `max_value_manual: <Wert>` u/o `max_value_entity: <entity>`)

Maximaler (Farb-)wert, bis zu welchem die **Moving Colors** Instanz herauf dimmen soll.

## Schrittweite
(yaml: `stepping_manual: <Wert>` u/o `stepping_entity: <entity>`)

Schrittweite, um welchen der Farbwert pro Durchlauf erhöht oder verringert werden soll.

Die Schrittweite gibt an, um welchen Betrag der aktuelle Dimm-Wert je nach Dimm-Richtung erhöht oder vermindert werden soll. Bei kleinen Werten ist die Veränderung der Dimmung fast nicht wahrnehmbar, bei größeren Werten erscheint sie mitunter ruckartig. Das ist aber auch von der verwendeten Leuchte resp. deren Trägheit beim Ändern der Dimmung abhängig und muss wie alle anderen Werte auch, an die örtlichen Gegebenheiten angepasst werden.

## Trigger-Intervall
(yaml: `trigger_interval_manual: <Wert>` u/o `trigger_interval_entity: <entity>`)

Intervall in Sekunden, in welchem die **Moving Colors** Instanz den Farbwert aktualisieren soll.

Für eine langsame und sanfte Dimmung sollte die Schrittweite nicht zu groß und das Trigger-Intervall nicht zu klein gewählt werden. Es ist zu beachten, dass jeder Durchlauf des Bausteines bei KNX-Leuchten die entsprechenden Dimm-Befehle auf den Bus sendet, was je nach Anzahl der verwendeten Instanzen und dem verwendeten Intervall eine nicht unerhebliche Buslast erzeugen kann!

## Zufallsgrenzen
(yaml: `random_limits_manual: true|false` u/o `random_limits_entity: <entity>`)

Verwendung zufälliger Grenzen de-/aktivieren.

Per Default werden zufällige Grenzwerte verwendet. Das bedeutet, dass die Grenzwerte der Richtungsumkehr zufällig gewählt werden. Bei Erreichen eines Grenzwertes wird immer der jeweils gegenüberliegende Grenzwert neu als Zufallswert ermittelt. Der Baustein läuft also beim ersten Durchlauf bis zum Max-Wert. Bei Erreichen dieses Wertes wird für den Min-Wert ein zufälliger Wert aus dem Bereich Min-Wert bis Max-Wert ermittelt und die Dimm-Richtung umgekehrt. Erreicht der Baustein den errechneten Min-Wert, wird aus dem Bereich des aktuellen Min-Wertes bis zum Max-Wert ein zufälliger neuer Max-Wert ermittelt und die Dimm-Richtung erneut gewechselt. Somit ergeben sich bei jedem Durchlauf andere Grenzwerte und die Dimmkurve ist bei jedem Durchlauf anders.

Wird das Zufallsverhalten deaktiviert, pendelt die Dimmung immer zwischen den Min-/Max-Werten.

## Farbwert von aktueller Position starten
(yaml: `start_from_current_position_manual: true|false` u/o `start_from_current_position_entity: <entity>`)

Wenn aktiviert, wird der Farbverlauf von der jeweils gerade aktiven Farb-Position gestartet.

## Standardmodus aktivieren
(yaml: `default_mode_enabled_manual: true|false` u/o `default_mode_enabled_entity: <entity>`)

Verwendung des Standardmodus aktivieren. Default: aus

Wenn die Instanz deaktiviert wird und diese Option ist aktiv, wird der [Standarwert](#standardwert) mit den unter [Schritte zum Standardwert](#schritte-zum-standardwert) angegebenen Schritten angefahren. Anderenfalls bleibt die Farbanimation einfach an der letzten Position stehen.

## Standardwert
(yaml: `default_value_manual: <Wert>` u/o `default_value_entity: <entity>`)

Standardwert beim Beenden des Farbwechsels.

Der hier konfigurierte Wert wird mit den unter [Schritte zum Standardwert](#schritte-zum-standardwert) angegebenen Schritten angefahren, wenn die Instanz deaktiviert wird und der [Standardmodus](#standardmodus-aktivieren) aktiviert ist.

## Schritte zum Standardwert
(yaml: `steps_to_default_manual: <Wert>` u/o `steps_to_default_entity: <entity>`)

Schritte bis zum Standardwert, wenn der Standardmodus aktiviert ist und der Farbwechsel deaktiviert wird.

## Debug-Modus
(yaml: `debug_enabled`)

Debug-Logs für diese Instanz aktivieren.



# Konfiguration via yaml

Es ist möglich, die **Moving Colors** Instanzen via yaml zu konfigurieren. Dazu müssen die entsprechenden Konfigurationen im `configuration.yaml` einmalig eingetragen und Home Assistant neu gestartet werden. **Moving Colors** wird die yaml-Konfiguration einlesen und entsprechende Instanzen anlegen. Diese Instanzen können im Anschluss via ConfigFlow bearbeitet werden. Änderungen an der yaml-Konfiguration werden nicht übernommen, da die gesamte Konfiguration via Home Assistant ConfigFlow abgebildet wird. Sollen die yaml-Konfigurationen dennoch neu eingelesen werden, müssen die entsprechenden **Moving Colors** Instanzen zunächst gelöscht und dann Home Assistant neu gestartet werden.

## yaml Beispielkonfiguration

Die Einträge der Konfiguration folgen den oben in der Dokumentation jeweils genannten Schlüsselwörtern. Nicht verwendete Schlüsselwörter müssen auskommentiert oder entfernt werden.

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
