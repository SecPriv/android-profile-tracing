#!/usr/bin/env python3

import contextlib
import csv
import re
import signal
import time
import traceback
from pathlib import Path

import click
import sh

from adbdevice import AdbRootDevice, SuRootDevice, log
from adbdevice.emulatorctrl import EmulatorCTRL

ANDROID_TMPDIR=Path("/data/local/tmp/tracer")

#https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class Tracer:
    def __init__(self, device, apk_path, dm_path=None):
        self.apk_path = apk_path
        self.dm_path = dm_path if dm_path else self.apk_path.with_suffix('.dm')
        self.pid = self.apk_path.stem
        if device.startswith('emulator'): # TODO lineage os does it differently
            self.adbdev = AdbRootDevice(device)
        else:
            self.adbdev = SuRootDevice(device)
        log.info("connected to device")
        self.check_and_enable_tracing()

        self._andro_odex_path = None
        self._oatdata_offset = None
        self.res_dir = Path(f"results/{self.pid}")
        if not self.res_dir.exists():
            sh.mkdir("-p", f"{self.res_dir}")

        self.__buf = ""

        self.profdump_path = self.res_dir / 'primary.profdump.txt'
        self.oatdump_path = self.res_dir / 'oatdump.txt'
        self.offsets_path = self.res_dir / 'offsets.csv'
        self.output_path = self.res_dir / 'output.txt'

        self.andro_tmpdir = ANDROID_TMPDIR / self.pid
        self.adbdev.root_shell(f"mkdir -p {self.andro_tmpdir}")
        self.andro_tracer_bin = ANDROID_TMPDIR / 'tracer.bin'
        self.andro_offsets_path = None
        # TODO adjust for architecture, but that depends on tracer bin dealing correctly with arm pt_regs
        if 'tracer' not in self.adbdev.root_shell(f"ls {ANDROID_TMPDIR}"):
            self.adbdev.push("./precompiled/tracer_x86-64.bin", self.andro_tracer_bin)
            log.info("pushed tracer binary")

        log.info("device set up")

        self._num_attach_logmessages = 0

    def check_and_enable_tracing(self):
        kconf = self.adbdev.shell("zcat /proc/config.gz")
        for setting in [
                "CONFIG_BPF=y",
                "CONFIG_BPF_SYSCALL=y",
                "CONFIG_UPROBES=y",
                "CONFIG_UPROBE_EVENTS=y"]:
            assert(setting in kconf)
        self.adbdev.root_shell("echo '1' > /sys/kernel/tracing/tracing_on")
        self.adbdev.root_shell("if [ `cat /proc/self/mounts | grep 'sys/kernel/debug' -c` -eq 0 ]; then mount -t debugfs debugfs /sys/kernel/debug; fi") # mount debugfs if not
        log.info("kernel seems ok!")


    def check_or_do_install(self):
        if not self.adbdev.installed(self.pid):
            log.info("package not installed, installing now..")
            self.adbdev.adb("install", self.apk_path)
        log.info("package installed")

    def compile_package(self):
        # TODO this takes a while, we can probably check with oatdump if the filter is "everything" in the oat file to avoid doing this
        log.debug("compiling package, might take a while")
        self.adbdev.root_shell(f"pm compile -m everything -f {self.pid}")
        log.info("compiled profile everything ahead of time")

    @property
    def andro_odex_path(self):
        if not self._andro_odex_path:
            p = self.adbdev.root_shell(f"pm dump {self.pid} | grep 'codePath' | xargs").strip()[9:]
            self._andro_odex_path = self.adbdev.root_shell(f"find {p} -name '*.odex' 2> /dev/null | head -n 1").strip()
            log.info(f"found oat at: {self._andro_odex_path}")
        return self._andro_odex_path

    @property
    def oatdata_offset(self):
        if not self._oatdata_offset:
            readelf = self.adbdev.root_shell(f"readelf -s {self.andro_odex_path}")
            for line in readelf.split('\n'):
                if line.endswith('oatdata'):
                    self._oatdata_offset = int(line.split()[1], 16)
            log.info(f"found oatdata offset at: {self._oatdata_offset:x}")
        return self._oatdata_offset

    def _prepare_profile_and_oatdump(self):
        andro_prof_path = self.andro_tmpdir / 'primary.prof'
        andro_profdump_path = self.andro_tmpdir / self.profdump_path.name
        andro_oatdump_path = self.andro_tmpdir / self.oatdump_path.name

        # -n to ignore existing files
        try:
            sh.unzip("-n", f"{self.dm_path}", "primary.prof", "-d", f"{self.res_dir}")
        except sh.ErrorReturnCode_11:
            # primar prof does not exist
            raise NotImplementedError("primary prof not in .dm file") from None

        if not self.profdump_path.exists():
            self.adbdev.push(f"{self.res_dir / 'primary.prof'}", andro_prof_path)
            self.adbdev.root_shell("profman", "--dump-only", f"--profile-file={andro_prof_path}", ">", andro_profdump_path)
            self.adbdev.pull(andro_profdump_path, self.profdump_path)
        log.info("got profdump")

        if not self.oatdump_path.exists():
            with contextlib.suppress(sh.ErrorReturnCode_1):
                # android plays fast and loose with errorcodes, for whatsapp the dump works but returns 1. also no errors
                self.adbdev.root_shell(f"oatdump --oat-file={self.andro_odex_path} --no-disassemble > {andro_oatdump_path}")
            self.adbdev.pull(andro_oatdump_path, self.oatdump_path)
        log.info("got oatdump")

    def _generate_and_save_offsets(self):
        # parse profdump for list of ids
        hotmethods = {}
        with open(self.profdump_path) as f:
            _current_dex = None
            for line in f.readlines():
                if '[index=' in line:
                    _current_dex = line.split()[0].strip()
                elif 'hot methods:' in line.strip():
                    methods = [int(x.split('[')[0]) for x in line.strip().split()[2:]]
                    hotmethods[_current_dex] = set(methods)
        log.info("parsed profman output")

        # parse oatdump for offsets
        all_results = []
        with open(self.oatdump_path, errors='backslashreplace') as f:
            cur_loc = None
            cur_method_idx = None
            cur_offset = None
            cur_method_name = None # always on same line as idx
            all_results = []
            for line in f.readlines():
                if line.startswith("location:"):
                    cur_loc = line.split()[1].split('/')[-1].strip()
                    cur_method_idx = None
                    cur_offset = None
                    log.info(f" - reading oatdump at: {cur_loc}") # for progress
                elif not cur_method_idx and (m := re.match(r"  [0-9]+: (.*)( \(dex_method_idx=)([0-9]+).*", line)):
                    cur_method_idx = int(m.group(3))
                    # check if it's an index we actually care about
                    if cur_method_idx not in hotmethods[cur_loc]:
                        cur_method_idx = None
                        continue
                    cur_method_name = m.group(1)
                    cur_offset = None
                    #log.info(line)
                    #log.info(cur_loc, cur_method_idx, cur_method_name)
                elif cur_method_idx and not cur_offset and (m := re.match(r"    CODE: \(code_offset=0x([0-9a-f]+) ", line)):
                    cur_offset = m.group(1)
                    #log.info(line)
                    #log.info(cur_offset)
                    all_results.append((cur_loc, cur_method_idx, f"0x{cur_offset}", f"0x{self.oatdata_offset:x}", cur_method_name))
                    cur_method_idx = None
        log.info(f"parsed oatdump output for {len(all_results)} offsets")

        # location;method_idx;offset;oatdata_offset;name

        # write to file
        with open(self.offsets_path, 'w', newline='') as csvfile:
            offsetwriter = csv.writer(csvfile, delimiter=';',quoting=csv.QUOTE_MINIMAL)
            offsetwriter.writerows(all_results)

    def calculate_offsets(self):
        if not self.offsets_path.exists():
            self._prepare_profile_and_oatdump()
            self._generate_and_save_offsets()
            log.info("generated offsets file")
        else:
            log.info("using already generated offsets file")
        self.andro_offsets_path = self.andro_tmpdir / self.offsets_path.name
        self.adbdev.push(self.offsets_path, self.andro_offsets_path)
        log.info("pushed offsets file")

    def _callback_print(self, quiet, line):
        if quiet and "[DEBUG]" in line: # TODO make it aggregate "Attach Probe events for quiet mode so we see progress but not 10k lines"
            return
        if "[DEBUG] - libbpf:" in line:
            return
        if "[DEBUG] - Attached probe for" in line:
            self._num_attach_logmessages +=1
            if self._num_attach_logmessages % 1000 == 0:
                log.debug(f"Attached {self._num_attach_logmessages} probes so far")
            return
        log.info(f"TRACER.BIN: {re_ansi_escape.sub('', line).strip()}")
        if "[INFO] - App can now be started" in line:
            self._canContinueStartingApp = True
        if "[INFO] - Starting to collect probes" in line:
            self._canStartTool = True
        elif "[INFO] - Statistic:" in line:
            self._canEndEmulator = True

    def run_monkey(self):
        raise NotImplementedError("TODO settings for monkey")
        log.info("running monkey for 5 seconds")
        try:
            self.adbdev.shell.monkey("-p", self.pid, "1") # start monkey with one interation to start it.
            time.sleep(5)
        except sh.ErrorReturnCode_252:
            # if monkey doesn't run log the fail and move on
            log.critical("could not launch activity for {}", self.pid)


    def run_tracer(self, quiet=False, tool="time"):

        if tool != "time" and tool != "monkey":
            log.critical(f"unknown tool {tool}")
            return

        log.debug(f"time in emulator: {self.adbdev.shell('date')}")

        self._canContinueStartingApp = False
        self._canStartTool = False
        self._canEndEmulator = False

        andro_output_path = self.andro_tmpdir / self.output_path.name
        tracecmd = f"{self.andro_tracer_bin} -d -p {self.pid} -i {self.andro_offsets_path} -o {andro_output_path}"
        log.info(f"starting tracer: {tracecmd}")

        proc_tracer = self.adbdev.adb("exec-out", tracecmd, _bg=True, _out=lambda x: self._callback_print(quiet, x))
        # TODO: this is hacky but whatever, google does it the same way lol
        grace = 30
        while not self._canContinueStartingApp: # wait until syscall probes are ready
            time.sleep(1)
            grace -= 1
            if grace < 0:
                raise NotImplementedError("setting up bpf syscall hookes took more than 30s, aborting")

        # kill app if it runs
        try:
            log.debug("killing app if it runs")
            self.adbdev.root_shell("killall", self.pid) # TODO check if running
        except sh.ErrorReturnCode_1:
            pass # killing not existing process ignored

        log.info("running monkey to start app for probe attachment")
        try:
            self.adbdev.shell.monkey("-p", self.pid, "1") # start monkey with one interation to start it.
        except sh.ErrorReturnCode_252:
            # if monkey doesn't run log the fail and move on
            log.critical("could not launch activity for {}", self.pid)
            raise NotImplementedError("todo handle app not starting for probe attachment") from None

        # wait until probes are attached
        log.debug("waiting for probes to finish attaching")
        grace = 30
        while not self._canStartTool:
            time.sleep(1)
            grace -= 1
            if grace < 0:
                raise NotImplementedError("setting up uprobes took more than 30s, aborting")

        # start tool we want to run
        log.info("starting app to attach probes")
        if tool=="monkey":
            self.run_monkey()
        elif tool=="time":
            time.sleep(5)
        else:
            log.critical("weird, no tool running!")

        # send SIGINT on android as it properly expects it
        log.info("sigint tracer")
        self.adbdev.root_shell("killall -2 tracer.bin")

        # then give it 10 seconds grace time to print the statistic
        grace = 10
        while not self._canEndEmulator:
            time.sleep(0.2)
            grace -= 0.2
            if grace < 0:
                log.info("grace period for tracer ended")
                break

        # finally koll the tracer
        log.info("sigkill tracer")
        try:
            proc_tracer.signal(signal.SIGKILL)
            log.info("waiting")
            proc_tracer.wait()
        except sh.SignalException_SIGKILL:
            log.info("handled expected sigkill exception of tracer process")

        # TODO pull output.txt // only if tracer got shut down, probably not if killed

        log.info("done")


@click.command()
@click.argument('apk', type=click.Path(exists=True))
@click.option("--control-emulator", is_flag=True, default=False)
@click.option('--device-id', default="emulator-5555")
@click.option("--skip-compinstall", default=False, is_flag=True)
@click.option("--only-emu-setup", default=False, is_flag=True)
@click.option("--slot", default=0, help="for arallelization, add to emulator port")
def main(apk, control_emulator, device_id, skip_compinstall, only_emu_setup, slot):
    emu = None
    retcode = 0
    try: # always terminate emulator
        # start emulator and override device_id
        if control_emulator:
            emu = EmulatorCTRL(slot=int(slot))
            log.debug("overriding device id")
            device_id = emu.get_device_name()
            emu.recreate(force=True)
            emu.start_and_wait_in_background()

        apk_path = Path(apk)
        t = Tracer(device_id, apk_path)

        if only_emu_setup:
            return

        if not skip_compinstall:
            t.check_or_do_install() # TODO mark force uninstall (void if emulator forced recreatuin used)
            t.compile_package()

        t.calculate_offsets()

        t.run_tracer(tool="time")
    except Exception:
        log.critical("generic exception caught")
        tb = traceback.format_exc()
        log.critical(tb)
        retcode = 131


    if emu:
        emu.shutdown_and_wait()

    log.info("done!")
    return retcode



if __name__ == "__main__":
    main()
