# OctoPrint-Marlin-Flasher

This plugins makes the upgrade of your Marlin firmware possible directly within OctoPrint.
Simply connect to your printer, upload your firmware code, select your motherboard type, and click flash. **DONE**.

It also supports Platform.io so even 32 bits boards can be flashed!.

## Screenshots

### Arduino

![Arduino Sketch](.github/img/arduino_sketch.png)

![Arduino Cores](.github/img/arduino_cores.png)

![Arduino Libraries](.github/img/arduino_libraries.png)

![Arduino Flash](.github/img/arduino_flash.png)

### Platform.io

![Platform.io Sketch](.github/img/pio_project.png)

![Platform.io Flash](.github/img/pio_flash.png)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/Renaud11232/Octoprint-Marlin-Flasher/archive/master.zip

### Arduino

First, you'll need to download `arduino-cli` from their official [GitHub page](https://github.com/arduino/arduino-cli/releases). Then all is left to do is to tell the plugin where you placed it via the settings.

### Platfrom.io

You first need to install PlatformIO-Core following their [official documentation](https://docs.platformio.org/en/latest/installation.html). Then as for Arduino, you need to tell the plugin where its installed.

## Configuration

There are a few configurable options:
* The name of the Arduino sketch (defaults to `Marlin.ino`)
* The path to your `arduino-cli` executable
* The additional boards urls (ie: Sanguino)
* The path for your PlatformIO-Core executable
* The maximum file upload size (defaults to `20MB`)
* The currently selected platform (Arduino, PlatformIO)

All can be configured directly though the *Settings* menu. or via the [config.yaml](https://docs.octoprint.org/en/master/configuration/config_yaml.html)

```yaml
plugins:
  marlin_flasher:
    arduino:
      sketch_ino: Marlin.ino
      cli_path: /path/to/arduino-cli
      additional_urls: 'https://what.ever/boards.json'
    platformio:
      cli_path: /path/to/platformio
    max_upload_size: 20
    platform_type: arduino
```

## Wiki

If you need more help on how to setup and use the plugin feel free to check the [wiki](https://github.com/Renaud11232/OctoPrint-Marlin-Flasher/wiki)

## Need help ?

If you need help please [open an issue](https://github.com/Renaud11232/OctoPrint-Marlin-Flasher/issues/new).
