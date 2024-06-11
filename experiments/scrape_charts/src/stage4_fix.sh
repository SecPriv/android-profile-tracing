export CHARTS_PATH="$(jq -r '.chartsPath' < session.json)";
export FULLDETAILS_PATH="$(jq -r '.fullDetailsPath' < session.json)";
echo "Fixing permissions";
sudo chown -R --from root:root $CHARTS_PATH --reference="./session.json";
sudo chown -R --from root:root $FULLDETAILS_PATH --reference="./session.json"
# Please note the * at the end of the variables