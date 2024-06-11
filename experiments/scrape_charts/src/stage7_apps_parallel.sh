export SAMPLE_APKPURE=$(jq -r '.serverSampleApkPurePath' < session.json);
export SAMPLE_FDROID=$(jq -r '.serverSampleFDroidPath' < session.json);
export SAMPLE_GOOGLEPLAY=$(jq -r '.serverSampleGoolePlayPath' < session.json);
export SAMPLE_HUAWEI=$(jq -r '.serverSampleHuaweiAppGalleryPath' < session.json);
export TOP_APKPURE=$(jq -r '.serverTopApkPurePath' < session.json);
export TOP_FDROID=$(jq -r '.serverTopFDroidPath' < session.json);
export TOP_GOOGLEPLAY=$(jq -r '.serverTopGoolePlayPath' < session.json);
export TOP_HUAWEI=$(jq -r '.serverTopHuaweiAppGalleryPath' < session.json);
export SLEEP_DURATION=$(jq -r '.sleepDuration' < session.json);
export NUM_PAR=$(jq -r '.parallel' < session.json);
export TOP_APPS=$(jq -r '.topApps' < session.json);
export SAMPLE_APPS=$(jq -r '.sampleApps' < session.json);
export GOOGLE_ACCOUNT=$(jq -r '.googleAccount' < session.json);
export GOOGLE_PASSWORD=$(jq -r '.googlePassword' < session.json);
# https://github.com/EFForg/apkeep/releases
# apkeep-x86_64-unknown-linux-gnu
echo "Downloading APKs";
echo -e "./apkeep -d apk-pure -s $SLEEP_DURATION -r $NUM_PAR -c $SAMPLE_APPS $SAMPLE_APKPURE; ./apkeep -d apk-pure -s $SLEEP_DURATION -r $NUM_PAR -c $TOP_APPS $TOP_APKPURE; \n ./apkeep -d f-droid -s $SLEEP_DURATION -r $NUM_PAR -c $SAMPLE_APPS $SAMPLE_FDROID; ./apkeep -d f-droid -s $SLEEP_DURATION -r $NUM_PAR -c $TOP_APPS $TOP_FDROID; \n ./apkeep -d google-play -o include_additional_files=true -u $GOOGLE_ACCOUNT -p $GOOGLE_PASSWORD -s $SLEEP_DURATION -r $NUM_PAR -c $SAMPLE_APPS $SAMPLE_GOOGLEPLAY; ./apkeep -d google-play -o include_additional_files=true -u downloadingprofiles@gmail.com -p zknnyjbkbeeaesyl -s $SLEEP_DURATION -r $NUM_PAR -c $TOP_APPS $TOP_GOOGLEPLAY; \n ./apkeep -d huawei-app-gallery -s $SLEEP_DURATION -r $NUM_PAR -c $SAMPLE_APPS $SAMPLE_HUAWEI; ./apkeep -d huawei-app-gallery -s $SLEEP_DURATION -r $NUM_PAR -c $TOP_APPS $TOP_HUAWEI;" | parallel -j4 "{}"

#./apkeep -a com.mojang.minecraftpe -d google-play -u downloadingprofiles@gmail.com -p zknnyjbkbeeaesyl ./
# TODO rewrite this into a readable format :)