#!/bin/bash

set -e 

DEVICE_ID_CAFFEINATED=38270DLJH004Q0

DEVICE_ID=${DEVICE_ID_CAFFEINATED}
DATADIR=../../../../__data/2024-04-01

TIME=$1
APP=$2

EXITNUM=33 # default premature termination

clean_up() {
    adb -s ${DEVICE_ID} uninstall ${APP} || true
    adb -s ${DEVICE_ID} shell rm -r /sdcard/Download/${APP} || true
    echo "cleaned up"
    exit ${EXITNUM}
}

trap clean_up EXIT

mkdir -p wd

echo ">>> uninstalling if installed"
adb -s ${DEVICE_ID} uninstall ${APP} || true
# if ran before, creating the result dir fails, so we make sure to remove it 
adb -s ${DEVICE_ID} shell rm -r /sdcard/Download/${APP} || true # can fail


echo ">>> instrumenting"
#if app exists, don't recreate
echo 'n' | python3 acvtool/acvtool.py instrument ${DATADIR}/${APP}/base.apk --wd wd/${APP} -g method || true # can fail? 
echo ">>> installing "
python3 acvtool/acvtool.py install -d ${DEVICE_ID} wd/${APP}/instr_${APP}.apk

echo ">>> activating"
python3 acvtool/acvtool.py activate -d ${DEVICE_ID} ${APP}
# because acvtool start blocks, we call the activity manager ourselves
timeout 30s adb shell am instrument ${APP}/tool.acv.AcvInstrumentation || true

echo ">>> running starting app for 10s -----------------------------------------------"
adb -s ${DEVICE_ID} exec-out monkey -p ${APP} 1 

sleep ${TIME}

echo ">>> snapshotting"
# snapshots can be done more often but create huge amounts of data
timeout 5s python3 acvtool/acvtool.py snap -d ${DEVICE_ID} --wd wd/${APP} ${APP} || true

echo ">>> stopping"
python3 acvtool/acvtool.py stop -d ${DEVICE_ID} ${APP}

echo ">>> create cov"
python3 acvtool/acvtool.py cover-pickles -d ${DEVICE_ID} --wd wd/${APP} ${APP}

echo ">>> create report"
python3 acvtool/acvtool.py report --wd wd/${APP} ${APP} -g method

echo "done \\o/"

EXITNUM=0

clean_up
