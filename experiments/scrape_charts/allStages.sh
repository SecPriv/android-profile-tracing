#!/bin/bash

set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

# If you copy the docker commands, add -it to them!

# echo -n "Stage -1: Reconnecting the storage server: "
#     if [ -f /mnt/SecPrivSt1/MOUNTED ]; then 
#         echo " (not necessary)"; 
#     else 
#         sshfs -o idmap=user playstorescraper@st1.secpriv.tuwien.ac.at:/data/playstorescraper /mnt/SecPrivSt1
#         echo "(reconnected)"
#     fi

echo "Stage 0a: preparing lists of categories "
python src/stage0_prepare.py

echo "Stage 0b: npm dependencies"
docker run --rm --name prep_deps -v "$PWD":/usr/src/app -w /usr/src/app node npm install google-play-scraper

echo "Stage 1: download charts"
docker run --rm --name stage1_charts -v "$PWD":/usr/src/app -w /usr/src/app node src/stage1_charts.js

echo "Stage 2: grab data from charts"
python src/stage2_collect.py

echo "Stage 3: grab metadata from charts"
docker run --rm --name stage3_fullDetails -v "$PWD":/usr/src/app -w /usr/src/app node src/stage3_fullDetails.js

echo "Stage 4: fix metadata"
sh src/stage4_fix.sh

echo "Stage 5: "
sh src/stage5_zip.sh

# echo "Stage 6: "
# sh src/stage6_copy.sh

# echo -n "Stage 7: "
# sh src/stage7_apps.sh

echo "Finished successfully";

date;

echo "TODO: DELETE FILES FROM SOURCE COMPUTER"
