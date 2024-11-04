
overview:
	for log in `find . -maxdepth 4 -type f -name "*joblog" | sort`; do wc -l $$log; choose -i $$log 6 | grep -v Exitval | sort | uniq -c; done
