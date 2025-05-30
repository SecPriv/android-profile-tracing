include ../../Makefile.variable
include ./Makefile.variable

dummy:
	python3 acvtool/acvtool.py -h

test-acv-time: JOBNAME=test-acv-time
test-acv-time: DURATION=10
test-acv-time: TOOL=time
test-acv-time: INPUTCSV=../preliminary_time/input.csv
test-acv-time: DEVICEID=$(DEVICEID_P8_GENIUS)
test-acv-time: --run-acvtool

stats-test-acv-time: JOBNAME=test-acv-time
stats-test-acv-time: --stats-acvtool

details:
	ls _parallel_meta/test-acv-time.results/1/ | wc -l
	rm list_*
	grep -L '^Command exited' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_success | wc -l
	grep -l '^Command exited' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error | wc -l
	@echo "---- known errors"
	grep -l 'INSTALL_PARSE_FAILED_NOT_APK' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_parse_failed | wc -l
	grep -l 'MISSING_SPLIT' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_missing_split | wc -l
	grep -l 'DUPLICATE_PERMISSION' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_dupli_perm | wc -l
	grep -l 'SHARED_USER_INCOMPATIBLE' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_shared_user | wc -l
	grep -l 'UPDATE_INCOMPATIBLE' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_update_incompatible | wc -l
	grep -l 'INVALID_APK' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_invalid_apk | wc -l
	grep -l 'FAILED_VERIFICATION_FAILURE' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_install_failed_verification_b | wc -l
	grep -l 'Error: b'"'"'Exception in thread "main" ' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_apktool_exc | wc -l
	grep -l 'Error: Exception in thread "main" ' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_apktool_exc | wc -l
	grep -l '^KeyError: ' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_keyerror | wc -l
	grep -l '^ValueError: ' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_valueerror | wc -l
	grep -l '^Error: zipro' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_zipro | wc -l
	grep -l 'Consider: \$$ acv snap ' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_snap_failed | wc -l
	grep -l 'Consider: \$$ acv cover' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_cover_failed | wc -l
	grep -l 'Error: b"AndroidManifest.xml' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_parsing_manifest_b | wc -l
	grep -l 'Error: AndroidManifest.xml' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_parsing_manifest | wc -l
	grep -l 'Error: b.*Invalid register' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_repack_register | wc -l
	grep -l 'IndexError' _parallel_meta/test-acv-time.results/1/**/stdout | sort | tee list_error_index_error | wc -l
	@echo "---- known errors"
	rm -f meta_list_error_known && cat list_error_* | sort > meta_list_error_known && rm -f list_error_unkown && comm -23 list_error meta_list_error_known > list_error_unknown  && wc -l list_error_unknown
	

