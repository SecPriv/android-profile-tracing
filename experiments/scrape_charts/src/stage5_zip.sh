export CHARTS_PATH=$(jq -r '.chartsPath' < session.json);
export CHARTS_ZIP_PATH=$(jq -r '.chartsZipPath' < session.json);
export FULLDETAILS_PATH=$(jq -r '.fullDetailsPath' < session.json);
export FULLDETAILS_ZIP_PATH=$(jq -r '.fullDetailsZipPath' < session.json);
#export TOPAPPS_PATH=$(jq -r '.topAppsPath' < session.json);
#export TOPAPPS_ZIP_PATH=$(jq -r '.topAppsZipPath' < session.json);
#export SAMPLEAPPS_PATH=$(jq -r '.sampleAppsPath' < session.json);
#export SAMPLEAPPS_ZIP_PATH=$(jq -r '.sampleAppsZipPath' < session.json);
echo "Zipping charts and details"
zip -r -m "$CHARTS_ZIP_PATH" "$CHARTS_PATH";
# unzip "$CHARTS_ZIP_PATH"
zip -r -m "$FULLDETAILS_ZIP_PATH" "$FULLDETAILS_PATH";
# unzip "$FULLDETAILS_ZIP_PATH"
#zip -r -m "$TOPAPPS_ZIP_PATH" "$TOPAPPS_PATH";
# unzip "$TOPAPPS_ZIP_PATH"
#zip -r -m "$SAMPLEAPPS_ZIP_PATH" "$SAMPLEAPPS_PATH";
# unzip "$SAMPLEAPPS_ZIP_PATH"