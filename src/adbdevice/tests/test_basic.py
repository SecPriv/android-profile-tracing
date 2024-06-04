import pytest
import sh
from adbdevice import AdbRootDevice


def test_nonexistant_serial_number():
    with pytest.raises(sh.ErrorReturnCode_1) as _:
        AdbRootDevice("FFAA55TT")

