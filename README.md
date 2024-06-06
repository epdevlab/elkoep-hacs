# Inels HACS integration

<!--[![GitHub Release][releases-shield]][releases]-->
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]](http://github.com/ZeD4805)
[![Community Forum][forum-shield]][forum]

Repository of the official iNELS MQTT Home Assistant Community Store integration.

[![iNELS_icon][iNELS_icon]][iNELS]

[![elko_ep_icon][elko_ep_icon]][elko_ep]

[iNELS][iNELS] by [ELKO EP][elko_ep]

## Features
Allows the integration of both wireless and bus based [iNELS] devices.

Platforms used:
Platform | Description
-- | --
`binary_sensor` | Mostly used to show binary input sensors, motion sensors, proximity sensors...
`button` | Used to trigger HA automations as if the physical buttons were pressed themselves
`climate` | Used to control thermovalves and thermostat behaviour
`cover` | Used to control shutters
`light` | Used to control various types of lights (dimmable lights, RGB, DALI...)
`sensor` | Used to show a wide array of sensors and their values (temperature, voltage, humidity, light...)
`select` | Used to display and select from a given number of options (used only to control fan speed)
`switch` | Used to control relays in the devices

## Supported devices
### Wireless
- Switches (01, 02)
- Shutters (03, 21)
- Light dimmers (04, 05)
- RGB dimmer (06)
- Switches with external temperature sensors (07)
- Wireless thermovalves (09)
- Temperature sensors (10)
- Thermostats (12)
- Flood detectors (15)
- Generic detector (16)
- Motion detector (17)
- Controllers/buttons (18, 19)
- Temperature and humidity sensors (29)

### Bus

- SA3-01B (100)
- DA3-22M (101)
- GRT3-50 (102)
- GSB3-90Sx (103)
- SA3-02B (104)
- SA3-02M (105)
- SA3-04M (106)
- SA3-06M (107)
- SA3-012M (108)
- SA3-022M (109)
- FA3-612M (111)
- IOU3-108M (112)
- RC3-610DALI (114)
- IM3_20B (115)
- IM3_40B (116)
- IM3_80B (117)
- DMD3-1 (120)
- IM3-140M (121)
- WSB3-20 (122)
- WSB3-40 (123)
- WSB3-20H (124)
- WSB3-40H (125)
- GCR3-11 (128)
- GCH3-31 (129)
- GSP3-100 (136)
- GDB3-10 (137)
- GSB3-40SX (138)
- GSB3-60SX (139)
- GSB3-20SX (140)
- GBP3-60 (141)
- GSB3-40-V2 (143)
- GSB3-60-V2 (144)
- GSB3-90-V2 (146)
- DAC3-04B (147)
- DAC3-04M (148)
- DCDA-33M (150)
- DA3-66M (151)
- ADC3-60M (156)
- TI3-10B (157)
- TI3-40B (158)
- TI3-60M (159)
- IDRT3-1 (160)
- JA3-018M (163)
- DALI-DMX-Unit (164)
- DALI-DMX-Unit-02 (165)
- Virtual controller (166)
- Virtual heating regulator (167)
- Virtual cooling regulator (168)
- SA3_014M (169)
- JA3_014M (170)
- GSB3-40Sx-V2 (174)
- GSB3-60Sx-V2 (175)
- GSB3-90Sx-V2 (176)
- MSB3-40 (177)
- MSB3-60 (178)
- MSB3-90 (179)
- BITS (bits)
- INTEGETS (integers)

[iNELS_icon]: https://www.inels.com/media/img/logo.png
[iNELS]: https://www.inels.com/
[elko_ep_icon]: https://www.elkoep.com/media/img/logo.png
[elko_ep]: https://www.elkoep.com
[commits-shield]: https://img.shields.io/github/commit-activity/y/ZeD4805/inels-hacs-new.svg?style=for-the-badge
[commits]: https://github.com/ZeD4805/inels-hacs-new/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/ZeD4805/inels-hacs-new.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-ZeD4805-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/ZeD4805/inels-hacs-new.svg?style=for-the-badge
[releases]: https://github.com/ZeD4805/inels-hacs-new/releases
