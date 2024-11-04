import contextlib
import glob
import logging
import pickle
import re
import signal
import sys
import time
import traceback
from math import ceil
from pathlib import Path

import click
import sh
from adbdevice import AdbRootDevice, SuRootDevice, check_device_ok
from adbdevice.emulatorctrl import EmulatorCTRL

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

_ch = logging.StreamHandler()
_ch.setFormatter(
    logging.Formatter(
        "{asctime}|{levelname}|{name}|{message}",
        style="{",
    )
)

# adds the handler to the global variable: log
log.addHandler(_ch)

TRACE_GROUP_NAME="sonoftroya"

# supported tools:
# to implement a new one add a function to call it in Tracer.run_tool()
_SUPPORTED_TOOLS=["time", "monkey", "droidbot", "fastbot"]

# default settings
# ONANDR means it refers to a location on the android system
# ONHOST means it refers to a location on the system running aproftracer
_ONANDR_TMPDIR=Path("/data/local/tmp/tracer/")
_ONHOST_DEFAULT_RESULT_DIR=Path("./_results/")
_TRACEPOINTS_SH_FNAME="tracepoints.sh"
_RAW_OUTPUT_FNAME="raw_output.txt"

_ONANDR_WRITEABLE_DIR=Path("/storage/emulated/0/Download/")

_TIMEOUT_FOR_PROBE_SETUP=300 # uprobe events are fast, but not that fast.
_DEFAULT_MAX_PROBES=30_000 # TODO still needed? yes


class Tracer:
    def __init__(
                self,
                apkid,

                device_id,
                use_adb_root=False,
                apks_dm_dir=None,
                android_tmpdir=_ONANDR_TMPDIR,
                host_result_dir=_ONHOST_DEFAULT_RESULT_DIR,

                max_probes=_DEFAULT_MAX_PROBES,
                buffer_size_kb=None,
                buffer_percent=None,

                force_wifi=None,

                verbose=False,
            ):
        self.apkid = apkid

        # set up the adbdevice
        self.device_id = device_id
        check_device_ok(device_id)
        self._use_adb_root = use_adb_root
        if use_adb_root:
            self.adbdev = AdbRootDevice(device_id)
        else:
            self.adbdev = SuRootDevice(device_id)

        if verbose:
            self.adbdev.log.setLevel(logging.DEBUG)
        self._verbose = verbose

        log.info("connected to device")

        # check eBPF capabilities
        self.check_and_enable_tracing(buffer_size_kb, buffer_percent)

        if force_wifi:
            self.check_or_connect_to_wifi(force_wifi)

        self.apks_dm_dir = Path(apks_dm_dir) if apks_dm_dir else None
        self.host_res_dir = host_result_dir / apkid
        if not self.host_res_dir.exists():
            log.debug(f"crearing result dir {self.host_res_dir}")
            self.host_res_dir.mkdir(parents=True, exist_ok=True)
        self._host_res_tmpdir = self.host_res_dir / "_tmp"
        if not self._host_res_tmpdir.exists():
            log.debug(f"crearing result tmpdir {self.host_res_dir}")
            self._host_res_tmpdir.mkdir(parents=True, exist_ok=True)
        self.host_raw_output_path = self._host_res_tmpdir / _RAW_OUTPUT_FNAME
        self.host_output_path = self.host_res_dir / "result.pickle"
        self.host_tracepoinsts_sh = self._host_res_tmpdir / _TRACEPOINTS_SH_FNAME

        # set up paths on device
        self.andro_tmpdir = android_tmpdir # where the tracer and other things live on device
        self.adbdev.root_shell(f"mkdir -p {self.andro_tmpdir}")
        self.andro_apkdir = self.andro_tmpdir / apkid # dir to keep apk files and tmp files for this apkid
        self.adbdev.root_shell(f"mkdir -p {self.andro_apkdir}")
        # helpers for parsing
        self.andro_prim_prof = self.andro_apkdir / 'primary.prof'
        self.andro_prim_profdump = self.andro_apkdir / 'primary.profdump'
        self.andro_base_oatdump = self.andro_apkdir / 'base.oatdump'
        self.andro_tracepoints_sh = self.andro_apkdir / _TRACEPOINTS_SH_FNAME
        self.andro_raw_output_path = self.andro_apkdir / _RAW_OUTPUT_FNAME

        self.host_prim_profdump_path = self._host_res_tmpdir / self.andro_prim_profdump.name
        self.host_base_oatdump_path = self._host_res_tmpdir / self.andro_base_oatdump.name

        # these are dynamic and depend on the data dir for the app, see the @properties later
        self._andro_dm_path = None
        self._andro_odex_path = None
        self._oatdata_offset = None

        self.profile_info = None # see read_profdump_info
        self.offsets_info = None # see read_oatdump_info
        self.trace_info = None # see _create_tracepoints_sh

        # collecting the uprobes
        self._raw_hit_uprobes = []

        self.num_probes_to_attach = 0
        self.max_probes = max_probes

        log.info("device set up")

    def check_and_enable_tracing(self, buffer_size_kb, buffer_percent):
        """test the kernel config, enable tracing, and mount the debugfs if needed."""
        kconf = self.adbdev.shell("zcat /proc/config.gz")
        for setting in [
                "CONFIG_BPF=y",
                "CONFIG_BPF_SYSCALL=y",
                "CONFIG_UPROBES=y",
                "CONFIG_UPROBE_EVENTS=y"]:
            assert(setting in kconf)
        # self.adbdev.root_shell("echo '1' > /sys/kernel/tracing/tracing_on")
        # mount debugfs if not mounted
        if self._use_adb_root:
            self.adbdev.root_shell("if [ $(cat /proc/self/mounts | grep -c sys/kernel/debug) -eq 0 ]; then mount -t debugfs debugfs /sys/kernel/debug; fi")
        else:
            # why do we need to escape the semicolons? idk, drop me a line if you find out.
            self.adbdev.root_shell("if [ $(cat /proc/self/mounts | grep -c sys/kernel/debug) -eq 0 ]\; then mount -t debugfs debugfs /sys/kernel/debug\; fi") # noqa: W605
        log.info("kernel seems ok!")
        if buffer_size_kb:
            self.adbdev.root_shell(f"echo {int(buffer_size_kb)} > /sys/kernel/tracing/buffer_size_kb")
            log.debug(f"set uprobe buffer size to {int(buffer_size_kb)}")
        if buffer_percent:
            log.error("Setting buffer_percent not supported for now due to permission issues. rest should work tho.")
            # FIXME setting the buffer_percent like this gets us a permission error :(
        #    self.adbdev.root_shell(f"echo {int(buffer_percent)} > /sys/kernel/tracing/buffer_percent")
        #    log.debug(f"set uprobe buffer percent to {int(buffer_percent)}")

    def check_or_connect_to_wifi(self, conn_string):
        log.info("making sure wifi is enabled")

        def get_ssid(conn_string):
            r = []
            for s in conn_string.split(' '):
                if s in "open|owe|wpa2|wpa3|wep".split('|'):
                    break
                r.append(s)
            return ' '.join(r)

        def is_wifi_enabled():
            wifi_status = self.adbdev.root_shell("cmd -w wifi status")
            return "Wifi is disabled" in wifi_status

        def is_wifi_connected(ssid):
            wifi_status = self.adbdev.root_shell("cmd -w wifi status")
            return f'Wifi is connected to "{ssid}"' in wifi_status

        ssid = get_ssid(conn_string)
        log.debug(f"checking for ssid: {ssid}")

        if is_wifi_connected(ssid):
            return # we are connected
        elif is_wifi_enabled():
            self.adbdev.shell("svc wifi enable")
            timeout = 10
            while (timeout > 0):
                time.sleep(1)
                if is_wifi_enabled():
                    break
                timeout-=1

        # we can't connect to a saved network from the cli,
        # see `adb shell su -c cmd -w wifi help`
        # so we need to use the full connection string
        self.adbdev.root_shell(f"cmd -w wifi connect-network {conn_string}")
        timeout = 10
        while (timeout > 0):
            time.sleep(1)
            if is_wifi_connected(ssid):
                return # success
            timeout-=1

        # if we are here connection timed out
        raise NotImplementedError("Tried to connect to wifi but it was not successful.")

    def uninstall_and_log_errors(self):
        """try to uninstall app and ignore errors, mainly due the app not being installed."""
        log.info(f"uninstalling {self.apkid}")
        try:
            # try uninstall and ignore failure
            self.adbdev.shell(f"pm uninstall {self.apkid}")
        except sh.ErrorReturnCode_1:
            log.warning(f"error while uninstalling {self.apkid}! (not installed?)")

    def install_and_compile_from_path(self, compile_all_aot=False):
        """
        install base apk and split apks and dm file from directory containing them all with the following steps:
        - collect apk and dm filepaths
        - run adb install-multiple
        we assume <apks_dm_dir>/ has all necessary apks and a .dm file
        """
        if not self.apks_dm_dir:
            raise NotImplementedError("cant install from files if no filepaths given")
        log.info(f"installing {self.apkid} from apk files")

        files_to_install = []
        apk_files = glob.glob(f"{self.apks_dm_dir!s}/*.apk")
        files_to_install.extend(apk_files)
        dm_file = list(glob.glob(f"{self.apks_dm_dir!s}/*.dm"))
        # TODO we assume there is just one dm file, but splits could have their own
        if len(dm_file) != 1:
            log.warning(f"expected one dm file but got {len(dm_file)}: {dm_file}")
        files_to_install.extend(dm_file)

        self.adbdev.adb("install-multiple", *files_to_install)

        if compile_all_aot:
            log.info("AOT compiling everyting")
            # instead of speed-profile, compile everything AOT
            # rest mimics fresh install instructions
            self.adbdev.root_shell(f"pm compile -r install -m everything -f -v --full {self.apkid}")
            log.info("AOT compilation successfull!")

        log.debug("installation successfull!")

        # Before, it was necessary to:
        # - temporarily push the files to _WRITABLE_DIR
        # - copy them to ANDROID_TMPDIR/<appid>/
        # - install the apk files
        # - copy the dm file to the <pm path>
        # - run dexopt to trigger profile-based compilation.

        #self.adbdev.root_shell(f"pm install {self.andro_apkdir}/*.apk")

        # put base.dm at correct location
        #log.debug("copying base.dm")
        #paths = self.adbdev.pm_path(self.apkid)
        #app_data_dir = Path(paths[0]).parent # if this is empty install failed
        # TODO we assume there is just one dm file, but splits could have their own
        # however, only a single app used split files with dms, and that was a preinstalled app, so we are leaving this for the future
        #self.adbdev.root_shell(f"cp {self.andro_apkdir / 'base.dm'} {app_data_dir}")
        #self.adbdev.root_shell(f"chown system:system {app_data_dir / 'base.dm'}") # just to be sure make permissios match other apps
        #self.adbdev.root_shell(f"chmod o+r {app_data_dir / 'base.dm'}")

        # run compilation like play store install would do it
        #log.info("compiling app with speed-profile")
        #self.adbdev.root_shell(f"pm compile -r install -m speed-profile -f --reset -v --full {self.apkid}")

    @property
    def andro_odex_path(self):
        """get odex path on emulator for apkid."""
        if not self._andro_odex_path:
            p = self.adbdev.root_shell(f"pm dump {self.apkid} | grep 'codePath' | xargs").strip()[9:]
            self._andro_odex_path = self.adbdev.root_shell(f"find {p} -name '*.odex' 2> /dev/null | head -n 1").strip()
            log.info(f"found oat at: {self._andro_odex_path}")
        return self._andro_odex_path

    @property
    def oatdata_offset(self):
        """get oatdata offset to calculate real function offsets within odex"""
        if not self._oatdata_offset:
            readelf = self.adbdev.root_shell(f"readelf -s {self.andro_odex_path}")
            for line in readelf.split('\n'):
                if line.endswith('oatdata'):
                    self._oatdata_offset = int(line.split()[1], 16)
            log.info(f"found oatdata offset at: {self._oatdata_offset:x}")
        return self._oatdata_offset

    @property
    def andro_dm_path(self):
        """get dm path"""
        if not self._andro_dm_path:
            pm_path = self.adbdev.pm_path(self.apkid)
            if len(pm_path) == 0:
                raise RuntimeError("pm path empty!")
            if not pm_path[0].endswith("base.apk"):
                raise RuntimeError(f"pm path unexpected: {pm_path[0]}")
            self._andro_dm_path = Path(pm_path[0]).with_suffix(".dm")
        return self._andro_dm_path

    def prepare_tracepoints_sh(self, code_coverage, also_startup_poststartup):
        """
        - create info.json containing offsets of methods in primary.prof
        - create tracepoints.sh and push it to device
        """
        if code_coverage:
            log.warning("code coverage is experimental and times out if app has many (>30k methods)")

        self._prepare_profile_and_oatdump()

        self.profile_info, self.offsets_info = Tracer.generate_profile_and_offsets_info(
                self.host_prim_profdump_path,
                self.host_base_oatdump_path,
                self.oatdata_offset,
                code_coverage)

        self._create_tracepoints_sh(also_startup_poststartup, code_coverage)
        self.push_thru_writable(self.host_tracepoinsts_sh, self.andro_tracepoints_sh)
        self.adbdev.root_shell(f"chmod +x {self.andro_tracepoints_sh}")

    def _prepare_profile_and_oatdump(self):
        """assumes dm file available at install directory, not tempdir. creates and pulls primary.prof, profdump, and oatdump"""
        log.debug("preparing prof, profdump, and oatdump")

        # extract primary prof from base_dm
        # -o to overwrite existing files
        self.adbdev.root_shell(f"unzip -o {self.andro_dm_path} primary.prof -d {self.andro_apkdir}")
        self.adbdev.pull(self.andro_prim_prof, (self._host_res_tmpdir / self.andro_prim_prof.name))
        log.debug("unzipped dm and pulled primary.prof")

        # create readable profdump file
        # because pErMiSsIoNs, the following does not work:
        # self.adbdev.root_shell(f"profman --dump-only --profile-file={self.andro_prim_prof} > {self.andro_prim_profdump}")
        # instead we need to dump to a writeable dir and then mv it where we want it
        tmpfile = _ONANDR_WRITEABLE_DIR / self.andro_prim_profdump.name
        self.adbdev.root_shell(f"profman --dump-only --profile-file={self.andro_prim_prof} > {tmpfile}")
        self.adbdev.root_shell(f"mv {tmpfile} {self.andro_prim_profdump}")
        self.adbdev.root_shell(f"chmod o+r {self.andro_prim_profdump}")
        self.adbdev.pull(self.andro_prim_profdump, self.host_prim_profdump_path)
        log.debug("created and pulled profdump")

        # create oatdump
        # also because permissions >_< see above
        # self.adbdev.root_shell(f"oatdump --oat-file={self.andro_odex_path} --no-disassemble > {self.andro_base_oatdump}")
        tmpfile = _ONANDR_WRITEABLE_DIR / self.andro_base_oatdump.name
        self.adbdev.root_shell(f"oatdump --oat-file={self.andro_odex_path} --no-disassemble > {tmpfile}")
        self.adbdev.root_shell(f"mv {tmpfile} {self.andro_base_oatdump}")
        self.adbdev.root_shell(f"chmod o+r {self.andro_base_oatdump}")
        self.adbdev.pull(self.andro_base_oatdump, self.host_base_oatdump_path)
        log.debug("created and pulled oatdump")

    @staticmethod
    def generate_profile_and_offsets_info(profdump_path, oatdump_path, oatdata_offset, code_coverage):
        """
        profile_info contains a parsed profile mapped based on startup/poststartup/hot methods

        offsets_info contains the methods we are interested in, or all, if code_coverage is set to true.
        """
        profile_info = Tracer.read_profdump_info(profdump_path)
        oatdump_info = Tracer.read_oatdump_info(profile_info, oatdump_path, oatdata_offset, code_coverage)
        return profile_info, oatdump_info

    @staticmethod
    def read_profdump_info(profdump_path):
        profile_info = {
                'startup':{},
                'poststartup':{},
                'hot':{}
            }
        with open(profdump_path) as f:
            _unknown_version = True
            _current_dex = None
            for line in f.readlines():
                if "ProfileInfo [015]" in line:
                    _unknown_version = False
                if '[index=' in line:
                    _current_dex = line.split()[0].strip()
                elif 'hot methods:' in line.strip():
                    methods = [int(x.split('[')[0]) for x in line.strip().split()[2:]] # hot methods have more info "36353[],"
                    profile_info['hot'][_current_dex] = set(methods)
                elif 'post startup methods' in line.strip():
                    methods = [int(x.split(',')[0]) for x in line.strip().split()[3:]] # more words
                    profile_info['startup'][_current_dex] = set(methods)
                elif 'startup methods' in line.strip():
                    methods = [int(x.split(',')[0]) for x in line.strip().split()[2:]]
                    profile_info['poststartup'][_current_dex] = set(methods)
            if _unknown_version:
                raise NotImplementedError("got a profile dump in an unknown version, compatibility not certain.")
        log.debug("parsed profman output")
        return profile_info

    @staticmethod
    def read_oatdump_info(profile_info, oatdump_path, oatdata_offset, include_nonprofile=False):

        oatdump_info = {'hot':[], 'startup':[], 'poststartup':[], 'other':[]}

        # important: oatdump sometimes has non-utf-8 chars :(
        with open(oatdump_path, errors='backslashreplace') as f:
            cur_loc = None # dex file location
            cur_method_idx = None # method id of dex method
            cur_offset = None # offset in binary (before adding oatdata offset)
            cur_method_name = None # always on same line as method idx

            _magic_check = 0
            for line in f.readlines():
                if _magic_check == 0 and line.startswith("MAGIC:"):
                    _magic_check = 1
                elif _magic_check == 1 and line.startswith("oat"):
                    _magic_check = 2
                elif _magic_check == 2 and line.startswith("236"):
                    _magic_check = 3

                # each dex is seperate and provided as /path/to/base.apk[!classesN.dex]
                if line.startswith("location:"):
                    cur_loc = line.split()[1].split('/')[-1].strip()
                    # check early if location is in the hotmethods
                    if cur_loc not in profile_info['hot'] and cur_loc not in profile_info['startup'] and cur_loc not in profile_info['poststartup']:
                        # TODO sometimes it is clases.dex instead base.apk, maybe one day we can errorhandle this better, for now raise an issue.
                        raise NotImplementedError(f"dex file id '{cur_loc}' not in method keys!(hot: {profile_info['hot'].keys()}, startup: {profile_info['startup'].keys()}, poststartup: {profile_info['poststartup'].keys()}")

                    cur_method_idx = None
                    cur_offset = None
                    log.info(f" - reading oatdump at: {cur_loc}") # to check progress

                # if we are not in a method, we scan for methods
                elif not cur_method_idx and (m := re.match(r"  [0-9]+: (.*)( \(dex_method_idx=)([0-9]+).*", line)):
                    cur_method_idx = int(m.group(3))
                    # check if it's an index we actually care about
                    if not include_nonprofile and cur_method_idx not in profile_info['hot'][cur_loc] and cur_method_idx not in profile_info['startup'][cur_loc] and cur_method_idx not in profile_info['poststartup'][cur_loc]:
                        cur_method_idx = None
                        continue
                    cur_method_name = m.group(1)
                    cur_offset = None
                    #log.info(line)
                    #log.info(cur_loc, cur_method_idx, cur_method_name)

                #if we are in a method and don't have the binary offset, we scan for the latter
                elif cur_method_idx and not cur_offset and (m := re.match(r"    CODE: \(code_offset=0x([0-9a-f]+) ", line)):
                    cur_offset = m.group(1)
                    #log.info(line)
                    #log.info(cur_offset)

                    __loc = str(cur_loc)
                    __mi = int(cur_method_idx)
                    __off = f"0x{cur_offset}"
                    __odo = f"0x{oatdata_offset:x}"
                    __cof = (int(cur_offset, 16)+oatdata_offset)
                    __nam = str(cur_method_name)

                    # str(dex-location);int(method_idx);hexstr(offset);hexstr(oatdata_offset);int(computed_offset);str(name)
                    __dat = (__loc, __mi, __off, __odo, __cof, __nam)

                    _in_prof = False
                    # can be optimized as it can appear in multiple sets, but it makes accessing it later easier for differentiating those cases
                    if cur_method_idx in profile_info['hot'][cur_loc]:
                        oatdump_info['hot'].append(__dat)
                        _in_prof = True
                    if cur_method_idx in profile_info['startup'][cur_loc]:
                        oatdump_info['startup'].append(__dat)
                        _in_prof = True
                    if cur_method_idx in profile_info['poststartup'][cur_loc]:
                        oatdump_info['poststartup'].append(__dat)
                        _in_prof = True

                    if not _in_prof:
                        oatdump_info['other'].append(__dat)

                    cur_method_idx = None

            if _magic_check != 3:
                raise NotImplementedError("oatdump magic does not match expected value!")

        log.debug("oatdump parsed for offsets")
        return oatdump_info

    def push_thru_writable(self, host_path, andro_path):
        """because #reasons, some dirs cant be pushed to directly"""
        self.adbdev.push(host_path, (_ONANDR_WRITEABLE_DIR / andro_path.name))
        self.adbdev.root_shell(f"mv {(_ONANDR_WRITEABLE_DIR / andro_path.name)} {andro_path}")

    def _create_tracepoints_sh(self,also_startup_poststartup, code_coverage):
        """create a .sh file that contains instructions to set up uprobes"""
        if self.max_probes == 0:
            self.max_probes = len(self.offsets_info)
        elif also_startup_poststartup:
            log.warning("setting limit to probes but including startup and poststartup might cut them off, no distributed selection is performed!")

        trace_info = [] # array of tracepoints set, using oatdata offsets

        offsets = []
        offsets.extend(self.offsets_info['hot'])
        if also_startup_poststartup or code_coverage:
            log.debug("also using startup and poststartup methods")
            offsets.extend(self.offsets_info['startup'])
            offsets.extend(self.offsets_info['poststartup'])
        if code_coverage:
            log.debug("also using non-profile methods")
            offsets.extend(self.offsets_info['other'])

        with open(self.host_tracepoinsts_sh, "w") as outfile:
            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] starting!'\n")
            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] disabling tracing'\n")
            outfile.write("echo 0 > /sys/kernel/tracing/tracing_on;\n")
            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] disabling tracing events and flushing output'\n")
            outfile.write("echo 0 > /sys/kernel/tracing/events/enable;\n")
            # FIXME empty pipe?
            # TODO echo > uprobe_events
            outfile.write("echo > /sys/kernel/tracing/trace;\n")
            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] starting setup of uprobes'\n")

            counter = 0
            _unique_offsets = set()
            for _, _, offset, _, computed_offset, _ in offsets:
                # sometimes functions are removed, leaving no offset to work with
                if int(offset, 16) == 0:
                    continue
                # sometimes multiple functions are mapped to the same offset, we only take it once
                if computed_offset in _unique_offsets:
                    continue
                else:
                    _unique_offsets.add(computed_offset)

                counter += 1
                if counter >= self.max_probes:
                    log.warning(f"max probes ({self.max_probes}) reached, not tracing more")
                    continue

                if counter % 1000 == 0 and counter > 0:
                    outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] set up {counter} probes'\n")
                computed_offset = hex(computed_offset)
                outfile.write(
                    f"echo 'p:{TRACE_GROUP_NAME}/event{computed_offset} {self.andro_odex_path}:{computed_offset}' >> /sys/kernel/tracing/uprobe_events;\n"
                )
                trace_info.append(computed_offset)
                # print(f"echo 'disable_event:{group}:event{counter}' > events/{group}/event{counter}/trigger") (doesn't show anything in the trace)
                # print(f"echo 'traceoff:1' > events/{group}/event{counter}/trigger") (shows one event)
                # print(f"echo 'disable_event:{group}:event{counter}:2 if nr_rq > 1' > events/{group}/event{counter}/trigger") (shows nothing)
                # these all seem to not work as intended

            log.info(f"tracing {len(trace_info)}/{counter} methods")

            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] {counter} uprobes set up, starting tracing group {TRACE_GROUP_NAME}'\n")
            outfile.write(f"echo 1 > /sys/kernel/tracing/events/{TRACE_GROUP_NAME}/enable;\n")
            outfile.write(f"echo '[{_TRACEPOINTS_SH_FNAME}] tracing set up, ready for on and app start'\n")
            outfile.write(f'tail -f -n +1 /sys/kernel/tracing/trace_pipe > {self.andro_raw_output_path} \n')

        self.trace_info = trace_info

    # TOOLS START HERE ----------------------------------------------

    def _monkey_callback_print(self, line):
        if "Monkey aborted due to error" in line or "Events injected" in line:
            self._should_stop_monkey = True
        if line.startswith("Got IOException") or "// Injection Failed" in line or "activityResuming" in line or line.strip() == "":
            return # swallow these things, very verbose
        log.debug(f"MONKEY: {line.rstrip()}")

    def run_monkey(self, max_runtime):
        self._should_stop_monkey = False


        monkeycmd = f"monkey -p {self.apkid} -s 20240412 --throttle 1000 --ignore-crashes --kill-process-after-error --ignore-security-exceptions 10000000" # seed with date

        log.info(f"starting monkey as: {monkeycmd}")

        proc_monkey = self.adbdev.adb("exec-out", monkeycmd, _bg=True, _bg_exc=False,  _out=lambda x: self._monkey_callback_print(x))

        log.info("waiting for timeout")
        time_in_monkey = 0
        while time_in_monkey < max_runtime:
            time.sleep(1)
            time_in_monkey+=1
            if self._should_stop_monkey:
                log.warning("uh-oh, monkey terminated earlier than expected")
                break

        try:
            self.adbdev.root_shell("kill -9 \\`pgrep monkey\\`")
            proc_monkey.signal(signal.SIGKILL) # TODO didn't work during testing so above added. figure out why
            log.info("waiting for monkey process to get killed")
            proc_monkey.wait()
        except sh.SignalException_SIGKILL:
            log.info("handled expected sigkill exception of monkey process")
        except ProcessLookupError:
                log.info("handled expected ProcessLookupError if monkey terminated early.")

    def _droidbot_callback_print(self, line):
        if line.strip() == "":
            return
        log.debug(f"DROIDBOT: {line.rstrip()}")

    def run_droidbot(self, max_runtime):
        # shitty impl because it does arg parsing
        from sh import droidbot

        if not self.apks_dm_dir:
            raise NotImplementedError("droidbot needs access to apk files")

        apk_path = self.apks_dm_dir / "base.apk"

        outdir = self._host_res_tmpdir / "_droidbot_res"
        outdir.mkdir(exist_ok=True)

        self._should_stop_bot=False

        cmd = ["-d", self.device_id,
               "-a", apk_path,
               "-o", outdir,
               "-t", max_runtime,
        ]
        cmd = [str(x) for x in cmd] # Path to str >(
        log.info(f"running droidbot as droidbot {' '.join(cmd)}")
        proc_droidbot = droidbot(*cmd, _bg=True, _bg_exc=False,
                 _out=lambda x: self._droidbot_callback_print(x),
                 _err_to_out=True)

        log.info("waiting for timeout")
        time_in_bot = 0
        while time_in_bot< max_runtime:
            time.sleep(1)
            time_in_bot+=1
            if self._should_stop_bot:
                log.warning("uh-oh, droidbot terminated earlier than expected")
                break

        try:
            proc_droidbot.signal(signal.SIGKILL)
            log.info("waiting for droidbot process to get killed")
            proc_droidbot.wait()
        except sh.SignalException_SIGKILL:
            log.info("handled expected sigkill exception of droidbot process")
        except ProcessLookupError:
                log.info("handled expected ProcessLookupError if droidbot terminated early.")

    def _fastbot_callback_print(self, line):
        if "aborted due to error" in line or "Events injected" in line:
            self._should_stop_fastbot = True
        if "  event time:" in line \
                or " rpc cost time: " in line \
                or " action type: " in line \
                or " // Event id: " in line \
                or line.strip() == "":
            return # swallow these things, very verbose
        if "// Monkey is over!" in line: # yeyeah, no it's fastbot.
            pass # successful finish
        log.debug(f"FASTBOT: {line.rstrip()}")

    def run_fastbot(self, max_runtime):
        self._should_stop_fastbot = False

        log.warning("TODO: implement checking and pushing fastbot files if necessary") # TODO

        _run_minutes = max_runtime/60
        if max_runtime % 60 != 0:
            _run_minutes = max(1, ceil(_run_minutes))
            log.warning(f"fastbot only takes minutes in runtime, rounding up to {_run_minutes}")

        # based on the command in the fastbot documentation
        # we use exec-out to stream the output and add a seed
        # verbosity removed since it doesn't do much
        # otherwise it's the same
        proc_fastbot = self.adbdev.adb("exec-out",
                        "CLASSPATH=/sdcard/monkeyq.jar:/sdcard/framework.jar:/sdcard/fastbot-thirdpart.jar",
                        "exec", "app_process",
                        "/system/bin", "com.android.commands.monkey.Monkey",
                        "-p", self.apkid,
                        "-s", "20240412",
                        "--agent", "reuseq",
                        "--running-minutes", str(int(_run_minutes)),
                        "--throttle", "1000",
                        _bg=True,
                        _bg_exc=False,
                        _out=lambda x: self._fastbot_callback_print(x))

        log.info("waiting for timeout")
        time_in_fastbot = 0
        while time_in_fastbot < max_runtime:
            time.sleep(1)
            time_in_fastbot+=1
            if self._should_stop_fastbot:
                log.warning("uh-oh, fastbot terminated earlier than expected")
                break

        try:
            self.adbdev.root_shell("kill -9 \\`pgrep monkey\\`") # fastbot based on monkey
        except sh.ErrorReturnCode_1:
            log.info("handled expected fail of kill when if fastbot already terminated")

        try:
            proc_fastbot.signal(signal.SIGKILL) # TODO didn't work during testing so above added. figure out why, see monkey
            log.info("waiting for fastbot process to get killed")
            proc_fastbot.wait()
        except sh.SignalException_SIGKILL:
            log.info("handled expected sigkill exception of fastbot process")
        except ProcessLookupError:
            log.info("handled expected ProcessLookupError if fastbot terminated early.")

    # TOOLS END HERE ------------------------------------------------

    def _run_tool(self, tool, max_runtime=5):
        # start tool we want to run
        log.info(f"starting app tool: {tool}")
        if tool == "time":
            self.adbdev.shell.monkey(
                "-p", self.apkid, "1"
            )  # start monkey with one interaction to just start the app
            time.sleep(max_runtime)
        elif tool == "monkey":
            self.run_monkey(max_runtime)
        elif tool == "droidbot":
            self.run_droidbot(max_runtime)
        elif tool == "fastbot":
            self.run_fastbot(max_runtime)
        else:
            log.critical("unknown tool specified!")

    def _tracer_callback_print(self, line):
        """implements handling tracer output."""
        # reading over adb is slow, leading to lost events in the ringbuffer
        #if self._canStartTool:
        #    self._raw_hit_uprobes.append(line.rstrip())
        #    if len(self._raw_hit_uprobes) % 5000 == 0:
        #        log.debug(f"hit {len(self._raw_hit_uprobes)} total uprobes")
        #    return
        if "tracing set up, ready for on and app start" in line:
            log.debug(f"{line.rstrip()}")
            log.debug("setting /sys/kernel/tracing/tracing_on to 1")
            self.adbdev.root_shell("echo 1 > /sys/kernel/tracing/tracing_on")
            self._canStartTool = True
            return
        log.debug(f"{line.rstrip()}")

    def _start_tracing(self):
        self._canStartTool = False
        self._canEndEmulator = False

        tracecmd = f"{self.andro_tracepoints_sh}"
        log.info(f"starting tracer with command: {tracecmd}")

        # exec-out is a non-buffering mode for adbdev to react to output
        # this is hacky because undocumented, but whatever. google does it the same way lol
        if self._use_adb_root: # IDK why emu and hw are different here. This is another hack that works. sue me. # TODO is this still relevant?
            proc_tracer = self.adbdev.adb("exec-out", tracecmd, _bg=True, _bg_exc=False,  _out=lambda x: self._tracer_callback_print(x))
        else:
            proc_tracer = self.adbdev.adb("exec-out", "su", "-c", tracecmd, _bg=True, _bg_exc=False,  _out=lambda x: self._tracer_callback_print(x))

        # wait for expected output from tracer to start app
        log.debug("waiting for tracer to signal ready")
        grace = _TIMEOUT_FOR_PROBE_SETUP
        while not self._canStartTool:
            time.sleep(1)
            grace -= 1
            if grace < 0:
                proc_tracer.signal(signal.SIGKILL) # TODO can this actually kill the scrip withthe uprobest?
                raise NotImplementedError(f"setting up tracer probes took more than {_TIMEOUT_FOR_PROBE_SETUP}s, aborting")

    def _stop_tracing(self):
        """turn tracing off but don't clean up the uprobes - reboot handles this."""
        log.debug("turning tracing off")
        self.adbdev.adb("exec-out", "su", "-c", "echo 0 > /sys/kernel/tracing/tracing_on")

        # TODO test on emulaotr, do we need to wait with uprobes?
        # then give it 10 seconds grace time to print the statistic
        #grace = 10
        #while not self._canEndEmulator:
        #    time.sleep(0.2)
        #    grace -= 0.2
        #    if grace < 0:
        #        log.info("grace period for tracer ended")
        #        break

    def run_tracer(self, tool="time", max_runtime=5):
        """start the tracer and the tool to be evaluated"""
        if tool not in _SUPPORTED_TOOLS:
            log.critical(f"unknown tool {tool}")
            return

        log.debug(f"time on android (for sync): {self.adbdev.shell('date').strip()}")

        with contextlib.suppress(sh.ErrorReturnCode_1):
            log.debug("killing app if it runs")
            self.adbdev.root_shell("killall", self.apkid) # TODO check if running

        self._start_tracing()
        self._run_tool(tool, max_runtime)
        self._stop_tracing()

        log.info("done tracing")

    @staticmethod
    def parse_raw_hit_uprobes(raw_output_path):

        first_probe_hit_time = None
        hit_uprobes = []
        total_lost_events = 0

        with open(raw_output_path) as f:
            for line in f.readlines():
                line = line.rstrip()
                # bpf can have lost events, handle those
                if "LOST" in line and "EVENTS" in line:
                    #log.debug(f"lost events: {line}")
                    with contextlib.suppress(ValueError):
                        total_lost_events += int(line.split()[-2])
                    continue
                elif " bpf_trace_printk: " in line:
                    # ignore kerneltraces
                    continue
                # check expected layout:
                # "app.organicmaps-24536   [002] .....  4423.725704: event0x1d96b0: (0x6e16e3e6b0)"
                # "AsyncTask #2-10249 [005] ..... 184.273432: event0xa4610: (0x767e1bc610)" -> process name can have space!
                if "event0x" not in line or "....." not in line or "[" not in line:
                    log.warning(f"unexpected raw line: '{line}'")
                    continue
                name_n_other = line.split("[")
                if len(name_n_other) != 2:
                    log.warning(f"multiple '[' found, assuming part of name: {name_n_other}")
                parts = name_n_other[-1].split()

                # get process name
                pname = ' '.join(name_n_other[:-1]).strip()
                if "-" not in pname:
                    log.warning(f"no process name in line: '{line}'")
                    continue

                # get timestamp
                if parts[2][-1] != ':':
                    log.warning(f"timestamp format wrong in line: '{line}'")
                    continue
                try:
                    timestamp = float(parts[2][:-1])
                except ValueError:
                    log.warning(f"timestamp format not float in line: '{line}'")
                    continue
                if not first_probe_hit_time:
                    first_probe_hit_time = timestamp
                timestamp = timestamp - first_probe_hit_time

                # get offset
                if parts[3][:7] != "event0x" or parts[3][-1] != ':':
                    log.warning(f"event tag wrong in line: '{line}'")
                    continue
                try:
                    computed_offset = parts[3][5:-1]
                    int(computed_offset, 16)
                except ValueError:
                    log.waring(f"offset not an int in line: '{line}'")
                    continue
                # put in list
                hit_uprobes.append((pname, timestamp, computed_offset))

        log.info(f"processed {len(hit_uprobes)} events")
        log.info(f"total lost events: {total_lost_events}")
        return hit_uprobes

    def save_results(self):
        """write results to file and print summary."""
        log.debug(f"saving results as {self.host_output_path}")

        self.adbdev.pull(self.andro_raw_output_path, self.host_raw_output_path)

        hit_uprobes = Tracer.parse_raw_hit_uprobes(self.host_raw_output_path)

        results = (
                self.profile_info,
                self.offsets_info,
                self.trace_info,
                hit_uprobes
            )

        with open(self.host_output_path, "wb") as f:
            pickle.dump(results, f)

    def cleanup_android(self):
        """delete artifacts on device"""
        log.debug("cleaning up android")
        self.uninstall_and_log_errors()
        try:
            self.adbdev.root_shell(f"rm -rf {self.andro_apkdir}")
        except sh.ErrorReturnCode_1:
            log.critical("failed to rm -rf apkdir on device")

    def cleanup_host(self):
        """remove artifacts from results except results"""
        log.debug("cleaning up host")
        sh.rm("-r", self._host_res_tmpdir)

    def reboot_and_wait_ok(self, timeout=60):
        """reboot the device afterwards an wait for it to come back in 60 seconds"""
        log.debug("rebooting")
        try:
            self.adbdev.shell("reboot")
        except sh.ErrorReturnCode_255:
            log.debug("got expected returncode 255 from reboot, waiting for device to pop back up")
        except Exception as e:
            raise NotImplementedError("failed to handle reboot error") from e

        grace = timeout
        while True:
            time.sleep(1)
            grace -= 1
            with contextlib.suppress(sh.ErrorReturnCode_1):
                self.adbdev.shell("echo hi")
                break
            if grace < 0:
                log.critical("grace period for reboot ended")
                raise NotImplementedError(f"failed to reboot in {timeout}s")
        log.info("reboot complete, waiting 10s to settle")
        time.sleep(10)

@click.command()
@click.argument('apkid')
@click.option("--verbose", default=False, is_flag=True)
@click.option('--device-id', default="emulator-5555", help="serial or emulaotor name. ignored when --emulator-config is set.")
@click.option("--emulator-config", default=None, type=click.Path(dir_okay=False, path_type=Path), help="use emulatorCTRL with given config file")
@click.option("--use-adb-root", default=False, is_flag=True, help="use adb root instead of adb sh su. if emulator-config given, read from there.")
@click.option("--slot", default=0, help="for parallelization, adds to emulator port")
@click.option("--android-tmpdir", default=_ONANDR_TMPDIR, type=click.Path(file_okay=False, path_type=Path), help="directory for files on android")
@click.option("--max-probes", default=_DEFAULT_MAX_PROBES, help="limit probe numbers for stability")
@click.option("--fresh-install", default=None, help="path to apk(s) and dms for fresh install. also neede by droidbot")
@click.option("--tool", default=_SUPPORTED_TOOLS[0], type=click.Choice(_SUPPORTED_TOOLS), help="which tool to run")
@click.option("--tool-max-runtime", default=5, help="hard time limit on tool run")
@click.option("--result-dir", default=_ONHOST_DEFAULT_RESULT_DIR, type=click.Path(file_okay=False, path_type=Path), help="directory to save result")
@click.option("--no-cleanup-android", default=False, is_flag=True, help="keep arifacts on device and skip reboot")
@click.option("--no-cleanup-host", default=False, is_flag=True, help="keep intermediate artifacts on host")
@click.option("--also-startup-poststartup", default=False, is_flag=True, help="also trace startup and poststartup methods, not just hot methods")
# TODO no-cleanup only if error?
@click.option("--code-coverage", default=False, is_flag=True, help="traces not just methods in profile, but all functions in oat file. also triggers complete AOT compilation.")
@click.option("--buffer-size-kb", default=None, help="set uprobe buffer size in /sys/kernel/tracing/buffer_size_kb. increase to avoid lost events")
@click.option("--buffer-percent", default=None, help="set when uprobe buffer starts reading in /sys/kernel/tracing/buffer_percent. decrease to avoid read spikes")
@click.option("--force-wifi", default=None, help="make sure we are connected to wifi as 'ssid wpa2 passwd', see `cmd -w wifi help` for more info")
def main(
            apkid,
            verbose,
            device_id,
            emulator_config,
            use_adb_root,
            slot,
            android_tmpdir,
            max_probes,
            fresh_install,
            tool,
            tool_max_runtime,
            result_dir,
            no_cleanup_android,
            no_cleanup_host,
            also_startup_poststartup,
            code_coverage,
            buffer_size_kb,
            buffer_percent,
            force_wifi
        ):
    """
    The Tracer assumes `adb -s <device_id>` can connect to the device and we have root.
    We go through the following motions:
    - if emulator-config passed, create fresh emulator and start it
    - create Tracer object
        - connect to android and check kernel capabilities, turn tracing on.
        - create tmpdirs on android
    - if app to be installed fresh:
        - uninstall app if installed
        - install app with DM file, triggering AOT compilation
    - (at this point we assume we have an oat file for the app)
    - generate tracepoints.sh
        - read DM and grab profile methods
        - oatdump oat and grab 1. oat offset and 2. offsets of profile methods
        - create info.json containing method <-> event mapping + method metadata
        - create tracepoints.sh settinung up all the events
        - push tracepoints.sh to device
    - (at this point we assume tracepoints.sh is on device an ready to go)
    - run dynamic tool
        - invoke tracepoints.sh and wait for it to set up
        - invoke the selected dynamic tool
        - (wait)
        - terminate dynamic tool
        - tear down uprobes
        - collect results
    - reboot if hw device
    """
    global log
    emu = None
    retcode = 0

    if verbose:
        log.setLevel(logging.DEBUG)

    log.debug("starting aproftracer")

    try: # always terminate emulator
        if emulator_config:
            # start emulator and override device_id
            emu = EmulatorCTRL.from_config(cfg_file=emulator_config, slot=int(slot), verbose=verbose)
            use_adb_root = emu.use_adb_root
            if device_id != "emulator-5555":
                log.warning("overriding device-id when controlling the emulator")
            device_id = emu.get_device_name()
            emu.recreate(force=True)
            emu.start_and_wait_in_background()

        t = None
        t = Tracer(
                    apkid=apkid,
                    device_id=device_id,
                    use_adb_root=use_adb_root,
                    apks_dm_dir=fresh_install,
                    android_tmpdir=android_tmpdir,
                    host_result_dir=result_dir,
                    max_probes=max_probes,
                    buffer_size_kb=buffer_size_kb,
                    buffer_percent=buffer_percent,
                    force_wifi=force_wifi,
                    verbose=verbose,
                )

        if fresh_install:
            t.uninstall_and_log_errors()
            t.install_and_compile_from_path(compile_all_aot=code_coverage)

        if code_coverage and also_startup_poststartup:
            log.warning("tracing code coverage will include startup and poststartup methods by definition, no need to set both.")
        t.prepare_tracepoints_sh(code_coverage, also_startup_poststartup)

        t.run_tracer(tool=tool, max_runtime=tool_max_runtime)

        t.save_results()
    except Exception:
        log.critical("generic exception caught")
        tb = traceback.format_exc()
        log.critical(tb)
        retcode = 131
    finally:
        if emu:
            emu.shutdown_and_wait()
        elif not no_cleanup_android and t: # confusing but better for cli
            # only if not emulator, we throw the emulator away anyway (on next start)
            t.cleanup_android()
            t.reboot_and_wait_ok()
        if not no_cleanup_host and t:
            t.cleanup_host()

    log.info("done!")
    sys.exit(retcode)


if __name__ == "__main__":
    main()
