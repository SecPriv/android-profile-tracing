# Notes

## droidbot

- droidbot requires an older androguard version, pre-4.0, due to changes in the API
- the default install also doesn't import the entrypoint correctly

## acvtool

- is special since it wants to run from commandline - we provide wrappers in the experiments folder
- for this, the experiments have their own pyenv and softlink the acvtool directory so it's locally executable
- acvtool also drops a configfile in `~/acvtool/config.json`, which specifies which binaries are used for aapt/zipalign/adb/apksigner
    - if "ANDROID_DATA not set" is thrown, change aapt to aapt2 in the config file.
- oh my gosh, acvtool does not pass the device-id to all incantations of adb, making it not usable with multiple emulatores/devices.
    - aaaargh.
    - this is also in the provided patch
- also remove debug output to log.log and timing info to time_log.csv, as they are created not in the workingdir but toplevel dir and hinder parallelization

## fastbot

- monkeyq.jar requires framework.jar
  - the bundled one in the code corresponds probably to sdk32
  - it is not documented how to generate it
  - it was probably compiled from AOSP, except the manifest doesn't say it's packed by soong
  - the bundled manifest contains android.app.IWindowManager
  - the framework.jars from github don't
  - the pixel 8 running A14 requires a method freezeRotation(degrees, caller), but the bundled framework only works with freezeRotation(degrees), so a signature mismatch throws this up
  - some (chines) issues on github refer to an updated monkeyq.jar to be downloaded from baidu, but it requires an account
  - e.g. https://github.com/bytedance/Fastbot_Android/issues/281
  - we patch this as silent success?
  - yay, it works without screen rotation

- alt: make our own framework.jar with dex2jar
  - doesn't work because some interface methods were deprecated -> needs fixing but is fixable
  - https://cs.android.com/android/platform/superproject/+/master:frameworks/base/core/java/android/view/inputmethod/InputMethodManager.java;l=3464?q=switchToLastInputMethod
  - okay, generating our own framework.jar has a problem:
    - iwifimanager.class is missing
- still happening:
  - `[Fastbot]*** ERROR *** findMethod() error, NoSuchMethodException happened, there is no such method: setActivityController`
  - `[Fastbot]*** ERROR *** findMethod() error, NoSuchMethodException happened, there is no such method: getTasks`
  - first because ActivityManagerNative has been moved to ActivityManager
  - no idea about second tho
- ANDROID_SDK_ROOT and JAVA_HOME needs to be set properly
- tl;dr:
  - we get a run out of it, but we patch out the screen rotate
  - the activitycontroller seems to be part of monkeys own reporting, so we can skip this
  
