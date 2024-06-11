import glob
import json

print("Extracting list of appIds")

with open("./session.json") as f:
    session = json.load(f)

chartsJsonPath = session["chartsJsonPath"]
appIds = set()

index = session["chartsPath"]
for path in glob.glob(index+"*.json"):
    with open(path, "r") as f:
        content = json.load(f)
        for app in content:
            appIds.add(app["appId"])

with open(chartsJsonPath, "w") as f:
    json.dump(sorted(appIds), f)
