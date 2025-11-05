# aproftracer - Android Profile Tracing Using Linux Uprobes

This is the repository for the ASE paper [Profile Coverage: Using Android Compilation Profiles to Evaluate Dynamic Testing](https://conf.researchr.org/details/ase-2025/ase-2025-papers/31/Profile-Coverage-Using-Android-Compilation-Profiles-to-Evaluate-Dynamic-Testing). You can find the originally submitted artifact under the [submitted-version tag](https://github.com/SecPriv/android-profile-tracing/tree/submitted-version).

We are preparing to upstream our patches to [apkeep](https://github.com/EFForg/apkeep) to download cloud profiles easily. If you can't wait for it to be available, you can check out our [fork of apkeep](https://github.com/themoep/apkeep) and its dependency [rs-google-play](https://github.com/themoep/rs-google-play).

## Overview

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

The `experiments` folder contains Makefiles to run experiments, including downloading apps and cloud profiles. We use a patched version of [apkeep](https://github.com/themoep/apkeep/) and [rs-google-play](https://github.com/themoep/rs-google-play/), and are in the process of upstreaming our patches.

The `dependencies` folder contains external dependencies that are not automatically installed. Install with `git submodule update --init`. Because the tools need patches, see the [dependencies/README.md] for more info.

## Setup

1. create a pyenv for python 3.11.5
2. run `pip instell -e .` in both projects in `src/`
3. run `aproftracer --help` to get an overview of functionality
4. install dependencies:
    a. run `git submodule update --init` to fetch the dependencies droidbot, acvtool, and fastbot.
    b. see the [dependencies/Readme.md] for further instructions to apply necessary patches 

## Updates

Installing an app that requires split-APKs can fail when instrumented with ACVTool because the resulting base.apk will have a different signature from the split-APKs. Thanks to Aleksandr Pilgun, who pointed this out and provided the following recommendation:

```sh
acv instrument base.apk
acvpatcher -a split_config.arm64_v8a.apk
acvpatcher -a split_config.xhdpi.apk
adb uninstall <package>
adb install-multiple *.apk
```
