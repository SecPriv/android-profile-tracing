# create directories, if they don't exist
import json
import os
from datetime import date

print("Preparing settings")

# LOCALE SETTINGS
country = "at"
lang = "en"

# DOWNLOAD SETTINGS
# JavaScript
downloadDelay = 1000
simultaneousDownloads = 10
# apkeep
sleepDuration = 10000  # ms
parallel = 1
googleAccount = "downloadingprofiles@gmail.com"
googlePassword = "srxuxdvywqassfva"

# LOCAL DIRECTORY PATHS
date = str(date.today())
datePath = "./daily/"+date+"/"   # override this with argv?
chartsPath = datePath+"charts/"
fullDetailsPath = datePath+"fullDetails/"
topAppsPath = datePath+"topApps/"
sampleAppsPath = datePath+"sampleApps/"
topApkPurePath = topAppsPath+"apkPure/"
topFDroidPath = topAppsPath+"fDroid/"
topGoolePlayPath = topAppsPath+"googlePlay/"
topHuaweiAppGalleryPath = topAppsPath+"huaweiAppGallery/"
sampleApkPurePath = sampleAppsPath+"apkPure/"
sampleFDroidPath = sampleAppsPath+"fDroid/"
sampleGoolePlayPath = sampleAppsPath+"googlePlay/"
sampleHuaweiAppGalleryPath = sampleAppsPath+"huaweiAppGallery/"

# LOCAL FILE PATHS
chartsJsonPath = datePath+"charts.json"
chartsZipPath = datePath+"charts.zip"
fullDetailsZipPath = datePath+"fullDetails.zip"
# topAppsZipPath = datePath+"topApps.zip"
# sampleAppsZipPath = datePath+"sampleApps.zip"
topApps = "./top250FreeApps"
sampleApps = "./sample250FreeApps"

# SERVER PATHS
serverPath = "/mnt/SecPrivSt1/profiles/daily/"+date+"/"
serverSessionPath = serverPath+"session.json"
serverChartsJsonPath = serverPath+"charts.json"
serverChartsZipPath = serverPath+"charts.zip"
serverFullDetailsZipPath = serverPath+"fullDetails.zip"
serverTopAppsPath = serverPath+"topApps/"
serverSampleAppsPath = serverPath+"sampleApps/"
serverTopApkPurePath = serverTopAppsPath+"apkPure/"
serverTopFDroidPath = serverTopAppsPath+"fDroid/"
serverTopGoolePlayPath = serverTopAppsPath+"googlePlay/"
serverTopHuaweiAppGalleryPath = serverTopAppsPath+"huaweiAppGallery/"
serverSampleApkPurePath = serverSampleAppsPath+"apkPure/"
serverSampleFDroidPath = serverSampleAppsPath+"fDroid/"
serverSampleGoolePlayPath = serverSampleAppsPath+"googlePlay/"
serverSampleHuaweiAppGalleryPath = serverSampleAppsPath+"huaweiAppGallery/"


# CREATE PATHS
paths = [
    chartsPath,
    fullDetailsPath,
    topApkPurePath,
    topFDroidPath,
    topGoolePlayPath,
    topHuaweiAppGalleryPath,
    sampleApkPurePath,
    sampleFDroidPath,
    sampleGoolePlayPath,
    sampleHuaweiAppGalleryPath,
    serverPath,
    serverTopApkPurePath,
    serverTopFDroidPath,
    serverTopGoolePlayPath,
    serverTopHuaweiAppGalleryPath,
    serverSampleApkPurePath,
    serverSampleFDroidPath,
    serverSampleGoolePlayPath,
    serverSampleHuaweiAppGalleryPath,
]
for path in paths:
    os.makedirs(path, exist_ok=True)

# WRITE session.json
session = {
    "country": country,
    "lang": lang,

    "downloadDelay": downloadDelay,
    "simultaneousDownloads": simultaneousDownloads,
    "sleepDuration": sleepDuration,
    "parallel": parallel,
    "googleAccount": googleAccount,
    "googlePassword": googlePassword,

    "date": date,  # unused
    "datePath": datePath,  # unused
    "chartsPath": chartsPath,
    "fullDetailsPath": fullDetailsPath,
    "topAppsPath": topAppsPath,  # unused
    "sampleAppsPath": sampleAppsPath,  # unused
    "topApkPurePath": topApkPurePath,
    "topFDroidPath": topFDroidPath,
    "topGoolePlayPath": topGoolePlayPath,
    "topHuaweiAppGalleryPath": topHuaweiAppGalleryPath,
    "sampleApkPurePath": sampleApkPurePath,
    "sampleFDroidPath": sampleFDroidPath,
    "sampleGoolePlayPath": sampleGoolePlayPath,
    "sampleHuaweiAppGalleryPath": sampleHuaweiAppGalleryPath,

    "chartsJsonPath": chartsJsonPath,
    "chartsZipPath": chartsZipPath,
    "fullDetailsZipPath": fullDetailsZipPath,
    # "topAppsZipPath": topAppsZipPath,
    # "sampleAppsZipPath": sampleAppsZipPath,
    "topApps": topApps,
    "sampleApps": sampleApps,

    "serverPath": serverPath,
    "serverSessionPath": serverSessionPath,
    "serverChartsJsonPath": serverChartsJsonPath,
    "serverChartsZipPath": serverChartsZipPath,
    "serverFullDetailsZipPath": serverFullDetailsZipPath,
    "serverTopAppsPath": serverTopAppsPath,  # unused
    "serverSampleAppsPath": serverSampleAppsPath,  # unused
    "serverTopApkPurePath":    serverTopApkPurePath,
    "serverTopFDroidPath": serverTopFDroidPath,
    "serverTopGoolePlayPath": serverTopGoolePlayPath,
    "serverTopHuaweiAppGalleryPath": serverTopHuaweiAppGalleryPath,
    "serverSampleApkPurePath": serverSampleApkPurePath,
    "serverSampleFDroidPath": serverSampleFDroidPath,
    "serverSampleGoolePlayPath": serverSampleGoolePlayPath,
    "serverSampleHuaweiAppGalleryPath": serverSampleHuaweiAppGalleryPath,
}

with open("./session.json", "w") as f:
    json.dump(session, f)
