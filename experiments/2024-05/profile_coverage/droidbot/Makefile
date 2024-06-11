METADIR=_parallel_meta

DEVICEID_P8_GENIUS=3A121FDJH00BT3
DEVICEID_P8_CAFFEINATED=38270DLJH004Q0
DEVICEID_P8_COOL=38091FDJH00PDT
DEVICEID_P8_PIONEER=39281FDJH006XT

APKS_DMS_DIR=../../../__data/2024-04-01


# defaults for run
INPUTCSV=../../../app_selection/apps_that_we_have_and_run_on_droidbot.csv
DURATION=600
DEVICEID=$(DEVICEID_P8_CAFFEINATED)
MAXPROBES=50000

dummy:
	echo "hi"

droidbot-test: JOBNAME=droidbot-test
droidbot-test: DURATION=5
droidbot-test: --run-time

droidbot-01: JOBNAME=droidbot-01
droidbot-01: --run-time

stats-droidbot-01: JOBNAME=droidbot-01
stats-droidbot-01: --stats-generic

droidbot-02: JOBNAME=droidbot-02
droidbot-02: --run-time

droidbot-03: JOBNAME=droidbot-03
droidbot-03: --run-time

droidbot-04: JOBNAME=droidbot-04
droidbot-04: --run-time

droidbot-05: JOBNAME=droidbot-05
droidbot-05: --run-time

# expects:
# - METADIR
# - JOBNAME
# - INPUTCSV
# - DEVICEID
# - MAXPROBES
# - DURATION
# - APKS_DMS_DIR
--run-time:
	mkdir -p $(METADIR)
	date | sed -e "s/^/Start: /" | tee -a $(METADIR)/$(JOBNAME).startend
	cat $(INPUTCSV) | parallel \
		-j1 \
		--joblog $(METADIR)/$(JOBNAME).joblog \
		--resume \
		--eta \
		--results $(METADIR)/$(JOBNAME).results/ \
		'aproftracer {} --verbose --device-id $(DEVICEID) --fresh-install $(APKS_DMS_DIR)/{} --max-probes $(MAXPROBES) --tool droidbot --tool-max-runtime $(DURATION) --result-dir results_$(JOBNAME) --also-startup-poststartup' || true 
	date | sed -e "s/^/End: /" | tee -a $(METADIR)/$(JOBNAME).startend


# expects:
# - JOBNAME
--stats-generic:
	@echo -n "result-dirs: "
	@ls results_$(JOBNAME)/ | wc -l
	@echo -n "+ trace_output.json: "
	@find results_$(JOBNAME)/ -name "trace_output.json" | wc -l
	@echo -n "- generic exceptions: "
	@grep -r "generic exception caught" $(METADIR)/$(JOBNAME).results/ | wc -l
	@echo -n "- timeout probes: "
	@grep -r "NotImplementedError: setting up tracer probes took more than" _parallel_meta/$(JOBNAME).results/ | wc -l
	@echo -n "- pids without pidmap: "
	@grep -r "has no associated pid_info" $(METADIR)/$(JOBNAME).results/ | wc -l


ids_in_joblog.csv:
	cat _parallel_meta/droidbot-01.joblog | cut -f 9 | cut -d ' ' -f 2 | tail -n +2	> ids_in_joblog.csv

clean-up-joblog: ids_in_joblog.csv
	for pth in _parallel_meta/droidbot-01.results/1/*; do ID=`echo $$pth | cut -d '/' -f 4`; if grep -wq "$$ID" ids_in_joblog.csv; then echo $$ID "in joblog"; else rm -r $$pth; fi; done
