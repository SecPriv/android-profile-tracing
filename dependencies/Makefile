SHELL := /bin/bash

submodule-update-init:
	git submodule update --init
	@echo "don't forget to set up android-sdk (cmdline tools)"

acvtool-00-apply-diff:
	cd acvtool && git apply ../acvtool.patch

acvtool-01-prepare:
	sudo apt install protobuf-compiler # if this is skipped pyaxml throuws cryptic errors, for arch use sudo pacman -S protobuf
	cd acvtool && pyenv virtualenv 3.11.5 acvtool-dev && pyenv local acvtool
	cd acvtool && pip install -e . # TODO cd enough or pyenv shell?
	echo "don't forget to adjust ~/acvtool/config.json to point to android build tools. we use 'build-tools;34.0.0' from sdkmanager"

droidbot-00-apply-diff:
	cd droidbot && git apply ../droidbot.patch

droidbot-01-install:
	cd droidbot && pip install -e .

fastbot-00-setup-gradle:
	@echo "assuming sdkman is installed according to fastbot readme"
	@echo ""
	cd fastbot && bash -i -c "sdk install gradle 7.6.2" 
	@echo "next step assumes you have ANDROID_SDK_ROOT set properly and 'cmake;3.18.1' and 'ndk;25.2.9519653' installed using sdkmanager"
	cd fastbot && gradle wrapper # in new shell so it's taking the newly installed gradle

fastbot-01-apply-diff:
	cd fastbot && git apply ../fastbot.patch
	# the fastbot patch currently only removes the rotation for android 14
	# TODO add android 14 framework.jar and fix other interface issues

fastbot-02-build-cached:
	@echo "FIXME: set to correct location: ANDROID_SDK_ROOT, NDK_ROOT to 25.2.9529653, and cmake resolving"
	@echo ""
	export ANDROID_SDK_ROOT=~/android/sdk/; cd fastbot && ./gradlew clean makeJar && cd ..
	# fastbots build_native.sh assumes NDK_HOME set, but it's actually ANDROID_NDK_HOME
	# it also requires a specific version, so we hardcode it here
	# CHANGEME set to correct location
	export NDK_ROOT=~/android/sdk/ndk/25.2.9519653/; echo "set NDK_ROOT to $${NDK_ROOT}" && cd fastbot && sh build_native.sh
	# instructions say build-tools 28.0.3, but we try first with latest
	# also instructions use dx, which is deprecated since 2021 and not included in modern build-tools
	# we use d8 instead
	# # throws some warnings but compiles :shrug:
	cd fastbot && ~/android/sdk/build-tools/34.0.0/d8 --output monkeyq.jar monkey/build/libs/monkey.jar && cd ..
	# monkeyq.jar is not in library as described in `usage` section, so I assume it's in the root dir
	cp fastbot/monkeyq.jar fastbot_cache/
	cp fastbot/fastbot-thirdpart.jar fastbot_cache/
	cp -r fastbot/libs/ fastbot_cache/
	cp fastbot/framework.jar fastbot_cache/




