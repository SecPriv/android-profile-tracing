export SESSION_PATH="./session.json"
export SERVER_SESSION_PATH=$(jq -r '.serverSessionPath' < session.json);
export CHARTS_ZIP_PATH=$(jq -r '.chartsZipPath' < session.json);
export CHARTS_JSON_PATH=$(jq -r '.chartsJsonPath' < session.json);
export FULLDETAILS_ZIP_PATH=$(jq -r '.fullDetailsZipPath' < session.json);
export SERVER_CHARTS_ZIP_PATH=$(jq -r '.serverChartsZipPath' < session.json);
export SERVER_CHARTS_JSON_PATH=$(jq -r '.serverChartsJsonPath' < session.json);
export SERVER_FULLDETAILS_ZIP_PATH=$(jq -r '.serverFullDetailsZipPath' < session.json);
echo "Copying files to storage server"
cp "$SESSION_PATH" "$SERVER_SESSION_PATH";
cp "$CHARTS_ZIP_PATH" "$SERVER_CHARTS_ZIP_PATH";
cp "$CHARTS_JSON_PATH" "$SERVER_CHARTS_JSON_PATH";
cp "$FULLDETAILS_ZIP_PATH" "$SERVER_FULLDETAILS_ZIP_PATH";
