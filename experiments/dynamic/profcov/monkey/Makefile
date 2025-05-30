include ../../../Makefile.variable

override INPUTCSV=../../../analysis/dynamic/samples_to_dynamic_test.csv 
override APKS_DMS_DIR=../../../raw_data/daily_collection/2025-05-07

TOOL=monkey

DEVICEID=$(DEVICEID_P8_COOL)

dummy:
	echo "hi"

monkey-test: JOBNAME=monkey-test
monkey-test: DURATION=10
monkey-test: --run-tool

stats-monkey-test: JOBNAME=monkey-test
stats-monkey-test: --stats-generic

monkey-test-all: JOBNAME=monkey-test-all
monkey-test-all: DURATION=10
monkey-test-all: INPUTCSV=../../../app_selection/downloaded_apps_2024-04-01.csv
monkey-test-all: --run-tool

stats-monkey-test-all: JOBNAME=monkey-test-all
stats-monkey-test-all: --stats-generic

### real runs

monkey-01: JOBNAME=monkey-01
monkey-01: DURATION=600
monkey-01: DEVICEID=$(DEVICEID_P8_GENIUS)
monkey-01: --run-tool

stats-monkey-01: JOBNAME=monkey-01
stats-monkey-01: --stats-generic

monkey-02: JOBNAME=monkey-02
monkey-02: DURATION=600
monkey-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
monkey-02: --run-tool

stats-monkey-02: JOBNAME=monkey-02
stats-monkey-02: --stats-generic

monkey-03: JOBNAME=monkey-03
monkey-03: DURATION=600
monkey-03: DEVICEID=$(DEVICEID_P8_COOL)
monkey-03: --run-tool

stats-monkey-03: JOBNAME=monkey-03
stats-monkey-03: --stats-generic

monkey-04: JOBNAME=monkey-04
monkey-04: DURATION=600
monkey-04: DEVICEID=$(DEVICEID_P8_PIONEER)
monkey-04: --run-tool

stats-monkey-04: JOBNAME=monkey-04
stats-monkey-04: --stats-generic

