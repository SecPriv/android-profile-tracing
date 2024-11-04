include ../../Makefile.variable

TOOL=time

dummy:
	echo "hi"

time-test: JOBNAME=time-test
time-test: DURATION=10
time-test: --run-tool

stats-time-test: JOBNAME=time-test
stats-time-test: --stats-generic

time-test-all: JOBNAME=time-test-all
time-test-all: DURATION=10
time-test-all: INPUTCSV=../../../app_selection/downloaded_apps_2024-04-01.csv
time-test-all: --run-tool

stats-time-test-all: JOBNAME=time-test-all
stats-time-test-all: --stats-generic

### real runs

time-01: JOBNAME=time-01
time-01: DURATION=600
time-01: DEVICEID=$(DEVICEID_P8_GENIUS)
time-01: --run-tool

stats-time-01: JOBNAME=time-01
stats-time-01: --stats-generic

time-02: JOBNAME=time-02
time-02: DURATION=600
time-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
time-02: --run-tool

stats-time-02: JOBNAME=time-02
stats-time-02: --stats-generic

time-03: JOBNAME=time-03
time-03: DURATION=600
time-03: DEVICEID=$(DEVICEID_P8_COOL)
time-03: --run-tool

stats-time-03: JOBNAME=time-03
stats-time-03: --stats-generic

time-04: JOBNAME=time-04
time-04: DURATION=600
time-04: DEVICEID=$(DEVICEID_P8_PIONEER)
time-04: --run-tool

stats-time-04: JOBNAME=time-04
stats-time-04: --stats-generic

