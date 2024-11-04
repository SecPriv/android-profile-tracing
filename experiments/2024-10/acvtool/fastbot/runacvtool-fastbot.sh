#!/bin/bash

set -e 

DATADIR=../../../__data/aot-scrapes/daily_apk_dm_scrapes/2024-04-01/
TIME=$1
APP=$2
DEVICEID=$3
JOBNAME=$4

WORKINGDIR=wd_${JOBNAME}

EXITNUM=33 # default premature termination

clean_up() {
    adb -s ${DEVICEID} uninstall ${APP} || true
    adb -s ${DEVICEID} shell rm -r /sdcard/Download/${APP} || true
    echo "cleaned up"
    exit ${EXITNUM}
}

trap clean_up EXIT

mkdir -p ${WORKINGDIR}

echo ">>> uninstalling if installed"
adb -s ${DEVICEID} uninstall ${APP} || true
# if ran before, creating the result dir fails, so we make sure to remove it 
adb -s ${DEVICEID} shell rm -r /sdcard/Download/${APP} || true # can fail


echo ">>> instrumenting"
#if app exists, don't recreate
echo 'n' | python3 acvtool/acvtool.py instrument ${DATADIR}/${APP}/base.apk --wd ${WORKINGDIR}/${APP} -g method || true # can fail? 
echo ">>> installing "
python3 acvtool/acvtool.py install -d ${DEVICEID} ${WORKINGDIR}/${APP}/instr_${APP}.apk

echo ">>> activating"
python3 acvtool/acvtool.py activate -d ${DEVICEID} ${APP}
# because acvtool start blocks, we call the activity manager ourselves
timeout 30s adb -s ${DEVICEID} shell am instrument ${APP}/tool.acv.AcvInstrumentation || true

echo ">>> running tool for ${TIME}s -----------------------------------------------"
#
#
# IMPORTANT: this needs to be synced with aproftracer.py's invocation to be comparable!
#
#
timeout $((TIME+90))s adb -s ${DEVICEID} exec-out "CLASSPATH=/sdcard/monkeyq.jar:/sdcard/framework.jar:/sdcard/fastbot-thirdpart.jar exec app_process /system/bin com.android.commands.monkey.Monkey -p ${APP} -s 20240412 --agent reuseq --running-minutes $(( (($TIME + 59) / 60) * 60 )) --throttle 1000" || true

adb -s ${DEVICEID} shell 'pgrep monkey | xargs kill' || true

echo ">>> snapshotting"
# snapshots can be done more often but create huge amounts of data
timeout 5s python3 acvtool/acvtool.py snap -d ${DEVICEID} --wd ${WORKINGDIR}/${APP} ${APP} || true

echo ">>> stopping"
python3 acvtool/acvtool.py stop -d ${DEVICEID} ${APP}

echo ">>> create cov"
python3 acvtool/acvtool.py cover-pickles -d ${DEVICEID} --wd ${WORKINGDIR}/${APP} ${APP}

echo ">>> create report"
python3 acvtool/acvtool.py report --wd ${WORKINGDIR}/${APP} ${APP} -g method

echo "done \\o/"

EXITNUM=0

clean_up
