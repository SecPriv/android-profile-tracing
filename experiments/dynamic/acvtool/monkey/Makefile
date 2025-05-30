include ../../../Makefile.variable
include ../Makefile.variable

TOOL=monkey

override INPUTCSV=../../../analysis/dynamic/samples_to_dynamic_test_only_acvtool.csv

dummy:
	python3 acvtool/acvtool.py -h

monkey-01: JOBNAME=monkey-01
monkey-01: DURATION=600
monkey-01: DEVICEID=$(DEVICEID_P8_GENIUS)
monkey-01: --run-acvtool

stats-monkey-01: JOBNAME=monkey-01
stats-monkey-01: --stats-acvtool

monkey-02: JOBNAME=monkey-02
monkey-02: DURATION=600
monkey-02: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
monkey-02: --run-acvtool

stats-monkey-02: JOBNAME=monkey-02
stats-monkey-02: --stats-acvtool

monkey-03: JOBNAME=monkey-03
monkey-03: DURATION=600
monkey-03: DEVICEID=$(DEVICEID_P8_COOL)
monkey-03: --run-acvtool

stats-monkey-03: JOBNAME=monkey-03
stats-monkey-03: --stats-acvtool

monkey-04: JOBNAME=monkey-04
monkey-04: DURATION=600
monkey-04: DEVICEID=$(DEVICEID_P8_PIONEER)
monkey-04: --run-acvtool

stats-monkey-04: JOBNAME=monkey-04
stats-monkey-04: --stats-acvtool

