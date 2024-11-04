include ../../Makefile.variable

TOOL=fastbot

DEVICEID=$(DEVICEID_P8_GENIUS)

dummy:
	echo "hi"

prepare-fastbot-files:
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/monkeyq.jar /sdcard/monkeyq.jar
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/fastbot-thirdpart.jar /sdcard/fastbot-thirdpart.jar
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/libs/* /data/local/tmp/
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/framework.jar /sdcard/framework.jar

fastbot-test: JOBNAME=fastbot-test
fastbot-test: DURATION=1
fastbot-test: prepare-fastbot-files --run-tool

stats-fastbot-test: JOBNAME=fastbot-test
stats-fastbot-test: --stats-generic

fastbot-test-all: JOBNAME=fastbot-test-all
fastbot-test-all: DURATION=10
fastbot-test-all: INPUTCSV=../../../app_selection/downloaded_apps_2024-04-01.csv
fastbot-test-all: prepare-fastbot-files --run-tool

stats-fastbot-test-all: JOBNAME=fastbot-test-all
stats-fastbot-test-all: --stats-generic

### real runs

fastbot-01: JOBNAME=fastbot-01
fastbot-01: DURATION=600
fastbot-01: DEVICEID=$(DEVICEID_P8_GENIUS)
fastbot-01: prepare-fastbot-files --run-tool

stats-fastbot-01: JOBNAME=fastbot-01
stats-fastbot-01: --stats-generic

fastbot-02: JOBNAME=fastbot-02
fastbot-02: DURATION=600
fastbot-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
fastbot-02: prepare-fastbot-files --run-tool

stats-fastbot-02: JOBNAME=fastbot-02
stats-fastbot-02: --stats-generic

fastbot-03: JOBNAME=fastbot-03
fastbot-03: DURATION=600
fastbot-03: DEVICEID=$(DEVICEID_P8_COOL)
fastbot-03: prepare-fastbot-files --run-tool

stats-fastbot-03: JOBNAME=fastbot-03
stats-fastbot-03: --stats-generic

fastbot-04: JOBNAME=fastbot-04
fastbot-04: DURATION=600
fastbot-04: DEVICEID=$(DEVICEID_P8_PIONEER)
fastbot-04: prepare-fastbot-files --run-tool

stats-fastbot-04: JOBNAME=fastbot-04
stats-fastbot-04: --stats-generic

