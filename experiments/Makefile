DEVICEID_P8_GENIUS=3A121FDJH00BT3
DEVICEID_P8_CAFFEINATED=38270DLJH004Q0
DEVICEID_P8_COOL=38091FDJH00PDT
DEVICEID_P8_PIONEER=39281FDJH006XT

CMD='su -c getprop ro.build.description'

test-devices:
	@if timeout 5 adb -s $(DEVICEID_P8_GENIUS) shell $(CMD); then \
		echo "++++ genius ready"; \
		else echo "---- genius missing"; fi
	@if timeout 5 adb -s $(DEVICEID_P8_CAFFEINATED) shell $(CMD); then \
		echo "++++ caffeinated ready"; \
		else echo "---- caffeinated missing"; fi
	@if timeout 5 adb -s $(DEVICEID_P8_COOL) shell $(CMD); then \
		echo "++++ cool ready"; \
		else echo "---- cool missing"; fi
	@if timeout 5 adb -s $(DEVICEID_P8_PIONEER) shell $(CMD); then \
		echo "++++ pioneer ready"; \
		else echo "---- pioneer missing"; fi
