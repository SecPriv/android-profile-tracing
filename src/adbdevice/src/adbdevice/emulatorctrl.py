import logging
import os
import time
from pathlib import Path

import sh
import tomllib

from adbdevice import AdbRootDevice, run_cmd

log = logging.getLogger(__name__)


class BootNotCompletedInTimeException(Exception):
    pass

class EmulatorCTRL:
    def __init__(self, sysimage="system-images;android-34;google_apis;x86_64", name="a34_tracer", device="pixel_6a", port=5560, use_adb_root=True, slot=0, verbose=False):
        if "ANDROID_SDK_HOME" not in os.environ:
            raise NotImplementedError("ANDROID_SDK_HOME not in path, set it up before")
        self.sysimage = sysimage
        self.port = port + slot
        if slot == 0: # gnu parallel slots start at 1, so 0 is an okay default
            self.name = name
        else:
            self.name = f"{name}_{slot}"
        self.device = device
        self._proc_emu = None
        self._ready = False
        self._boot_type = None
        self.use_adb_root = use_adb_root

        if verbose:
            log.setLevel(logging.DEBUG)

    @staticmethod
    def from_config(cfg_file, slot=0, verbose=False):
        """read a toml file containing arguments for creating an emulator"""
        with open(cfg_file, "rb") as f:
            data = tomllib.load(f)
        return EmulatorCTRL(
                sysimage=data["sysimage"],
                name=data["name"],
                device=data["device"],
                port=data["port"],
                use_adb_root=data["use_adb_root"],
                slot=slot,
                verbose=verbose
            )

    def get_device_name(self):
        return f"emulator-{self.port}"

    def recreate(self, force=True):
        """create emulator. if force is true, delete existing one."""
        #if "ANDROID_SDK_HOME" not in os.environ:
        #    env = dict(
        #        ANDROID_SDK_HOME="/home/jakob/android/sdk",
        #        **os.environ)
        #else:
        env = os.environ
        # TODO gosh forking darn help clean up this mess later
        p, _, stdout, stderr = run_cmd("~/android/sdk/cmdline-tools/latest/bin/avdmanager list avd", env=env)
        if p.returncode != 0:
            log.error(f"failed to execute avdmanager (exit {p.returncode})")
            log.error(f"stdout: \n{stdout}")
            log.error(f"stderr: \n{stderr}")
            raise NotImplementedError("failed to list avd")

        if self.name in stdout.decode("utf-8"):
            if force:
                cmd = f"~/android/sdk/cmdline-tools/latest/bin/avdmanager delete avd -n {self.name}"
                log.info("avd found, deleting")
                log.debug(f"..with {cmd}")
                p, _, stdout, stderr = run_cmd(cmd, env=env)
                if p.returncode != 0:
                    log.error(f"failed to execute avdmanager (exit {p.returncode})")
                    log.error(f"stdout: \n{stdout}")
                    log.error(f"stderr: \n{stderr}")
                    raise NotImplementedError("fauled to delete avd")
            else:
                log.info("avd found. not re-creating")
                return

        if force: # because avdmanager is a stupid piece of stellar matter, we check if files exist that would throw an error on re-creation but also don't show up in `list avd`
            avdfolder = Path(f"/home/jakob/android/sdk/.android/avd/{self.name}.avd")
            log.debug(f"checking if {avdfolder} exists")
            if avdfolder.exists():
                log.debug(" .. and deleting it")
                sh.rm("-rf", avdfolder)

        cmd = f"~/android/sdk/cmdline-tools/latest/bin/avdmanager create avd -k '{self.sysimage}' -n {self.name} -d {self.device}"
        log.debug(f"running: {cmd}")
        p, _, stdout, stderr = run_cmd(cmd, env=env)
        if p.returncode != 0:
            log.error(f"failed to execute avdmanager (exit {p.returncode})")
            log.error(f"stdout: \n{stdout}")
            log.error(f"stderr: \n{stderr}")
            raise NotImplementedError("failed to create avd")

    def _startcallback(self, line):
        log.debug(f"EMU: {line.strip()}")
        if "Boot completed" in line:
            self._boot_type = "cold"
            self._ready = True
        elif "Successfully loaded snapshot" in line:
            self._boot_type = "snapshot"
            self._ready = True

    def emulator(self, cmd, _out=None, _bg=True):
        # sh is being silly but no time to fix, TODO rewrite with subprocess
        return sh.sh("-c", f"~/android/sdk/emulator/emulator {cmd}", _out=_out, _bg=_bg)

    def start_and_wait_in_background(self):
        log.debug(f"running something like: ~/android/sdk/emulator/emulator @{self.name} -port {self.port} -feature -Vulkan")
        self._proc_emu = self.emulator(f"@{self.name} -port {self.port} -feature -Vulkan", _bg=True, _out=lambda x: self._startcallback(x)) # for sw rendering, more stable on some devicesa
        log.info("started emulator, waiting for boot complete")
        # maybe use https://cs.android.com/search?q=exec-out ?
        while not self._ready:
            time.sleep(1)
        if self._boot_type == "cold":
            log.info("cold boot complete")
        elif self._boot_type == "snapshot":
            log.info("snapshot boot complete")
        log.info("waiting for up to 30 sec to run adb")
        adbdev = AdbRootDevice(self.get_device_name())
        grace = 30
        while grace > 0:
            time.sleep(1)
            grace -= 1
            try:
                r = adbdev.shell("echo hello there general kenobi")
                if "hello there general kenobi" in r:
                    log.info(" .. done, device can be reached via adb!")
                    break
            except sh.ErrorReturnCode_1:
                pass
        if self._boot_type == "cold":
            log.info("cold boot detected, letting the emulator settle for 30s")
            time.sleep(30)
        if grace <= 0:
            log.critical("boot grace period timed out")
            raise BootNotCompletedInTimeException()

    def shutdown_and_wait(self):
        log.debug("shutting down emulator")
        if self._proc_emu is not None and self._proc_emu.is_alive():
            sh.adb("-s", self.get_device_name(), "emu", "kill")
            log.info("waiting for emulator shutdown")
            self._proc_emu.wait()
            log.info("emulator shut down")
        else:
            log.error("no emulator process")
