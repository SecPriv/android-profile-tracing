#!/usr/bin/bash

set -e
set -u
set -o pipefail
set -x

TODAY=`date +"%Y-%m-%d"`

WD=/home/jakob/code/daily-profile-scrapes

STORAGE_DESTINATION_ROOT=/mnt/SecPrivSt1/playstorescraper/2025-03-aot-scrapes
TMP_SAVE=${WD}/out
PAR_META=${WD}/_parallel_logs_${TODAY}
APPS_CSV=${WD}/apps.csv



# download apps
echo "downloading apps on ${TODAY}"
echo "start time: `date`"
http --ignore-stdin -j POST https://mattermost.secpriv.wien/api/v4/posts Authorization:"Bearer bbn1iqkm9ffi3qtbhtb8ekbw7w" channel_id="i9h39fjiuinri8ydc7u5r5gj5c" message="starting app scrape for dexmetadata files at `date`" > /dev/null || true


mkdir -p ${TMP_SAVE} ${PAR_META}

cat ${APPS_CSV} | cut -d ',' -f 1 | parallel \
    --joblog ${PAR_META}/dl.joblog \
    --results ${PAR_META}/dl.results/ \
    --resume \
    --delay 10 \
    --jobs 4 \
    --workdir ${WD} \
    /home/jakob/.local/bin/apkeep-fork -a {} -d google-play -i ./google_play.ini -o device=sp_pixel8,split_apk=true,include_dexmetadata=true,include_additional_files=true,device_properties=device.properties,always_appid_dir=true ${TMP_SAVE} \
    || true # if a single dl fails we still want to continue


echo "end time: `date`"

http --ignore-stdin -j POST https://mattermost.secpriv.wien/api/v4/posts Authorization:"Bearer bbn1iqkm9ffi3qtbhtb8ekbw7w" channel_id="i9h39fjiuinri8ydc7u5r5gj5c" message="successfully downloaded `ls ${TMP_SAVE} | wc -l`" > /dev/null || true

# move to storage
echo "moving to storage"

mv ${TMP_SAVE} ${WD}/${TODAY}

if [ ! -d ${STORAGE_DESTINATION_ROOT} ]; then
    echo "ERROR: storage not mounted"
    http --ignore-stdin -j POST https://mattermost.secpriv.wien/api/v4/posts Authorization:"Bearer bbn1iqkm9ffi3qtbhtb8ekbw7w" channel_id="i9h39fjiuinri8ydc7u5r5gj5c" message="ERROR: storage not mounted! @jakob help me!" > /dev/null || true
    exit 1
fi

rsync -Phva ${WD}/${TODAY} ${STORAGE_DESTINATION_ROOT}

rm -r ${WD}/${TODAY}


echo "done at: `date`"
