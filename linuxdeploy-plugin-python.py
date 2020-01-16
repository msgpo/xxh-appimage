from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from typing import List, Union


DEFAULT_APPDIR = "AppDir"
"""Default path for the app"""


PYTHON_PREFIX = "usr/python"
"""Prefix path for installing Python"""


LDFLAGS = os.getenv("LDFLAGS") or ""
NPROC   = os.getenv("NPROC")   or 1


_Path = Union[Path, str]


def _unipath(s: _Path) -> Path:
    return Path(s).resolve()


def install_python(source: _Path, appdir: _Path = None,
        pip: bool=True, **kwargs: Union[str, bool]) -> None:

    source = _unipath(source)
    if appdir is None:
        appdir = DEFAULT_APPDIR
    appdir = _unipath(appdir)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        # Extract or copy the source
        ext = source.suffix
        if ext in (".tgz", ".gz", ".tar"):
            mode = "r:" if ext == ".tar" else "r:gz"
            with tarfile.open(source, mode) as tar:
                names = tar.getnames()
                tar.extractall()
            os.chdir(names[0])
        else:
            shutil.copytree(source, ".")
            os.chdir(source.name)

        prefix = appdir / PYTHON_PREFIX
        reldir = os.path.relpath(appdir / "usr/lib", prefix / "bin")

        # Configure the Python build
        configure_cmd: List[str] = [
            "./configure",
            f"--prefix=/{prefix}",
            f"LDFLAGS='{LDFLAGS} -Wl,-rpath='$ORIGIN/{reldir}'"
        ]

        if pip:
            configure_cmd.append("--with-ensurepip=install")

        for k, v in kwargs.items():
            k = k.replace("_", "-")

            arg: str
            if type(v) == str:
                arg = f"--{k}={v}"
            else:
                action = "enable" if v else "disable"
                arg = f"--{action}-{k}"
            configure_cmd.append(arg)

        subprocess.run(configure_cmd, shell=True)

        # Build and install
        install_cmd = (
            "make", f"-j{NPROC}", f"DESTDIR={appdir}", "install"
        )

        subprocess.run(install_cmd, shell=True)


if __name__ == "__main__":
    install_python("Python-3.8.1.tgz", pip=False, optimizations=False)
