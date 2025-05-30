include ../../../Makefile.variable
include ../Makefile.variable

TOOL=droidbot

override INPUTCSV=../../../analysis/dynamic/samples_to_dynamic_test_only_acvtool.csv

dummy:
	python3 acvtool/acvtool.py -h

droidbot-01: JOBNAME=droidbot-01
droidbot-01: DURATION=600
droidbot-01: DEVICEID=$(DEVICEID_P8_GENIUS)
droidbot-01: --run-acvtool

stats-droidbot-01: JOBNAME=droidbot-01
stats-droidbot-01: --stats-acvtool

droidbot-02: JOBNAME=droidbot-02
droidbot-02: DURATION=600
droidbot-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
droidbot-02: --run-acvtool

stats-droidbot-02: JOBNAME=droidbot-02
stats-droidbot-02: --stats-acvtool

droidbot-03: JOBNAME=droidbot-03
droidbot-03: DURATION=600
droidbot-03: DEVICEID=$(DEVICEID_P8_COOL)
droidbot-03: --run-acvtool

stats-droidbot-03: JOBNAME=droidbot-03
stats-droidbot-03: --stats-acvtool

droidbot-04: JOBNAME=droidbot-04
droidbot-04: DURATION=600
droidbot-04: DEVICEID=$(DEVICEID_P8_PIONEER)
droidbot-04: --run-acvtool

stats-droidbot-04: JOBNAME=droidbot-04
stats-droidbot-04: --stats-acvtool

