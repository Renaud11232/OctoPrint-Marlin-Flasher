# OctoPrint-Marlin-Flasher

This plugins makes the upgrade of your Marlin (or any Arduino based) firmware possible directly within OctoPrint.
Simply connect to your printer, upload your firmware code, select your motherboard type, and click flash.**DONE**.

![](/extras/assets/img/plugins/marlin_flasher/sketch.png)

![](/extras/assets/img/plugins/marlin_flasher/cores.png)

![](/extras/assets/img/plugins/marlin_flasher/libraries.png)

![](/extras/assets/img/plugins/marlin_flasher/flash.png)

## Setup

First, you'll need to download and install `arduino-cli` from their official [GitHub page](https://github.com/arduino/arduino-cli).

Then, install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/Renaud11232/Octoprint-Marlin-Flasher/archive/master.zip

## Configuration

In order to be able to use Marlin Flasher properly you will need to increase the maximum request size. This is necessary
to successfully upload your firmware if the files weights more than 100kB. You will need to edit
[config.yaml](https://docs.octoprint.org/en/master/configuration/config_yaml.html)

```yaml
server:
  maxSize: 102400000
```

There are two configurable options:
* The path to your `arduino-cli` executable
* The name of the Arduino sketch (defaults to `Marlin.ino`)

Both can be configured directly though the *Settings* menu. or via the [config.yaml](https://docs.octoprint.org/en/master/configuration/config_yaml.html)

```yaml
plugins:
  marlin_flasher:
    arduino_path: /path/to/arduino-cli
    sketch_ino: Marlin.ino
```

You may also want to add custom boards ie: `Sanguino`. To do that edit the arduino-cli configuration file manually (cf: `arduino-cli` official documentation)
