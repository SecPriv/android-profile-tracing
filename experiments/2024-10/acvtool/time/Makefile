include ../../Makefile.variable
include ../Makefile.variable

TOOL=time

dummy:
	python3 acvtool/acvtool.py -h

time-01: JOBNAME=time-01
time-01: DURATION=600
time-01: DEVICEID=$(DEVICEID_P8_GENIUS)
time-01: --run-acvtool

stats-time-01: JOBNAME=time-01
stats-time-01: --stats-generic

time-02: JOBNAME=time-02
time-02: DURATION=600
time-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
time-02: --run-acvtool

stats-time-02: JOBNAME=time-02
stats-time-02: --stats-generic

time-03: JOBNAME=time-03
time-03: DURATION=600
time-03: DEVICEID=$(DEVICEID_P8_COOL)
time-03: --run-acvtool

stats-time-03: JOBNAME=time-03
stats-time-03: --stats-generic

time-04: JOBNAME=time-04
time-04: DURATION=600
time-04: DEVICEID=$(DEVICEID_P8_PIONEER)
time-04: --run-acvtool

stats-time-04: JOBNAME=time-04
stats-time-04: --stats-generic

