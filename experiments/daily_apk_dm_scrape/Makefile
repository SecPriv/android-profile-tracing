
.PHONY: full-daily-run
full-daily-run:
	./harvest.py --serial 34251JEGR03854 --serial 34251JEGR04718 --verbose ../top400apps.txt

.PHONY: stats-on-logs
stats-on-logs:
	@for logdir in logs/*; do \
		datestr="$${logdir##logs/}"; \
		echo "----------------$${datestr}"; \
		echo -n "- processed: "; \
			grep "finished processing" $${logdir}/*.log | wc -l; \
		echo -n "- failures:  "; \
			grep -l "whoopsie" $${logdir}/*.log | wc -l; \
		echo "----- files:"; \
		echo -n "- folders:         "; \
			ls "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" | wc -l; \
		echo -n "- # of base.apk's: "; \
			find "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" -name "base.apk" -type f | wc -l; \
		echo -n "- # of base.dm's:  "; \
			find "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" -name "base.dm" -type f | wc -l; \
		echo; \
	done

.PHONY: stats-on-logs-latest
stats-on-logs-latest:
	@logdir=logs/`ls logs | sort | tail -1`; \
		datestr="$${logdir##logs/}"; \
		echo "----------------$${datestr}"; \
		echo -n "- processed: "; \
			grep "finished processing" $${logdir}/*.log | wc -l; \
		echo -n "- failures:  "; \
			grep -l "whoopsie" $${logdir}/*.log | wc -l; \
		echo "----- files:"; \
		echo -n "- folders:         "; \
			ls "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" | wc -l; \
		echo -n "- # of base.apk's: "; \
			find "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" -name "base.apk" -type f | wc -l; \
		echo -n "- # of base.dm's:  "; \
			find "/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes/$${datestr}/" -name "base.dm" -type f | wc -l; \
		
