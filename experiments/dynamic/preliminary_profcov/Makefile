override APKS_DMS_DIR=../../raw_data/daily_collection/2025-05-07

include ../../Makefile.variable

TOOL=time

dummy:
	echo "hi"

input.csv:
	find ../../raw_data/daily_collection/2025-05-07/ -iname "*.apk" | choose -f / 5 | sort | uniq > input.csv

time-test: 
time-test: DEVICEID=$(DEVICEID_P8_GENIUS)
time-test: JOBNAME=time-test
time-test: DURATION=10
time-test: INPUTCSV=input.csv
time-test: --run-tool

stats-time-test: JOBNAME=time-test
stats-time-test: --stats-generic
	@echo "apps that threw a generic error:"
	@grep -P '\t131\t'  _parallel_meta/$(JOBNAME).joblog | choose 19 | sort | sed 's/^/ - /'

droidbot-test: 
droidbot-test: DEVICEID=$(DEVICEID_P8_COOL)
droidbot-test: JOBNAME=droidbot-test
droidbot-test: DURATION=10
droidbot-test: INPUTCSV=input.csv
droidbot-test: --run-tool

stats-droidbot-test: JOBNAME=droidbot-test
stats-droidbot-test: --stats-generic
	@echo "apps that threw a generic error:"
	@grep -P '\t131\t'  _parallel_meta/$(JOBNAME).joblog | choose 19 | sort | sed 's/^/ - /'

fastbot-test: 
fastbot-test: DEVICEID=$(DEVICEID_P8_CAFFEINATED)
fastbot-test: JOBNAME=fastbot-test
fastbot-test: DURATION=10
fastbot-test: INPUTCSV=input.csv
fastbot-test: --run-tool

stats-fastbot-test: JOBNAME=fastbot-test
stats-fastbot-test: --stats-generic
	@echo "apps that threw a generic error:"
	@grep -P '\t131\t'  _parallel_meta/$(JOBNAME).joblog | choose 19 | sort | sed 's/^/ - /'

create-lists-of-successfull-apps:
	find results_time-test/ -iname "result.pickle" | choose -f '/' 1 | sort > list_apps_working_tracer_time
	find results_droidbot-test/ -iname "result.pickle" | choose -f '/' 1 | sort > list_apps_working_tracer_droidbot
	find results_fastbot-test/ -iname "result.pickle" | choose -f '/' 1 | sort > list_apps_working_tracer_fastbot

