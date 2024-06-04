#!/usr/bin/env python3

import logging
import traceback
from datetime import datetime
from multiprocessing import Pool, Queue
from pathlib import Path

import adbdevice
import click
import sh

_today = datetime.today().strftime('%Y-%m-%d')

LOGDIR = Path("logs/") / _today
LOGFMT ='{asctime}|{levelname}|{name}|{message}'
STORAGEDIR = Path("/mnt/SecPrivSt1/aot-scrapes/daily_apk_dm_scrapes") / _today

logging.basicConfig(format=LOGFMT,  style="{",)
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


def _install(device, appid):
    log.debug(f"entering install for {appid}")
    device.install(appid)

def _get_apk_dm(device, appid):
    dumppath = STORAGEDIR / appid
    dumppath.mkdir(parents=True, exist_ok=True)

    log.debug(f"entering get_apk_dm for {appid}, dumping to {dumppath}")
    device.dump_apk_dm(appid, str(dumppath)) # TODO upstream usage of Path

def _uninstall(device, appid):
    # silently ignore if not installed, called again if exception occurs
    log.debug(f"entering uninstall for {appid}")
    device.uninstall_single(appid)

def _harvest(serial, appid):
    ok = False

    device = adbdevice.AdbDevice(serial_number=serial, logger=log)
    try:
        _install(device, appid)
        _get_apk_dm(device, appid)
        _uninstall(device, appid)
        ok = True
    except: # noqa: E722
        log.error(f"oh no, we have a whoopsie for {appid}!")
        log.error(traceback.format_exc())
    if not ok:
        try:
            _uninstall(device, appid)
        except: # noqa: E722
            log.error(f"oh no, major failure is visiting us by failing the second uninstall for {appid}!")
            log.error(traceback.format_exc())
    log.info("finished processing")


def worker_init():
    global serials_queue
    global worker_serial
    worker_serial = serials_queue.get()


def worker_harvest(appid):
    global worker_serial
    global log

    # appid:worker_serial makes sure this logger is uniqe
    lvl = log.level
    log = logging.getLogger(f"{appid}:{worker_serial}")
    log.setLevel(lvl)

    # also output to file. since appid is unique we don't need to worry about concurrent access
    fileHandler = logging.FileHandler(LOGDIR / f"{appid}.log")
    fileHandler.setLevel(lvl)
    fileHandler.setFormatter(logging.Formatter(LOGFMT, style="{"))
    log.addHandler(fileHandler)

    _harvest(worker_serial, appid)


@click.command()
@click.option("--serial", "-s", default=[], multiple=True)
@click.option("--verbose", "-v", default=False, is_flag=True)
@click.argument("appid-csv")
def main(serial, verbose, appid_csv):
    serials = serial # make cli naming consistent

    if verbose:
        log.setLevel(logging.DEBUG)

    log.info("starting harvest")

    num_serials = len(serials)
    if num_serials == 0:
        click.echo("not enough serial nubmers to work with: zero.")
        exit(1)
    log.debug(f"got {num_serials} serials")

    log.info("checking storage server mount and logdir")
    sh.sh("../mount_storage_server.sh")

    LOGDIR.mkdir(parents=True, exist_ok=True)

    log.info("preparing workers")

    global serials_queue
    serials_queue = Queue()
    for serial in serials:
        serials_queue.put(serial)


    appids = []
    with open(appid_csv) as f:
        for line in f.readlines():
            appids.append(line.strip())

    pool = Pool(num_serials, initializer=worker_init)
    log.info("starting harvesting")
    for _ in pool.imap(worker_harvest, appids):
        continue

    log.info("done, have a nice day :)")


if __name__ == "__main__":
    main()



###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################


def old():
# /data/misc/profman/ is where the output of dump-profiles goes
# /data/misc/profiles/cur/0/<package>/primary.prof is, I guess, the current profile for a package? There can be multiple: Check com.google.android.webview , com.android.chrome , com.google.android.gms

# APKs
# Dex Metadata
# profiles-cur
# profiles-ref
# dump-profiles
# snapshot-profiles
    import os
    from datetime import date

    import adbdevice
    import click
    from sh import sshfs


    @click.command()
    @click.argument("serial")
    @click.argument("appids", type=click.File("r"))
    def main(serial, appids):
        # if you run multiple instances, make sure there are no appids in common or stuff will break!
        if not os.path.exists("/mnt/SecPrivSt1/MOUNTED"):
            logging.info("mounting storage server")
            sshfs(
                "-o",
                "idmap=user",
                "playstorescraper@st1.secpriv.tuwien.ac.at:/data/playstorescraper",
                "/mnt/SecPrivSt1",
            )
        # if you do lots of apps, reboot after a thousand or so
        device = adbdevice.Device(serial)
        device.clear_dump_dir()

        folder = str(date.today()) + "-" + serial
        server_path = os.path.join("/mnt/SecPrivSt1/cloud/", folder)

        for raw_appid in appids:
            appid = raw_appid.strip()
            logging.info(f"install/dump/uninstall-ing: {appid}")
            try:
                device.install_single(appid)
                pull_path = os.path.join(server_path, appid)
                os.makedirs(pull_path, exist_ok=True)
                device.dump_apk_dm(appid, pull_path)
            except Exception as e:
                logging.error(f"uncaught exception: {e}")
                continue
            device.uninstall_single(appid)

        logging.info(f"rebooting phone with serial: {serial}")
        device.reboot()
        logging.info("Done.")


    if __name__ == "__main__":
        main()
