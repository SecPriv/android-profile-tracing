#!/usr/bin/env python3

import click
import json
import sh
from pathlib import Path
import glob
import tqdm
import datetime
import zipfile
import re
import shutil
import shelve
import traceback
from multiprocessing import Pool


ALL_DAILY_DIR = Path("/mnt/SecPrivSt1/playstorescraper/2025-03-aot-scrapes/")


SAMPLE_DAY_DIR=Path("../../raw_data/daily_collection/2025-05-07/")


CACHE_DIR = Path("./_analysis_cache/")
HASH_CACHE = CACHE_DIR / "hashed"
HASH_CACHE.mkdir(exist_ok=True, parents=True)
APK_HASH_CACHE = HASH_CACHE / "apkdata"
APK_HASH_CACHE.mkdir(exist_ok=True, parents=True)
APK_VERSION_HASH_CACHE = HASH_CACHE / "apkversions"
APK_VERSION_HASH_CACHE.mkdir(exist_ok=True, parents=True)
PROF_HASH_CACHE = HASH_CACHE / "profdumps"
PROF_HASH_CACHE.mkdir(exist_ok=True, parents=True)
PROFILES_CACHE_DIR = CACHE_DIR / "profiles"
BASELINE_CACHE = PROFILES_CACHE_DIR / "baseline"
BASELINE_CACHE.mkdir(exist_ok=True, parents=True)
CLOUDPROF_CACHE = PROFILES_CACHE_DIR / "cloud"
CLOUDPROF_CACHE.mkdir(exist_ok=True, parents=True)
PROFILEJSON_CACHE = PROFILES_CACHE_DIR / "json"
PROFILEJSON_CACHE.mkdir(exist_ok=True, parents=True)

IN_APK_BASELINE_PATH=Path("assets/dexopt/baseline.prof")
IN_DM_CLOUDPROFILE_PATH=Path("primary.prof")

HASHSHELVE = None
HASHSHELVE_PATH = CACHE_DIR / "hashshelve"

def daily_dirs(do_tqdm=False):
    itr = []
    itr.append(ALL_DAILY_DIR / "2025-03-31")
    itr.extend([Path(ALL_DAILY_DIR / f"2025-04-{i:02}") for i in range(1, 31)])
    itr.extend([Path(ALL_DAILY_DIR / f"2025-05-{i:02}") for i in range(1,21)])
    #itr = sorted([Path(x) for x in glob.glob(str(ALL_DAILY_DIR / "*"))])
    #itr = [x for x in itr if x.is_dir() and "-" in str(x)] # remove "failed" dir and notes
    
    if do_tqdm:
        itr = tqdm.tqdm(itr)
    return itr

def apkdirs_from_daily_dir(daily_dir, do_tqdm=False):
    itr = [Path(x) for x in glob.glob(str(daily_dir / "*"))]
    if do_tqdm:
        itr = tqdm.tqdm(itr)
    return itr

def sample_day_dirs(do_tqdm=False):
    itr = [Path(x) for x in glob.glob(str(SAMPLE_DAY_DIR / "*"))]
    if do_tqdm:
        itr = tqdm.tqdm(itr)
    return itr

def get_date_apkid(apkdir):
    date = apkdir.parent.name
    apkid = apkdir.name
    return date, apkid

def get_base_apkpath(apkdir):
    _, apkid = get_date_apkid(apkdir)
    return apkdir / f"{apkid}.apk"

def get_base_dmpath(apkdir):
    _,apkid = get_date_apkid(apkdir)
    return apkdir / f"{apkid}.dm"

def get_splitapks(apkdir):
    splits = []
    _, apkid = get_date_apkid(apkdir)
    splits.extend(list(glob.glob(f"{apkdir / apkid}.*.apk")))
    return splits

def get_cache_profile_baseline_dir(apkdir):
    """existence indicates apk checked already"""
    date, apkid = get_date_apkid(apkdir)
    return BASELINE_CACHE / date / apkid

def get_cache_profile_cloud_dir(apkdir):
    """existence indicates apk checked already"""
    date, apkid = get_date_apkid(apkdir)
    return CLOUDPROF_CACHE / date / apkid

def get_profdumppath_from_profpath(profpath):
    assert(str(profpath).endswith(".prof"))
    return Path(f"{str(profpath)}dump")

def setup_hashshelve(writeback=False):
    global HASHSHELVE
    HASHSHELVE = shelve.open(HASHSHELVE_PATH, writeback=writeback)

def close_hashshelve():
    global HASHSHELVE
    if HASHSHELVE:
        HASHSHELVE.close()
        HASHSHELVE = None

def get_filehash(filepath):
    global HASHSHELVE
    if HASHSHELVE:
        if str(filepath) in HASHSHELVE:
            return HASHSHELVE[str(filepath)]
    
    filehash = _get_filehash_without_shelve(filepath)

    if HASHSHELVE:
        HASHSHELVE[str(filepath)] = filehash

    return filehash

def _get_filehash_without_shelve(filepath):
    return str(sh.sha256sum(filepath)).split(' ')[0]

def cached_apk_to_version(apkdir):
    date, apkid = get_date_apkid(apkdir)

    base_apk = get_base_apkpath(apkdir)
    apk_hash = get_filehash(base_apk)

    cachefile = APK_VERSION_HASH_CACHE / apk_hash

    if cachefile.exists():
        with open(cachefile) as f:
            return json.load(f)
    
    if base_apk.exists():
        try:
            try:
                versionCode = sh.apkanalyzer("manifest", "version-code", base_apk).strip()
                versionName = sh.apkanalyzer("manifest", "version-name", base_apk).strip()
            except sh.Error.ReturnCode_1:
                print(f"error analyzing {apkid}")
                return None
        except sh.CommandNotFound:
            # why? idk. today computers are not fun
            print(f"error analyzing {apkid}")
            return None

        dexmetadata = { "appid": apkid,
                        "date": date,
                        "versionCode": versionCode,
                        "versionName": versionName
                      }
        
        with open(cachefile, "w") as f:
            json.dump(dexmetadata, f)
        
        return dexmetadata

    return None

def cached_apk_to_metadata(apkdir):

    _, apkid = get_date_apkid(apkdir)

    base_apk = get_base_apkpath(apkdir)
    apk_hash = get_filehash(base_apk)

    cachefile = APK_HASH_CACHE / apk_hash

    if cachefile.exists():
        #print("cache exists")
        with open(cachefile) as f:
            return json.load(f)
        
    #print(f"looking at {apkid}")
    _start = datetime.datetime.now()

    if base_apk.exists():
        num_dex_methods = -1
        try:
            dex_packages = sh.apkanalyzer("dex", "packages", base_apk)
            # if t's a Method and it's defined in the apk
            num_dex_methods = len([method for method in dex_packages.splitlines() if method.startswith("M d")])
        except sh.ErrorReturnCode:
            print(f"WARNING: failed to apkanalyze base.apk for {apkid}")
            return None

        try:
            try:
                versionCode = sh.apkanalyzer("manifest", "version-code", base_apk).strip()
                versionName = sh.apkanalyzer("manifest", "version-name", base_apk).strip()
                activities = [a.split('"')[1] for a in str(sh.awk('/E: activity/ {found=1} found && /A: http:\/\/schemas.android.com\/apk\/res\/android:name/ {print $0; found=0}',_in=sh.aapt2("dump", "xmltree", "--file", "AndroidManifest.xml", base_apk))).splitlines()]
            except sh.Error.ReturnCode_1:
                print(f"error analyzing {apkid}")
                return None
        except sh.CommandNotFound:
            # why? idk. today computers are not fun
            print(f"error analyzing {apkid}")
            return None
        
        _delta = datetime.datetime.now() - _start

        dexmetadata = { "appid": apkid,
                        "time": str(_delta),
                        "versionCode": versionCode,
                        "versionName": versionName,
                        "num_dex_methods": num_dex_methods,
                        "activities": activities}
        
        with open(cachefile, "w") as f:
            json.dump(dexmetadata, f)
        
        return dexmetadata

    else:
        print(f"WARNING: no base.apk for {apkid}!")
        return None
    
def cached_extract_baseline_prof(apkdir, force=False):
    """return profpath"""
    # if cache exists, skip
    targetdir = get_cache_profile_baseline_dir(apkdir)
    if targetdir.exists():
        if force:
            shutil.rmtree(targetdir)
        else:
            return None

    targetdir.mkdir(parents=True)

    apkpath = get_base_apkpath(apkdir)
    try:
        
        zf = zipfile.ZipFile(apkpath)

        # if in apk, extract
        if str(IN_APK_BASELINE_PATH) in zf.namelist():
            zf.extract(str(IN_APK_BASELINE_PATH), targetdir)
            return targetdir / IN_APK_BASELINE_PATH
    except zipfile.BadZipFile:
        print(f"error extracting {apkpath}")
    return None
        
def cached_extract_cloud_prof(apkdir, force=False):
    """return profpath or None"""
    # if cache exists, skip
    targetdir = get_cache_profile_cloud_dir(apkdir)
    if targetdir.exists():
        if force:
            shutil.rmtree(targetdir)
        else:
            return None
    
    try:
        targetdir.mkdir(parents=True)

        # if dm exists
        dmpath = get_base_dmpath(apkdir)
        if dmpath.exists():
            # and file in dm, extract
            zf = zipfile.ZipFile(dmpath)
            if str(IN_DM_CLOUDPROFILE_PATH) in zf.namelist():
                zf.extract(str(IN_DM_CLOUDPROFILE_PATH), targetdir)
                return targetdir / IN_DM_CLOUDPROFILE_PATH

    except zipfile.BadZipFile:
        print(f"error extracting {dmpath}")
    return None
    

def cached_extract_baseline_and_cloud_prof(apkdir, force=False):
    bl = cached_extract_baseline_prof(apkdir, force)
    cl = cached_extract_cloud_prof(apkdir, force)
    return (bl, cl)

uid = sh.id("-u").strip()
gid = sh.id("-g").strip()

def cached_profdump(profpath, cloud=True):
    """return location of profdump but its a hashfile"""
    prof_hash = get_filehash(profpath)
    prof_hash_path = PROF_HASH_CACHE / prof_hash
    if prof_hash_path.exists():
        return prof_hash_path

    # we use a docker container from another research project, but effectively this can also be done by installing the 
    profdumppath = get_profdumppath_from_profpath(profpath)
    if cloud:
        container = "registry.gitlab.secpriv.tuwien.ac.at/secpriv/systemsec/oatmeal-code/oatmeal-android-15.0.0"
    else:
        container = "registry.gitlab.secpriv.tuwien.ac.at/secpriv/systemsec/oatmeal-code/oatmeal-android-11.0.0"
    
    sh.docker(
        "run", "--network", "none", "--rm", "-v", "./:/workdir", "-u", f"{uid}:{gid}",
        container,
        "profman-prepared", str(profpath), str(profdumppath)
    )
    if profdumppath.exists():
        profdumppath.rename(prof_hash_path)
    return prof_hash_path

def cached_get_profdump_path(apkdir, cloud=True):
    _, apkid = get_date_apkid(apkdir)
    location = None
    if cloud:
        profpath = get_cache_profile_cloud_dir(apkdir) / IN_DM_CLOUDPROFILE_PATH
    else:
        profpath = get_cache_profile_baseline_dir(apkdir) / IN_APK_BASELINE_PATH
    if profpath.exists():
        try:
            location = cached_profdump(profpath, cloud=cloud)
        except:
            print(f"error extracting {'cloud' if cloud else 'baseline'} profile for {apkid}")
            raise
    
    if location:
        return location
    return None

def cached_get_profdump_path_both(apkdir):
    bl = cached_get_profdump_path(apkdir, cloud=False)
    cl = cached_get_profdump_path(apkdir, cloud=True)
    return (bl, cl)

def _parse_number_line(line, prefix, split, suffix):
    numbers = []
    for number in line.removeprefix(prefix).removesuffix(suffix).split(split):
        numbers.append(int(number))
    return numbers

def _profile_txt_to_json(profdumppath):
    profile_json = {}
    with open(profdumppath, "r") as f:
        current_dex = -1
        for raw_line in f:
            line = raw_line.strip()
            # skip headers and such
            if (
                line.startswith("===")
                or line.startswith("ProfileInfo")
                or line == ""
            ):
                continue
            # demarks new dexfile entry
            elif "[index=" in line:
                parts = line.split(" ")
                raw_dex = parts[0]
                # the first dex file can be either implied or explicit
                if raw_dex == "base.apk" or raw_dex == "classes.dex":
                    current_dex = 1
                else:
                    # all others are always base.apk!classesN.dex
                    current_dex = int(
                        raw_dex.removeprefix("base.apk!")
                        .removeprefix("classes")
                        .removesuffix(".dex")
                    )
                profile_json[current_dex] = {}
            # parse the different method classifications
            elif line.startswith("hot methods:") and line != "hot methods:":
                # hot methods have some more data that we ignore
                line_without_args = re.sub("\[[^\]]+\]", "[]", line)
                profile_json[current_dex]["hot"] = _parse_number_line(
                    line_without_args, "hot methods: ", "[], ", "[],"
                )
            elif line.startswith("startup methods:") and line != "startup methods:":
                profile_json[current_dex]["startup"] = _parse_number_line(
                    line, "startup methods: ", ", ", ","
                )
            elif (
                line.startswith("post startup methods:")
                and line != "post startup methods:"
            ):
                profile_json[current_dex]["post"] = _parse_number_line(
                    line, "post startup methods: ", ", ", ","
                )
            # we parse it but don't use it
            elif line.startswith("classes:") and line != "classes:":
                profile_json[current_dex]["classes"] = _parse_number_line(
                    line, "classes: ", ",", ","
                )
    return profile_json

def cached_profile_txt_to_json(apkdir, cloud=True):
    profdumppath = cached_get_profdump_path(apkdir, cloud)
    if not profdumppath or not profdumppath.exists():
        return None
    
    profile_json_path = PROFILEJSON_CACHE / f"{get_filehash(profdumppath)}"

    if profile_json_path.exists():
        with open(profile_json_path) as f:
            return json.load(f)

    profile_json = _profile_txt_to_json(profdumppath)

    with open(profile_json_path, "w") as f:
        json.dump(profile_json, f)

    return profile_json

def _prep_all(apkdir):
    try:
        cached_apk_to_version(apkdir)
    except:
        print(f"failed to get version info for {apkdir}")
        traceback.print_exc()
    try:
        cached_extract_baseline_and_cloud_prof(apkdir)
    except:
        print(f"failed to extract prof for {apkdir}")
    try:
        cached_get_profdump_path(apkdir, cloud=False)
    except:
        print(f"failed to get baseline prof for {apkdir}")
    try:
        cached_get_profdump_path(apkdir, cloud=True)
    except:
        print(f"failed to get cloud prof for {apkdir}")
    return None 

def _prepshelve(apkdir):
    global HASHSHELVE
    try:
        baseapk = get_base_apkpath(apkdir)
        if HASHSHELVE:
            if str(baseapk) in HASHSHELVE:
                return baseapk, HASHSHELVE[str(baseapk)]
        return baseapk, _get_filehash_without_shelve(baseapk)
    except:
        print(f"failed to get hash for {apkdir}")
        return None, None

@click.command
@click.option("--app-in-day-dir", default=None, help="used for all testing. required")
@click.option("--also-print", is_flag=True, default=False, help="print stuff to stdout if available")
@click.option("--test-dexmetadata", is_flag=True, default=False, help="process dexmetadata")
@click.option("--test-extract-profiles", is_flag=True, default=False, help="extract profiles if available")
@click.option("--test-profdump-path", is_flag=True, default=False, help="create profdump")
@click.option("--setup-shelve-only", is_flag=True, default=False)
@click.option("--do-all-longitudinal", default = 0, help="processes for exporting all longitudinal metadata")
@click.option("--show-profdump", default=None, help="resolve cache hashes and show content of cloud profdumpfor <appid,date,iscloud>")
def main(app_in_day_dir, also_print,
         test_dexmetadata, 
         test_extract_profiles, 
         test_profdump_path,
         setup_shelve_only,
         do_all_longitudinal,
         show_profdump):
    """test stuff on the commandline"""

    if app_in_day_dir:
        apkdir = Path(app_in_day_dir)
    else:
        apkdir = None

    if test_dexmetadata:
        if not app_in_day_dir:
            raise ValueError("app in day dir required")
        dexmetadata = cached_apk_to_metadata(apkdir)
        if also_print:
            print(dexmetadata)
    
    if test_extract_profiles:
        if not app_in_day_dir:
            raise ValueError("app in day dir required")
        x = cached_extract_baseline_and_cloud_prof(apkdir, force=True)
        if also_print:
            print(x)
    
    if test_profdump_path:
        if not app_in_day_dir:
            raise ValueError("app in day dir required")
        x = cached_get_profdump_path_both(apkdir)
        if also_print:
            print(x)

    if setup_shelve_only:
        setup_hashshelve()
        print("running 6 processes, adjust in src if not good")
        pool = Pool(processes=6)
        for daily_dir in daily_dirs():
            for apkpath, filehash in tqdm.tqdm(pool.imap_unordered(
                _prepshelve,
                apkdirs_from_daily_dir(daily_dir)
            ), total=len(apkdirs_from_daily_dir(daily_dir))):
                if apkpath and str(apkpath) not in HASHSHELVE:
                    HASHSHELVE[str(apkpath)] = filehash
            HASHSHELVE.sync()
        close_hashshelve()
        return
    
    if do_all_longitudinal > 0:
        setup_hashshelve()
        pool = Pool(processes=do_all_longitudinal)

        # we pull a trick here: because we don't expect two apks with different ids to share a hash, we do this in batches of days, where each id is unique. so we don't have to worry about likely raceconditions or collisions
        for daily_dir in daily_dirs():
            print(daily_dir.name)
            for _ in tqdm.tqdm(pool.imap_unordered(
                        _prep_all,
                        apkdirs_from_daily_dir(daily_dir)
                    ), total=len(apkdirs_from_daily_dir(daily_dir))):
                pass

        close_hashshelve()

    if show_profdump:
        appid, date, iscloud = show_profdump.split(',')
        apkdir = Path(f"/mnt/SecprivSt1/playstorescraper/2025-03-aot-scrapes/{date}/{appid}")
        if "rue" in iscloud:
            profhash = get_filehash(get_cache_profile_cloud_dir(apkdir) / IN_DM_CLOUDPROFILE_PATH)
        else:
            profhash = get_filehash(get_cache_profile_baseline_dir(apkdir) / IN_APK_BASELINE_PATH)
        profdump = PROF_HASH_CACHE / profhash
        print(profdump)
        with open(profdump) as f:
            print(f.read())

if __name__ == "__main__":
    main()
