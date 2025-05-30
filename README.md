# android-tracing

## overview

This repository contains two python projects in `src/`: 

1. `adbdevice`
    - python bindings for adb (hw and emulator devices supported)
    - emulator control for automated creation/start/stop of emulators
2. `aproftracer`
    - depends on adbdevice
    - runs profile coverage experiments
        - starts emulator if asked to
        - installs apps from .apk + .dm if asked to
        - calculates offsets in .oat files
        - prepares and starts tracing using uprobe events for a given list of offsets
        - runs baseline/monkey/droidbot experiment
        - collects results
        - cleans up if asked to

The `experiments` folder contains Makefiles to run experiments, including downloading apps and cloud profiles. 

The `dependencies` folder contains external dependencies that are not automatically installed. Install with `git submodule update --init`. Because the tools need patches, see the [dependencies/README.md] for more info.

## setup

1. create a pyenv for python 3.11.5
2. run `pip instell -e .` in both projects in `src/`
3. run `git submodule update --init` to fetch the dependencies droidbot and acvtool
    a. apply the acvtool patch
4. run `aproftracer --help` to get an overview of functionality

