import logging

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

from adbdevice.adbdevice import (  # noqa: F401 E402
    AdbDevice,
    AdbRootDevice,
    SuRootDevice,
    check_device_ok,
    run_cmd,
)
