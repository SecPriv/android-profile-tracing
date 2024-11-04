include ../../Makefile.variable
include ../Makefile.variable

TOOL=fastbot

dummy:
	python3 acvtool/acvtool.py -h

prepare-fastbot-files:
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/monkeyq.jar /sdcard/monkeyq.jar
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/fastbot-thirdpart.jar /sdcard/fastbot-thirdpart.jar
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/libs/* /data/local/tmp/
	adb -s $(DEVICEID) push ../../../../dependencies/fastbot_cache/framework.jar /sdcard/framework.jar

fastbot-01: JOBNAME=fastbot-01
fastbot-01: DURATION=600
fastbot-01: prepare-fastbot-files --run-acvtool



fastbot-01: JOBNAME=fastbot-01
fastbot-01: DURATION=600
fastbot-01: DEVICEID=$(DEVICEID_P8_GENIUS)
fastbot-01: prepare-fastbot-files --run-acvtool

stats-fastbot-01: JOBNAME=fastbot-01
stats-fastbot-01: --stats-acvtool

fastbot-02: JOBNAME=fastbot-02
fastbot-02: DURATION=600
fastbot-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
fastbot-02: prepare-fastbot-files --run-acvtool

stats-fastbot-02: JOBNAME=fastbot-02
stats-fastbot-02: --stats-acvtool

fastbot-03: JOBNAME=fastbot-03
fastbot-03: DURATION=600
fastbot-03: DEVICEID=$(DEVICEID_P8_COOL)
fastbot-03: prepare-fastbot-files --run-acvtool

stats-fastbot-03: JOBNAME=fastbot-03
stats-fastbot-03: --stats-acvtool

fastbot-04: JOBNAME=fastbot-04
fastbot-04: DURATION=600
fastbot-04: DEVICEID=$(DEVICEID_P8_PIONEER)
fastbot-04: prepare-fastbot-files --run-acvtool

stats-fastbot-04: JOBNAME=fastbot-04
stats-fastbot-04: --stats-acvtool

