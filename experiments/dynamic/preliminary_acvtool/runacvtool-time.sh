!/bin/bash

set -e

#DATADIR=../../../__data/aot-scrapes/daily_apk_dm_scrapes/2024-04-01/
DATADIR=../../raw_data/daily_collection/2025-05-07/

TIME=$1
APP=$2
DEVICEID=$3
JOBNAME=$4

WORKINGDIR=wd_${JOBNAME}

EXITNUM=33 # default premature termination
EXIT_FAIL_INSTR=34
EXIT_FAIL_ACTIVATION=35

clean_up() {
    trap - EXIT
    echo ">>> cleaning up"
    /usr/bin/rm -rf ${WORKINGDIR}/${APP}/apktool
    /usr/bin/rm -rf ${WORKINGDIR}/${APP}/_tmp
    /usr/bin/rm -rf ${WORKINGDIR}/${APP}/pickles
    /usr/bin/rm -rf ${WORKINGDIR}/${APP}/covered_pickles
    /usr/bin/rm -rf ${WORKINGDIR}/${APP}/instr_${APP}.apk
    echo ">>> uninstalling"
    adb -s ${DEVICEID} uninstall ${APP} || true
    adb -s ${DEVICEID} shell rm -r /sdcard/Download/${APP} || true
    echo " ... cleaned up"
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
echo 'n' | acv instrument ${DATADIR}/${APP}/${APP}.apk --wd ${WORKINGDIR}/${APP} -g method || true # can fail?

echo " >>> checking if instrumented"
if [ ! -f ${WORKINGDIR}/${APP}/instr_${APP}.apk ]; then
    echo "!! can't find ${WORKINGDIR}/${APP}/instr_${APP}.apk"
    exit ${EXIT_FAIL_INSTR}
fi
echo " ... ok!"

# so acvtool just fails if the apk requires to handle split apks
echo ">>> collecting apks to install"
mkdir -p ${WORKINGDIR}/${APP}/_tmp
cp ${WORKINGDIR}/${APP}/instr_*.apk ${WORKINGDIR}/${APP}/_tmp/
cp ${DATADIR}/${APP}/${APP}.*.apk ${WORKINGDIR}/${APP}/_tmp/ || true # can be empty

echo ">>> installing "
adb -s ${DEVICEID} install-multiple ${WORKINGDIR}/${APP}/_tmp/*.apk
#acv install -d ${DEVICEID} ${WORKINGDIR}/${APP}/instr_${APP}.apk

echo " >>> removing apks"
# if we installed, remove local files because they be huge
/usr/bin/rm -rf ${WORKINGDIR}/${APP}/apktool
/usr/bin/rm -rf ${WORKINGDIR}/${APP}/_tmp

echo ">>> activating"
acv activate -d ${DEVICEID} ${APP}
# because acvtool start blocks, we call the activity manager ourselves
timeout 30s adb -s ${DEVICEID} shell am instrument ${APP}/tool.acv.AcvInstrumentation || cleap_up ${EXIT_FAIL_ACTIVATION}

echo ">>> running starting app for ${TIME}s -----------------------------------------------"
#
#
# IMPORTANT: this needs to be synced with aproftracer.py\'s invocation to be comparable!
#
#
adb -s ${DEVICEID} exec-out monkey -p ${APP} 1

sleep ${TIME}

echo ">>> snapshotting"
# snapshots can be done more often but create huge amounts of data
timeout 5s acv snap -d ${DEVICEID} --wd ${WORKINGDIR}/${APP} ${APP} || true

echo ">>> stopping"
acv stop -d ${DEVICEID} ${APP}

echo ">>> create cov"
acv cover-pickles -d ${DEVICEID} --wd ${WORKINGDIR}/${APP} ${APP}

echo ">>> create report"
acv report --wd ${WORKINGDIR}/${APP} ${APP} -g method

echo "done \\o/"

EXITNUM=0

clean_up
