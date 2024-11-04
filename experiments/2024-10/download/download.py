#!/usr/bin/env python3

import logging
import traceback
from pathlib import Path
import adbdevice
import click
import sh
import sys

log = logging.getLogger("downloader")
log.setLevel(logging.WARNING)

_ch = logging.StreamHandler()
_ch.setFormatter(
    logging.Formatter(
        "{asctime}|{levelname}|{name}|{message}",
        style="{",
    )
)
log.addHandler(_ch)


def get_only_serial_or_fail():
    lines  = sh.adb("devices", "-l").split('\n')
    if len(lines) != 4:
        log.error("There is more than one or no adb device connected!")
    else:
        return lines[1].split(' ')[0]

def download(appid, serial, output_dir):
    device = adbdevice.AdbDevice(serial_number=serial, logger=log)

    # press home
    device.shell("input keyevent 82") # wake up
    device.shell("input keyevent 82") # unlock

    try:
        device.install(appid)
    except: # noqa: E722
        log.error("Error installing app")
        log.error(traceback.format_exc())
        sys.exit(1)
    
    try:
        device.dump_apk_dm(appid, str(output_dir))
    except: # noqa: E722
        log.error("Error dumping apk and dm file")
        log.error(traceback.format_exc())

    try: 
        device.uninstall_single(appid)
    except: # noqa: E722
        log.error("Error uninstalling app")
        log.error(traceback.format_exc())
    

@click.command()
@click.argument("appid")
@click.option("--serial", "-s", default=None)
@click.option("--output-dir", "-o", default="./", type=click.Path(file_okay=False, writable=True, path_type=Path), help="appid will be appended to this path")
@click.option("--verbose", "-v", default=False, is_flag=True)
def main(appid, serial, output_dir, verbose):
    if verbose:
        log.setLevel(logging.DEBUG)
    
    if not serial:
        serial = get_only_serial_or_fail()

    output_dir = output_dir / appid
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    download(appid, serial, output_dir)
    
if __name__ == "__main__":
    main()