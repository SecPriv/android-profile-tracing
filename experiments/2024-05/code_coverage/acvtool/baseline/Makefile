METADIR=_parallel_meta
# defaults for run

DEVICE_ID_CAFFEINATED=38270DLJH004Q0

DEVICE_ID=$(DEVICE_ID_CAFFEINATED)

INPUTCSV=../apps-that-dont-crash.csv

help:
	python3 acvtool/acvtool.py -h


run-baseline-01:JOBNAME=run-baseline-01
run-baseline-01:TIME=600
run-baseline-01:--run


# expects:
# - METADIR
# - JOBNAME
# - INPUTCSV
# - DEVICE_ID
# - TIME
--run:
	mkdir -p $(METADIR)
	date | sed -e "s/^/Start: /" | tee -a $(METADIR)/$(JOBNAME).startend
	cat $(INPUTCSV) | parallel \
		-j1 \
		--joblog $(METADIR)/$(JOBNAME).joblog \
		--resume \
		--eta \
		--results $(METADIR)/$(JOBNAME).results/ \
		'./runacvtool-baseline.sh $(TIME) {} 2>&1' || true
	date | sed -e "s/^/End: /" | tee -a $(METADIR)/$(JOBNAME).startend


noncrashing-results.csv:
	while read -r f; do echo $$f `grep -A1 "Total" ./wd/$$f/report/main_index.html | grep -oP '\d+ of \d+' | choose 0 2`; done < ../apps-that-dont-crash.csv > noncrashing-results.csv 
