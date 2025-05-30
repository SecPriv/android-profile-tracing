import logging
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import sh
from lxml import etree
from sh import adb


def check_device_ok(device_id: str):
    """check if the device is listed in adb and authorized, else raise RunTimeError"""
    output = sh.adb("devices", "-l")
    if device_id not in output:
        raise RuntimeError(f"device-id '{device_id}' not found in adb device list")
    for line in output.splitlines():
        if line.startswith(device_id) and "unauthorized" in line:
            raise RuntimeError(f"device-id '{device_id}' has not authorized us")


class AdbDevice:
    def __init__(self, serial_number: str, logger=None):
        if logger is None:
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.WARNING)
            self.log.addHandler(logging.StreamHandler())
        else:
            self.log = logger

        # don't know the serial number? one of these will tell you:
        # adb get-serialno
        # adb devices

        # codes for different android versions
        # if this grows too big, move it to a json file or something
        aidl_codes = {
            "30": {
                "isInteractive": "16",
                "isKeyguardLocked": "30",
                "freezeRotation": "49",
                "thawRotation": "50",
            },
            "31": {
                "isInteractive": "15",  # https://cs.android.com/android/platform/superproject/+/android-12.0.0_r34:frameworks/base/core/java/android/os/IPowerManager.aidl
                "isKeyguardLocked": "30",  # https://cs.android.com/android/platform/superproject/+/android-12.0.0_r34:frameworks/base/core/java/android/view/IWindowManager.aidl
                "freezeRotation": "49",  # same TODO test
                "thawRotation": "50",  # same
                "__root_required_for_snapshot_profile__": True,
            },
            "34": {
                "isInteractive": "17",  # https://cs.android.com/android/platform/superproject/+/android-14.0.0_r2:frameworks/base/core/java/android/os/IPowerManager.aidl
                "isKeyguardLocked": "31",  # https://cs.android.com/android/platform/superproject/+/android-14.0.0_r2:frameworks/base/core/java/android/view/IWindowManager.aidl
                "freezeRotation": "54",  # same
                "thawRotation": "55",  # same
                "__root_required_for_snapshot_profile__": False,
            },
        }

        # set up bootstrap functions
        self.adb = adb.bake("-s", serial_number)
        self.shell = self.adb.bake("shell")
        version_sdk = self.getprop("ro.build.version.sdk")

        # set up AIDL codes
        if version_sdk in aidl_codes:
            self.aidl_codes = aidl_codes[version_sdk]
        if version_sdk == "35":
            self.log.fatal(f"unsupported SDK version: 35. continuing anyway")
            self.aidl_codes = None
        else:
            # NOTE log/crash/guess?
            error_msg = f"Unsupported SDK version: {version_sdk}."
            self.log.fatal(error_msg)
            sys.exit(error_msg)

        # set up other values
        # TODO make these configurable with keyword args
        self.version_sdk = version_sdk
        self.input_wait = 1  # wait after user interaction
        self.long_wait = 10  # time between checks while waiting
        self.app_time = 5  # how long an app stays open for
        self.padding_y = 200  #
        self.device_dump_path = "/storage/emulated/0/DumpData"
        # ^ TODO have a slash at the end!
        self.host_dump_path = "./daily"  # NOTE not super happy with the name...

        # set up other adb functions
        self.pull = self.adb.bake("pull")
        self.push = self.adb.bake("push")

        # set up other shell functions
        self.am = self.shell.bake("am")
        self.cat = self.shell.bake("cat")
        self.keyevent = self.shell.bake("input", "keyevent")
        self.notification_post = self.shell.bake("cmd", "notification", "post")
        self.pm = self.shell.bake("pm")
        self.service_call = self.shell.bake("service", "call")
        self.swipe = self.shell.bake("input", "touchscreen", "swipe")
        self.tap = self.shell.bake("input", "touchscreen", "tap")
        self.uiautomator_dump = self.adb.bake(
            "exec-out", "uiautomator", "dump", "--compressed", "/dev/stdout"
        )  # should also work with "shell -t", but doesn't.

        # HACK HACK HACK
        if self.getprop("ro.build.id") == "AP1A.240305.019.A1":
            self.aidl_codes["isKeyguardLocked"] = "30"
            # for some godforsaken reason, it is different on that build, and probably on future ones...

    def wait(self, amount=None):
        if amount is None:
            amount = self.input_wait
        time.sleep(amount)

    def clear_dump_dir(self):
        self.shell("mkdir", "-p", self.device_dump_path)
        self.shell("rm", "-rf", self.device_dump_path + "/*")

    def count_installed_packages(self):
        return int(self.shell("pmlistpackages|wc-l").strip())  # TODO

    def dump_apk_dm(self, appid, pull_path):
        # TODO just do it properly...
        if not pull_path.endswith("/"):
            pull_path = pull_path + "/"
        for path in self.pm_path(appid):
            self.pull(path, pull_path)
            try:
                self.pull(path[:-3] + "dm", pull_path)
            except sh.ErrorReturnCode_1:
                self.log.info(f"file not found: {appid}")

    def freezeRotation(self, orientation: str):
        self.service_call(
            "window", self.aidl_codes["freezeRotation"], "i32", orientation
        )
        self.wait()

    def ui_root(self):
        self.wake_up()
        # time.sleep(self.input_wait)
        return etree.fromstring(
            bytes(
                self.uiautomator_dump()
                # .removeprefix("<?xml version='1.0' encoding='UTF-8' standalone='yes'?>")
                .rstrip()
                .removesuffix("UI hierchary dumped to: /dev/stdout"),
                encoding="utf-8",
            )
        )
        # time.sleep(self.input_wait)  # shouldn't really be necessary...

    def getprop(self, prop: str):
        return self.shell("getprop", prop).strip()

    def install(self, appid: str):
        # TODO add optional parameter to look for install_on_* nodes
        self.play_app(appid)

        # TODO rewrite to xpath variables: https://lxml.de/xpathxslt.html
        either = ".//node[@text='{arg}' or @content-desc='{arg}']"
        text = ".//node[@text='{arg}']"
        # content_desc = ".//node[@content-desc='{arg}']"
        unknown_states = 0
        while True:
            page = self.ui_root()  # TODO retry until it is the right screen?
            # the seem to have both now, so either should be fine
            install_nodes = page.xpath(either.format(arg="Install"))
            cancel_nodes = page.xpath(either.format(arg="Cancel"))
            uninstall_nodes = page.xpath(either.format(arg="Uninstall"))
            update_nodes = page.xpath(either.format(arg="Update"))
            # open_play_nodes = page.xpath(".//node[@text='Open' or @text='Play or @content-desc='Open' or @content-desc='Play']")
            play_pass_nodes = page.xpath(
                ".//node[starts-with(@text, 'Try Google Play') and ends-with(@text, 'Pass for 1 month')]"
            )  # there's a weird character in between
            not_now_nodes = page.xpath(text.format(arg="Not now"))
            # install_on_more = page.find(content_desc.format(arg="Install on more devices"))
            # install_on_phone = page.find(text.format(arg="Install on phone. More devices available."))
            if play_pass_nodes != []:
                self.log.info(f"Play Pass ad overlaying: {appid}")
                # one of those annoying "tRy gOoGlE PlAy pAsS FoR 1 MoNtH" ads
                self.tap_node(not_now_nodes[0])
                self.wait()
                continue
            elif cancel_nodes != []:
                self.log.debug(f"Waiting for installation: {appid}")
                # installation in progress
                self.wait()  # TODO define a proper amount of time...
                continue
            elif update_nodes != []:
                # installed, but not up to date
                self.log.info(f"Updating app: {appid}")
                self.tap_node(update_nodes[0])
                continue
            elif uninstall_nodes != []:
                self.log.info(f"App installed: {appid}")
                # (already) installed and up to date
                # this could probably also be done via the package manager
                return
            elif install_nodes != []:
                self.log.info(f"Installing app: {appid}")
                # not installed
                self.tap_node(install_nodes[0])
                continue
                # we have to handle this case later than the others, because if there are multiple devices on the Google account,
                # and another device doesn't have the app, an Install button will be shown - for that other device!
            else:
                unknown_states += 1
                if unknown_states > 4:
                    self.log.error(f"Could not install app: {appid}")
                    # TODO attempt recovery?
                    return

    # def install_multiple(self, appids):
    #    for appid in appids:
    #        self.install_single_nowait(appid)
    #    self.update_and_wait()

    # def install_single(self, appid: str):
    #    self.install_single_nowait(appid)
    #    self.update_and_wait()  # TODO replace with proper wait...

    # def install_single_nowait(self, appid: str):
    #    self.play_app(appid)
    #    self.tap_installupdate_button(appid)
    #    self.wait()

    def installed(self, appid: str):
        # bit of a hacky way, but that's what adbkit does...
        return self.pm_path(appid) != []

    def isInteractive(self):
        return _boolparcel(self.service_call("power", self.aidl_codes["isInteractive"]))

    def isKeyguardLocked(self):
        return _boolparcel(
            self.service_call("window", self.aidl_codes["isKeyguardLocked"])
        )

    def keyevent_power(self):
        self.keyevent("26")
        self.wait()

    def keyevent_home(self):
        self.keyevent("3")
        self.wait()

    def launch_multiple(self, appids):
        for appid in appids:
            self.launch_single(appid)

    def launch_single(self, appid):
        if self.installed(appid):
            try:
                self.monkey(appid, "1")
                self.wait(self.app_time)
            except sh.ErrorReturnCode_252:
                # ** No activities found to run, monkey aborted.
                self.log.warning(f"could not launch activity for appid: {appid}")
        self.keyevent_home()

    def notification(self, tag: str, text: str):
        # tag is basically the topic, text is the actual message
        # if you send the same tag in a following notification, it replaces the earlier one
        self.notification_post(tag, f'"{text}"')

    def play_app(self, appid: str):
        self.wake_up()
        self.am(
            "start-activity",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            f"http://play.google.com/store/apps/details?id={appid}",
        )
        self.wait(3)  # TODO proper "are we there yet" implementation

    def play_downloads(self):
        # play store home page
        self.play_home()
        # find account button
        account_button_candidates = self.ui_root().findall(
            ".//node[@content-desc!='']"
        )  # TODO rewrite with a single XPath, now that there is an actual lib available...
        account_button = None
        for candidate in account_button_candidates:
            if candidate.get("content-desc").endswith("Account and settings."):
                account_button = candidate
                break
        if account_button is not None:
            self.tap_node(account_button)
            self.wait(2)  # TODO this really should not be necessary. yet here we are.
        else:
            error_msg = "no account button found!"
            self.log.error(error_msg)
            sys.exit(error_msg)
        # find "Manage apps & devices"
        root = self.ui_root()
        manage_button = root.find(".//node[@text='Manage apps & device']")
        if manage_button is None:
            manage_button = root.find(".//node[@text='My apps & games']")
        # ^ FML: this didn't work with 'Manage apps &amp; device' even though that is what is in the xml...
        self.tap_node(manage_button)
        # find "See details"
        details_root = self.ui_root()
        details_button = details_root.find(".//node[@text='See details']")
        if details_button is None:
            details_button = details_root.find(".//node[@text='All apps up to date']")
            # ^ could probably be some "or" construction
        self.tap_node(details_button)

    def play_home(self):
        self.wake_up()
        self.am(
            "start-activity",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            "http://play.google.com/store",
        )
        self.wait()

    def pm_path(self, appid: str):
        try:
            packages = self.pm("path", appid)
        except sh.ErrorReturnCode_1:
            self.log.info(f"no paths found for: {appid}")
            return []
        return _unpackage(packages)

    def reboot(self):
        self.shell("reboot")

    def rm(self, *args):
        try:
            self.shell("rm", *args)
        except sh.ErrorReturnCode_1 as e:
            self.log.warning(f"rm failed: {e}")

    def screen_dimensions(self):
        # could probably also be done with some service calls, but eh
        m = re.match(r"Physical size: (?P<x>\d*)x(?P<y>\d*)", self.shell("wm", "size"))
        return (int(m.group("x")), int(m.group("y")))

    def swipe_unlock(self):
        (x, y) = self.screen_dimensions()
        x_half = str(x / 2)
        y_lower = str(y - self.padding_y)
        y_upper = str(self.padding_y)
        self.swipe(x_half, y_lower, x_half, y_upper)
        self.wait()

    def tap_node(self, node):
        (x1, y1, x2, y2) = _unbound(node.get("bounds"))
        self.tap((int(x1) + int(x2)) // 2, (int(y1) + int(y2)) // 2)
        self.wait()

    # def tap_installupdate_button(self, appid: str):
    #     # amogh's tool just hard-codes a tap location, but since that location is not only device-dependent but also influenced by stuff like the length of the name of an app, this is more reliable and doesn't need per-device configuration!
    #     root = self.ui_root()
    #     install_button = root.find(".//node[@content-desc='Install']")
    #     uninstall_button = root.find(".//node[@content-desc='Uninstall']")
    #     update_button = root.find(".//node[@content-desc='Update']")
    #     open_button = root.find(".//node[@content-desc='Open']")
    #     if open_button is not None:
    #         print(f"already up to date: {appid}")
    #     elif update_button is not None:
    #         print(f"updating: {appid}")
    #         self.tap_node(update_button)
    #     elif uninstall_button is not None:
    #         print(f"already up to date: {appid}")
    #     elif install_button is not None:
    #         # now, why isn't this earlier? if the app is already installed, there can still be an install button, but it'll be for another device!
    #         print(f"installing: {appid}")
    #         self.tap_node(install_button)
    #     else:
    #         print(f"something went wrong: {appid}")
    #         return

    def uninstall_multiple(self, appids):
        for appid in appids:
            self.uninstall_single(appid)

    def uninstall_single(self, appid):
        try:
            self.pm("uninstall", appid)
        except sh.ErrorReturnCode_1:
            # Failure [DELETE_FAILED_INTERNAL_ERROR]
            # aka "wasn't even installed"
            self.log.info(f"app not installed: {appid}")

    def update_and_wait(self):
        self.play_downloads()
        all_your_apps_are_up_to_date = self.ui_root().find(
            ".//node[@text='All your apps are up to date']"
        )
        while all_your_apps_are_up_to_date is None:
            self.wake_up()
            update_all = self.ui_root().find(".//node[@text='Update all']")
            if update_all is not None:
                self.tap_node(update_all)
            self.wait(self.long_wait)
            all_your_apps_are_up_to_date = self.ui_root().find(
                ".//node[@text='All your apps are up to date']"
            )
        self.log.info("everything up to date")
        self.keyevent_home()

    def wake_up(self):
        if not self.isInteractive():
            self.keyevent_power()
        if self.isKeyguardLocked():
            self.swipe_unlock()
        self.freezeRotation("0")


# abstract class, don't use!
# (can't be asked to do proper abstract classing right now)
class AbstractRootDevice(AdbDevice):
    def __init__(self, serial_number: str):
        super().__init__(serial_number)
        # could be easily created on a non-root device, it just doesn't really make sense
        self.device_push_path = "/storage/emulated/0/ProfmanData/"
        self.apk_push_path = self.device_push_path + "base.apk"
        self.baseline_name = "assets/dexopt/baseline.prof"
        self.baseline_path = self.device_push_path + self.baseline_name
        self.dm_push_path = self.device_push_path + "base.dm"
        self.cloud_name = "primary.prof"
        self.cloud_path = self.device_push_path + self.cloud_name

    def clear_push_dir(self):
        self.shell("mkdir", "-p", self.device_push_path)
        self.shell("rm", "-rf", self.device_push_path + "/*")

    def profman_profile(self, profile):
        path = self.device_push_path + "profile.prof"
        self.clear_push_dir()
        self.push(profile, path)
        return self.root_shell("profman", "--dump-only", f"--profile-file={path}")

    def profman_baseline(self, host_apk):
        self.clear_push_dir()
        self.push(host_apk, self.apk_push_path)
        self.shell(
            "unzip",
            "-d",
            self.device_push_path,
            self.apk_push_path,
            self.baseline_name,
        )
        return self.profman(self.baseline_path, self.apk_push_path)

    def profman_cloud(self, host_apk, host_dm):
        self.clear_push_dir()
        self.push(host_apk, self.apk_push_path)
        self.push(host_dm, self.dm_push_path)
        self.shell(
            "unzip", "-d", self.device_push_path, self.dm_push_path, self.cloud_name
        )
        return self.profman(self.cloud_path, self.apk_push_path)

    def snapshot_profile(self, *args):
        try:
            self.root_shell("pm", "snapshot-profile", *args)
        except (
            sh.ErrorReturnCode_1,
            sh.ErrorReturnCode_2,
            sh.ErrorReturnCode_255,
        ) as e:
            self.log.error(f"snapshot_profile failed: {e}")

    def profman(self, profile, apk):
        return self.root_shell(
            "profman", "--dump-only", f"--profile-file={profile}", f"--apk={apk}"
        )

    # TODO su_try, dump_everything ?


class SuRootDevice(AbstractRootDevice):
    def __init__(self, serial_number: str):
        super().__init__(serial_number)
        self.root_shell = self.shell.bake("su", "-c")


class AdbRootDevice(AbstractRootDevice):
    def __init__(self, serial_number: str):
        super().__init__(serial_number)
        self.adb("root")  # just do everything in a root shell
        self.root_shell = self.shell


# UTIL FUNCTIONS


def _unparcel(parcel: str):  # extracts the bytes in a Parcel
    # assumes a specific amount of dots, which is not true for longer parcels!
    # should probably fix up the regex parser...

    # m = re.match("Result: Parcel\((\d{8} )*  '........'\)", parcel)
    # return m.groups()
    return [int(x, 16) for x in parcel[15:-15].split(" ")]


def _boolparcel(parcel: str):  # parses a boolean Parcel
    return _unparcel(parcel)[1] != 0


def _unbound(bounds: str):
    # extracts the values from a bounds attribute as they appear in the uiautomator xml
    # re.match("\[(?P<x1>\d*),(?P<y1>\d*)\]\[(?P<x2>\d*),(?P<y2>\d*)\]", bounds)
    return re.match(r"\[(\d*),(\d*)\]\[(\d*),(\d*)\]", bounds).groups()


def _unpackage(packages):
    # could also be regexed
    return [x.removeprefix("package:") for x in packages.splitlines()]


# def unpath(path: str):
#     return path.split("/")[-1][:]


# def unsplitfile(splitfile: str):
#     return splitfile[6:-4]


def run_cmd(
    cmd,
    shell: bool = True,
    timeout: int | None = None,
    env: dict | None = None,
    cwd: str | Path | None = None,
) -> tuple[subprocess.Popen, bool, str, str]:
    """
    Run a cmd in a subshell.

    Popen is needed becasue many tools we call spawn their own threads and timing out on subprocess.run does not terminate them properly.

    return (p, timed_out, stdout, stderr)
     - p is the process object
     - timed_out is a boolean
     - stdout and stderr are the results from .communicate()
    """
    timed_out = True
    stdout = None
    stderr = None
    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=shell,
            start_new_session=True,
            cwd=cwd,
        )
        stdout, stderr = p.communicate(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)  # terminate the process group
        stdout, stderr = (
            p.communicate()
        )  # grab stdout and stderr so far as the prior threw an exception
    return p, timed_out, stdout, stderr
