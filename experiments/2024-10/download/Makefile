
APPLISTCSV=../../app_selection/apps_that_we_have_and_run_on_droidbot.csv

guard:
	@echo "invoking make without a target, are we now?"

download-test-apps-new:
	mkdir -p meta_download.results
	cat $(APPLISTCSV) | parallel \
		-j1 \
		--joblog meta_download.joblog \
		--resume \
		--eta \
		--results meta_download.results/ \
		'/usr/bin/time -v nice -n 5 -- choom -n 1000 -- ./download.py -o apps/ -v {}'

check-count:
	@echo -n "downloaded base.apks: " && \
		find apps/ -type f -name "base.apk" | wc -l
	@echo -n "downloaded base.dms: " && \
		find apps/ -type f -name "base.dm" | wc -l
	@echo -n "base dms w/ primary.prof: " && \
		for f in $$(find apps/ -type f -name "base.dm"); do if unzip -l $$f | grep -q primary.prof ; then echo there; fi; done | wc -l
	@echo -n "missing apks: " && while read app; do if [ ! -f apps/$$app/base.apk ]; then echo " - $$app"; fi; done < $(APPLISTCSV) | wc -l
	@while read app; do if [ ! -f apps/$$app/base.apk ]; then echo " - $$app"; fi; done < $(APPLISTCSV)

clean:
	rm -rf meta_*

copy-to-storage:
	rsync -Phav apps/ ../../__data/experiments-2024-10/apps-2024-10-11