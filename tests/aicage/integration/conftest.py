import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

_FAKE_HOME = Path(tempfile.mkdtemp(prefix="aicage-test-home-")).resolve()
_FAKE_HOME.mkdir(parents=True, exist_ok=True)

if sys.platform != "darwin":
    os.environ["HOME"] = str(_FAKE_HOME)
    os.environ["USERPROFILE"] = str(_FAKE_HOME)
    if sys.platform == "win32":
        drive, tail = os.path.splitdrive(str(_FAKE_HOME))
        if drive:
            os.environ["HOMEDRIVE"] = drive
            os.environ["HOMEPATH"] = tail or "\\"


def _cleanup_fake_home() -> None:
    shutil.rmtree(_FAKE_HOME, ignore_errors=True)


atexit.register(_cleanup_fake_home)
