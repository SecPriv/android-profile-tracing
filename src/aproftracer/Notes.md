# Notes

## AOT compilation for install from files

original playstore cli invocation found through `adb logcat | grep dex2oat`:

```txt

03-26 14:35:07.055  1425  1756 I PackageManager: Integrity check passed for file:///data/app/vmdl11548363.tmp
03-26 14:35:07.056 22293 22293 I Finsky  : [2] ajzw.c(68): VerifyApps: Install-time verification requested for package app.organicmaps, id = 26
03-26 14:35:07.057  8748  8766 I Finsky:quick_launch: [49] ncb.run(349): Stats for Executor: bgExecutor ped@97b3d04[Running, pool size = 4, active threads = 0, queued tasks = 0, completed tasks = 23]
03-26 14:35:07.057  8748  8766 I Finsky:quick_launch: [49] ncb.run(349): Stats for Executor: LightweightExecutor ped@b2862ed[Running, pool size = 4, active threads = 0, queued tasks = 0, completed tasks = 20]
03-26 14:35:07.061  8748  8766 I Finsky:quick_launch: [49] ncb.run(349): Stats for Executor: BlockingExecutor ped@ea48522[Running, pool size = 0, active threads = 0, queued tasks = 0, completed tasks = 1]
03-26 14:35:07.065 22293 25049 I Finsky  : [395] VerifyAppsInstallTask.aky(52): VerifyApps: Anti-malware verification task started for package=app.organicmaps
03-26 14:35:07.065 22293 25049 I Finsky  : [395] VerifyAppsInstallTask.aky(139): VerifyApps: Skipping verification because own installation
03-26 14:35:07.065 22293 25049 I Finsky  : [395] VerifyAppsInstallTask.aky(691): VerifyApps: Skipping anti malware verification (preconditions not met). package=app.organicmaps
03-26 14:35:07.069 22293 25049 I Finsky  : [395] VerifyPerSourceInstallationConsentInstallTask.aky(222): PSIC verification started with installer uid: 10133 package name: com.android.vending, originating uid: -1
03-26 14:35:07.076 22293 25049 I Finsky  : [395] VerifyPerSourceInstallationConsentInstallTask.aky(442): Skipping logging for attempted installation. This is a Play Store installation.
03-26 14:35:07.077 22293 22293 I Finsky  : [2] VerifyInstallTask.j(17): VerifyApps: Returning package verification result id=26, result=ALLOW
03-26 14:35:07.078 22293 25133 E AbstractLogEventBuilder: The provided ProductIdOrigin 3 is not one of the process-level expected values: 1 or 2
03-26 14:35:07.079  1425  1756 I PackageManager: Continuing with installation of file:///data/app/vmdl11548363.tmp
03-26 14:35:07.079 22293 22293 I Finsky  : [2] VerifyInstallTask.akx(71): VerifyApps: Verification complete: id=26, package_name=app.organicmaps
03-26 14:35:07.098  1425  2343 V SafetySourceDataValidat: Package: com.android.vending has expected signature
03-26 14:35:07.098  1425  2343 V SafetySourceDataValidat: Package: com.android.vending has expected signature
03-26 14:35:07.102  1425  1756 W libc    : Access denied finding property "pm.dexopt.dm.require_manifest"
03-26 14:35:07.139  1425  1756 I PermissionManager: Permission ownership changed. Updating all permissions.

03-26 14:35:07.250 24915 24923 I artd    : Running profman: 
    /apex/com.android.art/bin/art_exec 
        --drop-capabilities 
        --keep-fds=6:7:8 -- 
            /apex/com.android.art/bin/profman 
                --copy-and-update-profile-key
                --profile-file-fd=6 
                --apk-fd=7 
                --reference-profile-file-fd=8
03-26 14:35:07.250 24915 24923 I artd    : Opened FDs: 
    6:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.dm 
    7:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
    8:/data/misc/profiles/ref/app.organicmaps/primary.prof.rKjG5f.tmp 
03-26 14:35:07.270 24915 24923 I artd    : profman returned code 0
03-26 14:35:07.271 24915 24923 I artd    : Merge skipped because there are no existing profiles
03-26 14:35:07.335  1425  1688 E AppOps  : Trying to set mode for unknown uid 10281.
03-26 14:35:07.339 24915 24923 I artd    : Running dex2oat: /apex/com.android.art/bin/art_exec --drop-capabilities --set-task-profile=Dex2OatBootComplete --set-priority=background --keep-fds=6:7:8:9:10:11:12 -- /apex/com.android.art/bin/dex2oat64 --zip-fd=6 --zip-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk --oat-fd=7 --oat-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex --output-vdex-fd=8 --app-image-fd=9 --image-format=lz4 --swap-fd=10 --class-loader-context=PCL[] --classpath-dir=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A== --dm-fd=11 --profile-file-fd=12 --instruction-set=arm64 --instruction-set-features=default --instruction-set-variant=cortex-a55 --compiler-filter=speed-profile --compilation-reason=install-dm --compact-dex-level=none --max-image-block-size=524288 --resolve-startup-const-strings=true --generate-mini-debug-info --runtime-arg -Xtarget-sdk-version:34 --runtime-arg -Xhidden-api-policy:enabled --runtime-arg -Xms64m --runtime-arg -Xmx512m --comments=app-version-name:2024.03.18-5-Google,app-version-code:24031805,art-version:341411300
03-26 14:35:07.339 24915 24923 I artd    : Opened FDs: 
    6:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
    7:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex.3c9wr3.tmp 
    8:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.vdex.pFQfsf.tmp 
    9:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.art.ApGfZD.tmp 
    10:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex.swap.ZhCOrp.tmp 
    11:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.dm 
    12:/data/misc/profiles/ref/app.organicmaps/primary.prof.rKjG5f.tmp 
03-26 14:35:07.375 25169 25169 W dex2oat64: Mismatch between dex2oat instruction set features to use (ISA: Arm64 Feature string: -a53,crc,lse,fp16,dotprod,-sve) and those from CPP defines (ISA: Arm64 Feature string: -a53,-crc,-lse,-fp16,-dotprod,-sve) for the command line:
03-26 14:35:07.375 25169 25169 W dex2oat64: /apex/com.android.art/bin/dex2oat64 
    --zip-fd=6 
    --zip-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
    --oat-fd=7 
    --oat-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex 
    --output-vdex-fd=8 
    --app-image-fd=9 
    --image-format=lz4 
    --swap-fd=10 
    --class-loader-context=PCL[] 
    --classpath-dir=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A== 
    --dm-fd=11 
    --profile-file-fd=12 
    --instruction-set=arm64 
    --instruction-set-features=default 
    --instruction-set-variant=cortex-a55 
    --compiler-filter=speed-profile 
    --compilation-reason=install-dm 
    --compact-dex-level=none 
    --max-image-block-size=524288 
    --resolve-startup-const-strings=true 
    --generate-mini-debug-info 
    --runtime-arg -Xtarget-sdk-version:34 
    --runtime-arg -Xhidden-api-policy:enabled 
    --runtime-arg -Xms64m 
    --runtime-arg -Xmx512m 
    --comments=app-version-name:2024.03.18-5-Google,app-version-code:24031805,art-version:341411300

03-26 14:35:07.380 25169 25169 I dex2oat64: Using CollectorTypeCMC GC.
03-26 14:35:07.746 25169 25169 I dex2oat64: Explicit concurrent mark compact GC freed 15354(4675KB) AllocSpace objects, 0(0B) LOS objects, 63% free, 891KB/2427KB, paused 8us,72us total 6.499ms
03-26 14:35:07.837 25169 25169 I dex2oat64: dex2oat took 464.258ms (1.297s cpu) (threads: 8) arena alloc=6616KB (6774912B) java alloc=891KB (912720B) native alloc=7625KB (7808976B) free=4077KB (4175440B)
03-26 14:35:07.848 24915 24923 I artd    : dex2oat returned code 0
03-26 14:35:07.849  1425  1756 I ArtService: Dexopt result: [packageName = app.organicmaps] DexContainerFileDexoptResult{dexContainerFile=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk, primaryAbi=true, abi=arm64-v8a, actualCompilerFilter=speed-profile, status=PERFORMED, dex2oatWallTimeMillis=515, dex2oatCpuTimeMillis=1320, sizeBytes=3272908, sizeBeforeBytes=0, extendedStatusFlags=[]}
03-26 14:35:07.851  1425  1756 V BackupManagerService: [UserID:0] restore ...
```

seems like playstore is installing the app and invoking profman with fds to merge reference and cloud, then runs dex2oat

- [profman help](https://cs.android.com/android/platform/superproject/main/+/main:art/profman/profman.cc;l=107)
- [dex2oat help](https://cs.android.com/android/platform/superproject/main/+/main:art/dex2oat/dex2oat_options.cc;l=57)

```sh
/apex/com.android.art/bin/dex2oat64 
    # skip zips cause we use --dex-file= instead
    --zip-fd=6 
    --zip-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
    # use --oat-file= instead
    --oat-fd=7 
    --oat-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex 
    # TODO is this needed?
    --output-vdex-fd=8 
    # "Specify a file name for app image. Only used if a profile is passed in."
    # is pointing to a tmp base.art image. woner if we can get around doing a tmp file
    --app-image-fd=9 
    # defaults to uncompressed, we can skup
    --image-format=lz4 
    # skip 
    --swap-fd=10 
    # "a string specifying the intended runtime loading context for the compiled dex files."
    # keep, but I wonder if it ever changes?
    #const std::string valid_context = "PCL[" + dex_files[0]->GetLocation() + "]"; from https://cs.android.com/android/platform/superproject/main/+/main:art/dex2oat/dex2oat_test.cc;drc=00ffa77a08213fcb114f7625b7e0615b3c920abf;l=2231?q=class-loader-context
    # I suppose we can leave it empty
    --class-loader-context=PCL[] 
    # same as app dir
    --classpath-dir=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A== 
    # use --dm-file= instead
    --dm-fd=11 
    # points to /data/misc/profiles/ref/app.organicmaps/primary.prof.rKjG5f.tmp 
    # "Specify profiler output file to use for compilation using a filename."
    # we can skip it
    --profile-file-fd=12 
    # keep all of these 
    --instruction-set=arm64 
    --instruction-set-features=default 
    --instruction-set-variant=cortex-a55 # maybe skip this?
    --compiler-filter=speed-profile 
    --compilation-reason=install-dm 
    # skip "This flag is obsolete and does nothing."
    --compact-dex-level=none 
    # keep
    --max-image-block-size=524288 
    # keep the rest
    --resolve-startup-const-strings=true 
    --generate-mini-debug-info 
    --runtime-arg -Xtarget-sdk-version:34 
    --runtime-arg -Xhidden-api-policy:enabled 
    --runtime-arg -Xms64m 
    --runtime-arg -Xmx512m 
    # except this
    --comments=app-version-name:2024.03.18-5-Google,app-version-code:24031805,art-version:341411300
```

## where does the dm come from?

requested together with apks (line 2):

```log
03-26 14:34:45.261 22293 22443 I Finsky  : [117] aavq.p(25): RM: create resource request id 13f77aa9-3a9b-464f-90c6-234c8eef45f6 for request app.organicmaps.apk reason: single_install isid: ME-z3UZoSumDKzUhuXngUA
03-26 14:34:45.262 22293 22400 I Finsky  : [113] aavq.p(25): RM: create resource request id 0272a5a7-07b2-436a-b780-888ef02448db for request app.organicmaps.dm reason: single_install isid: ME-z3UZoSumDKzUhuXngUA
03-26 14:34:45.263 22293 22370 I Finsky  : [103] aavq.p(25): RM: create resource request id 3a59d598-23c6-4025-b706-6632e0b61295 for request config.xxhdpi reason: single_install isid: ME-z3UZoSumDKzUhuXngUA
03-26 14:34:45.264 22293 22377 I Finsky  : [108] aavq.p(25): RM: create resource request id 66e620f4-5e49-45b8-91df-5c59a4c9c6ff for request config.en reason: single_install isid: ME-z3UZoSumDKzUhuXngUA
03-26 14:34:45.265 22293 22400 I Finsky  : [113] aavq.p(25): RM: create resource request id 12857b49-b4d1-4bb2-a116-b77776927125 for request config.arm64_v8a reason: single_install isid: ME-z3UZoSumDKzUhuXngUA
```

## difference between playstore install and file install?

- playstore uses:
  - `--app-image-fd=9`
  - `--image-format=lz4`
  - `--dm-fd=11`
  - `--profile-file-fd=12`
  - odex is about 2.5M after install

- file install does not use the above
  - it also uses `--compilation-reason=install` instead of `install-dm`
  - and `--compiler-filter=verify` instead of `--compiler-filter=speed-profile`
  - odex is only 61k after install

sample from file-based install:

```txt
artd    : Running dex2oat: 
/apex/com.android.art/bin/art_exec 
    --drop-capabilities 
    --set-task-profile=Dex2OatBootComplete 
    --set-priority=background 
    --keep-fds=6:7:8:9 --
    /apex/com.android.art/bin/dex2oat64 
        --zip-fd=6 
        --zip-location=/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/base.apk 
        --oat-fd=7 
        --oat-location=/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/oat/arm64/base.odex 
        --output-vdex-fd=8 
        --swap-fd=9 
        --class-loader-context=PCL[] 
        --classpath-dir=/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw== 
        --instruction-set=arm64 
        --instruction-set-features=default 
        --instruction-set-variant=cortex-a55 
    !   --compiler-filter=verify 
    !   --compilation-reason=install 
        --compact-dex-level=none 
        --max-image-block-size=524288 
        --resolve-startup-const-strings=true 
        --generate-mini-debug-info 
        --runtime-arg -Xtarget-sdk-version:34 
        --runtime-arg -Xhidden-api-policy:enabled 
        --runtime-arg -Xms64m 
        --runtime-arg -Xmx512m 
        --comments=app-version-name:2024.03.18-5-Google,app-version-code:24031805,art-version:341411300

03-26 16:17:21.326 26582 26582 I artd    : Opened FDs: 
    6:/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/base.apk 
    7:/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/oat/arm64/base.odex.2iG6SH.tmp 
    8:/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/oat/arm64/base.vdex.Zsv7uV.tmp 
    9:/data/app/~~EoqEBx4OGOTMYQ2iRNWqgg==/app.organicmaps-06acZuMWjUtbM2fEWn6Jcw==/oat/arm64/base.odex.swap.r6NCUQ.tmp 
```

sample from playstore install:

```txt
artd    : Running dex2oat: 
/apex/com.android.art/bin/art_exec 
    --drop-capabilities 
    --set-task-profile=Dex2OatBootComplete 
    --set-priority=background 
    --keep-fds=6:7:8:9:10:11:12 -- 
    /apex/com.android.art/bin/dex2oat64 
        --zip-fd=6 
        --zip-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
        --oat-fd=7 
        --oat-location=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex 
        --output-vdex-fd=8 
    +   --app-image-fd=9 
    +   --image-format=lz4 
        --swap-fd=10 
        --class-loader-context=PCL[] 
        --classpath-dir=/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A== 
    +   --dm-fd=11 
    +   --profile-file-fd=12 
        --instruction-set=arm64 
        --instruction-set-features=default 
        --instruction-set-variant=cortex-a55 
    !   --compiler-filter=speed-profile 
    !   --compilation-reason=install-dm 
        --compact-dex-level=none 
        --max-image-block-size=524288 
        --resolve-startup-const-strings=true 
        --generate-mini-debug-info 
        --runtime-arg -Xtarget-sdk-version:34 
        --runtime-arg -Xhidden-api-policy:enabled 
        --runtime-arg -Xms64m 
        --runtime-arg -Xmx512m 
        --comments=app-version-name:2024.03.18-5-Google,app-version-code:24031805,art-version:341411300

03-26 14:35:07.339 24915 24923 I artd    : Opened FDs: 
    6:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.apk 
    7:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex.3c9wr3.tmp 
    8:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.vdex.pFQfsf.tmp 
    9:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.art.ApGfZD.tmp 
    10:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/oat/arm64/base.odex.swap.ZhCOrp.tmp 
    11:/data/app/~~TURb1z6w_GoqnAE5VSzA2Q==/app.organicmaps-YpSYit7tdPXb7PoCnuHK9A==/base.dm 
    12:/data/misc/profiles/ref/app.organicmaps/primary.prof.rKjG5f.tmp 
```

## how does play pas the dm info?

- search for argument: [https://cs.android.com/search?q=%22--dm-fd%22&sq=]
  - used in `run_dex2oat.cc` [https://cs.android.com/android/platform/superproject/main/+/main:frameworks/native/cmds/installd/run_dex2oat.cpp;l=128;drc=9a7062382c16a10abdd406312ddbf7788d5d99bf;bpv=1;bpt=1?q=%22--dm-fd%22]
    - used in `Initialize`: [https://cs.android.com/android/platform/superproject/main/+/main:frameworks/native/cmds/installd/run_dex2oat.cpp;l=65;drc=9a7062382c16a10abdd406312ddbf7788d5d99bf;bpv=1;bpt=1?q=%22--dm-fd%22]
      - used in dexopt.cpp [https://cs.android.com/android/platform/superproject/main/+/main:frameworks/native/cmds/installd/dexopt.cpp;l=1787;drc=9a7062382c16a10abdd406312ddbf7788d5d99bf]
  - and `artd.cc` (as is invoked by pm install as visible in the full logs): [https://cs.android.com/android/platform/superproject/main/+/main:art/artd/artd.cc?q=%22--dm-fd%22]
    - passed through `dexopt` method: [https://cs.android.com/android/platform/superproject/main/+/main:art/artd/artd.cc;drc=9a7062382c16a10abdd406312ddbf7788d5d99bf;l=930?q=%22--dm-fd%22]

so we don't want to run dex2oat ourselves but trigger dexopt?

- `pm compile` to the rescue?

```txt
compile [-r COMPILATION_REASON] [-m COMPILER_FILTER] [-p PRIORITY] [-f]
      [--primary-dex] [--secondary-dex] [--include-dependencies] [--full]
      [--split SPLIT_NAME] [--reset] [-a | PACKAGE_NAME]
    Dexopt a package or all packages.
    Options:
      -a Dexopt all packages
      -r Set the compiler filter and the priority based on the given
         compilation reason.
         Available options: 'first-boot', 'boot-after-ota',
         'boot-after-mainline-update', 'install', 'bg-dexopt', 'cmdline'.
      -m Set the target compiler filter. The filter actually used may be
         different, e.g. 'speed-profile' without profiles present may result in
         'verify' being used instead. If not specified, this defaults to the
         value given by -r, or the system property 'pm.dexopt.cmdline'.
         Available options (in descending order): 'speed', 'speed-profile',
         'verify'.
      -p Set the priority of the operation, which determines the resource usage
         and the process priority. If not specified, this defaults to
         the value given by -r, or 'PRIORITY_INTERACTIVE'.
         Available options (in descending order): 'PRIORITY_BOOT',
         'PRIORITY_INTERACTIVE_FAST', 'PRIORITY_INTERACTIVE',
         'PRIORITY_BACKGROUND'.
      -f Force dexopt, also when the compiler filter being applied is not
         better than that of the current dexopt artifacts for a package.
      --reset Reset the dexopt state of the package as if the package is newly
         installed.
         More specifically, it clears reference profiles, current profiles, and
         any code compiled from those local profiles. If there is an external
         profile (e.g., a cloud profile), the code compiled from that profile
         will be kept.
         For secondary dex files, it also clears all dexopt artifacts.
         When this flag is set, all the other flags are ignored.
      -v Verbose mode. This mode prints detailed results.
      --force-merge-profile Force merge profiles even if the difference between
         before and after the merge is not significant.
    Scope options:
      --primary-dex Dexopt primary dex files only (all APKs that are installed
        as part of the package, including the base APK and all other split
        APKs).
      --secondary-dex Dexopt secondary dex files only (APKs/JARs that the app
        puts in its own data directory at runtime and loads with custom
        classloaders).
      --include-dependencies Include dependency packages (dependencies that are
        declared by the app with <uses-library> tags and transitive
        dependencies). This option can only be used together with
        '--primary-dex' or '--secondary-dex'.
      --full Dexopt all above. (Recommended)
      --split SPLIT_NAME Only dexopt the given split. If SPLIT_NAME is an empty
        string, only dexopt the base APK.
        Tip: To pass an empty string, use a pair of quotes ("").
        When this option is set, '--primary-dex', '--secondary-dex',
        '--include-dependencies', '--full', and '-a' must not be set.
      Note: If none of the scope options above are set, the scope defaults to
      '--primary-dex --include-dependencies'.
```

**IDEA**:
    - put dm in place, run dexopt. hope for the best.

**OUTCOME**:
    - `pm compile -r install -m speed-profile -f --reset -v app.organicmaps`
        - 727k odex
    - `pm compile -r install -m speed-profile -f --reset -v --full app.organicmaps`
        - 727k odex
    - `pm compile -r install -m everything -f --reset -v --full app.organicmaps`
        - 727k odex
    - all too small `:(`

**QUESTION**: why is playstore installed odex bigger? how do we compile the bigger odex? are the cloud profile methods in there?
    - because we use the dm file we have with a setup from the play store?
        - no, clean install from files but same result 727k methods
    - because we are wrong in how big the playstore odex should be?
        - no, fresh install is def way bigger
    - is `pm compile` producing the smaller odex also when run on the app installed through playstore?
        - no, running the same command will create a file with a new timestamp that matches
        - what if we remove the odex?
            - then it will be re-created
    - are we comparing the wrog things because our apk + dm just create a smaller footprint?
        - copy out current path contents and install those from file
        - **FUCK YEAH THIS WAS IT**
            - future research: how can the playstore installthe apk and dm at the same time?
    - there are some different files: `base.digests` and `app.metadata`
        - what do they do? no idea

## not working on pixel6a heron / identify offsets

1. why is tracer not working on phone?

2. how to get cookies?
    - cookies are not implemented in aya
    - [on discord someone says](https://discord.com/channels/855676609003651072/855676609003651075/989982416250736720):
        - use /proc/id/maps to calculate offset
            - but on heron there is no odex in this list
            - this explains why no tracing happens
        - alternatively use N programs, lol

so why is odex not mapped?
    - permissions (no)
        - dm is different, should be system:system
            - fixed but still no cigar
    - oat file borked?
        - yes! `oatdump --headers-only --oat-file=base.odex` shows:
        - `Failed to open oat file from 'base.odex': Invalid oat header for 'base.odex': Invalid oat magic, expected 0x6f61740a, got 0xa00020d4.`

we can either:
    - rewrite in not-aya to support cookies
        - challenge: time
        - challenge: cross-compilation
    - hack around it with process mapping
        - challenge: when to get process map, app should ideally be started by tool
            - but then again, whatever.
            - then again agina, we can listen for process id in logs and grab it if we see a process id that we didn't look at yet.

hypothesis: at some point compilation on pixel6a diverges
    - rerun clean
    - go through steps and check oat file

big learn:
    - i had a very old tracer binary on the phone. it did take other arguments and my wrapper didn't push a recompiled version
    - the arguments were different and it might have tried to open the odex as csv, maybe somehow mangling it.
    - anyway, it breaks now in more interesting ways, probably because bpf cookie is not supported

okay, so:
    1. when installing on the pixel6a with `pm install` and then `pm compile`, the odex does not show up in the `/proc/<id>/maps`
    2. when installing through the playstore, it does show up
    3. when installing on the emulator through `pm`, it does show up as well
    4. permissions are the same of the files for `pm` and playstore install

- differences that appear are:
  - no app.metadata for pm install
    - contains:
            ```xml
            <bundle>
            <long name="version" value="1" />
            <pbundle_as_map name="safety_labels">
            <pbundle_as_map name="data_labels">
            <pbundle_as_map name="data_collected" />
            <pbundle_as_map name="data_shared" />
            </pbundle_as_map>
            <long name="version" value="1" />
            <pbundle_as_map name="security_labels">
            <boolean name="is_data_deletable" value="false" />
            <boolean name="is_data_encrypted" value="true" />
            </pbundle_as_map>
            </pbundle_as_map>
            </bundle>
            ```
  - no base.digests
    - binary content
  - basedm o+r: fixed, not the issue

- omg, it's the tracer.
  - when it is running, no matter how the app is started it does not load the odex
  - well fuck.

- the offset look weird: there's multipl 4096 for the latest app.organicmaps, this is when there is no code
- first, make these methods static for debugging
- then remove all 0x00 offsets fromt he csv used for tracing
- and then it workssss! \o/

nest steps:
1. re-calculate offsets from log via /proc
2. collect results to file
3. implement cleanup
4. ????