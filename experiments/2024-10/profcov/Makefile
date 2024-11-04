

num_methods.csv:
	grep -Ero "tracing .+ methods" time/_parallel_meta/time-01.results/ | choose -f : 1 | choose 1 | choose -f / 0 | sort -n > num_methods.csv

lost_events.txt:
	grep -Ero "total lost events: [0-9]+" ./**/_parallel_meta/**.results/ | choose -1 | sort -n | uniq -c > lost_events.txt

processed_events.txt:
	 grep -Ero "processed [0-9]+ events" ./**/_parallel_meta/**.results/ | choose -2 | sort -n | uniq -c > processed_envents.txt

stats:
	@echo min, max, median, mean, stdev
	@echo number of traced methods:
	cat ./num_methods.csv | datamash min 1 max 1 median 1 mean 1 sstdev 1
	@echo processed events:
	cat ./processed_envents.txt | choose 1 | datamash min 1 max 1 median 1 mean 1 sstdev 1
	@echo lost events:
	cat ./lost_events.txt | choose 1 | datamash min 1 max 1 median 1 mean 1 sstdev 1

