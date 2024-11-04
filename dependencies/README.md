# REAMDE - dependencies

To install the dependencies such that the experiments can be reproduced, clone the submodules with `git submodule update --init`.
Then follow the specific instructions to set up the external tools. Usually, this means applying our patches in order to get the dependencies to a working state.

To save new changes in the dependencies, run `git diff > ../<toolname>.patch` in the tools main folder.

# ACVTool

1. run `make acvtool-00-apply-diff` to apply the patch allowing:
    - parallel execution of acvtool by removing logging to hardcoded files
    - passing the device id to all adb commands, allowing parallelization
    - hardcoding the path of sdktools (requires changes in `~/acvtool/config.json` to match your username)
    - fixing versions and bugs
2. run `make acvtool-01-prepare` to:
    - install a protobuf compiler, if it is myssing pyaxml throws strange errors
    - create a new pyenv, because droidbot depends on a different version of androguard that is not compatible with what acvtool uses.
    - install acvtool in the pyenv

# Droidbot

1. run `make droidbot-00-apply-diff`
    - fix androguard version and cli paths so it can be used from anywhere as cli tool
2. run `make droidbot-01-install`
    - install droidbot

# Fastbot2

1. [install sdkman](https://sdkman.io/install/) as per fastbot requirements
    - also make sure `ANDROID_SDK_ROOT` and `NDK_ROOT` is set and `cmake;3.18.1` and `ndk;25.2.9519653` installed using sdkmanager and `cmake` is resolving correctly

2. run `make fastbot-00-setup-gradle`
    - installs gradle environment and sets gradle wrapper

3. run `make fastbot-01-apply-diff`
    - sets target sdk to 34 and handles an error with new screen rotation api in sdk 34

4. run `fastbot-02-build-cached`
    - builds the necessary files to run fastbot and copy them to `fastbot_cache`, where the experiments are expecting them.

