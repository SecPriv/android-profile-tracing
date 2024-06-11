#!/bin/sh

set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

# If you copy the docker commands, add -it to them!

#echo -n "Stage -1: Reconnecting the storage server: "
#    if [ -f /mnt/SecPrivSt1/MOUNTED ]; then 
#        echo " (not necessary)"; 
#    else 
#        sshfs -o idmap=user playstorescraper@st1.secpriv.tuwien.ac.at:/data/playstorescraper /mnt/SecPrivSt1
#        echo "(reconnected)"
#    fi

echo -n "Stage 0: "
python src/stage0_prepare.py

echo -n "Stage 1: "
docker run      --name stage1_charts -v "$PWD":/usr/src/app -w /usr/src/app node:22.2 npm install google-play-scraper
docker run --rm --name stage1_charts -v "$PWD":/usr/src/app -w /usr/src/app node:22.2 src/stage1_charts.js

echo -n "Stage 2: "
python src/stage2_collect.py

echo -n "Stage 3: "
docker run      --name stage3_fullDetails -v "$PWD":/usr/src/app -w /usr/src/app node:22.2 npm install google-play-scraper
docker run --rm --name stage3_fullDetails -v "$PWD":/usr/src/app -w /usr/src/app node:22.2 src/stage3_fullDetails.js

echo -n "Stage 4: "
sh src/stage4_fix.sh

echo -n "Stage 5: "
sh src/stage5_zip.sh

echo -n "Stage 6: "
sh src/stage6_copy.sh

# echo -n "Stage 7: "
# sh src/stage7_apps.sh

echo "Finished successfully";

date;

echo "TODO: DELETE FILES FROM SOURCE COMPUTER"
