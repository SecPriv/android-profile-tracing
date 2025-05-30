

jupyter:
	uv run --with androguard --with seaborn --with jupyter --with pandas --with matplotlib jupyter lab explore.ipynb

summary:
	 cat libs.txt | parallel -j1 "grep '^{}' resultingmethods.csv | wc -l | sed 's|$$| {}|'" | sort -n

dump-activities:
	while true; do adb shell dumpsys activity a | grep '[^p]ResumedActivity' | choose 3 | ts "%b %d %H:%M:%.S"; sleep 0.5; done

run-aproftracer:
	rm results/ && aproftracer org.thoughtcrime.securesms \
		--device-id 38270DLJH004Q0 \
		--verbose \
		--fresh-install org.thoughtcrime.securesms \
		--max-probes 30000 \
		--tool monkey \
		--tool-max-runtime 10 \
		--result-dir results \
		--no-cleanup-host \
		--also-startup-poststartup \
		--buffer-size-kb 4096 \
		--also-trace-activities \
			| tee aproftracer.log
