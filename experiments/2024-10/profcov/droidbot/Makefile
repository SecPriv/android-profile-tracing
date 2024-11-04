include ../../Makefile.variable

TOOL=droidbot

dummy:
	echo "hi"

droidbot-test: JOBNAME=droidbot-test
droidbot-test: DURATION=10
droidbot-test: --run-tool

stats-droidbot-test: JOBNAME=droidbot-test
stats-droidbot-test: --stats-generic

droidbot-test-all: JOBNAME=droidbot-test-all
droidbot-test-all: DURATION=10
droidbot-test-all: INPUTCSV=../../../app_selection/downloaded_apps_2024-04-01.csv
droidbot-test-all: --run-tool

stats-droidbot-test-all: JOBNAME=droidbot-test-all
stats-droidbot-test-all: --stats-generic

### real runs

droidbot-01: JOBNAME=droidbot-01
droidbot-01: DURATION=600
droidbot-01: DEVICEID=$(DEVICEID_P8_GENIUS)
droidbot-01: --run-tool

stats-droidbot-01: JOBNAME=droidbot-01
stats-droidbot-01: --stats-generic

droidbot-02: JOBNAME=droidbot-02
droidbot-02: DURATION=600
droidbot-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
droidbot-02: --run-tool

stats-droidbot-02: JOBNAME=droidbot-02
stats-droidbot-02: --stats-generic

droidbot-03: JOBNAME=droidbot-03
droidbot-03: DURATION=600
droidbot-03: DEVICEID=$(DEVICEID_P8_COOL)
droidbot-03: --run-tool

stats-droidbot-03: JOBNAME=droidbot-03
stats-droidbot-03: --stats-generic

droidbot-04: JOBNAME=droidbot-04
droidbot-04: DURATION=600
droidbot-04: DEVICEID=$(DEVICEID_P8_PIONEER)
droidbot-04: --run-tool

stats-droidbot-04: JOBNAME=droidbot-04
stats-droidbot-04: --stats-generic
