"""Exercise the nested cloud entrypoint without pytest's repository import path."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("working_directory", ["repository", "entrypoint", "unrelated"])
def test_cloud_startup_without_repository_on_python_path(tmp_path, working_directory):
    root = Path(__file__).resolve().parents[1]
    entrypoint = root / "deployment/streamlit/app.py"
    directories = {"repository": root, "entrypoint": entrypoint.parent, "unrelated": tmp_path}
    environment = {key: value for key, value in os.environ.items()
                   if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE"}}
    environment.update(APP_ENV="test", STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
    code = """
import importlib.util
from pathlib import Path
import socket
import sys
from streamlit.testing.v1 import AppTest

entrypoint = Path(sys.argv[1])
assert importlib.util.find_spec('interview_app_frontend') is None
connect = socket.socket.connect
def guarded(sock, address):
    if isinstance(address, tuple) and address[0] in {'127.0.0.1', '::1'}:
        return connect(sock, address)
    raise AssertionError('External network prohibited during startup')
socket.socket.connect = guarded
ui = AppTest.from_file(str(entrypoint)).run(timeout=15)
assert not ui.exception, [error.message for error in ui.exception]
assert [error.value for error in ui.error] == [
    'The demonstration requires the approved mocked Preview backend.']
assert not ui.button
import interview_app_frontend.app
assert Path(interview_app_frontend.app.__file__).resolve() == entrypoint.parents[2] / 'interview_app_frontend/app.py'
assert Path.cwd() == Path(sys.argv[2])
print('Nested entrypoint imported; inactive configuration; no backend requests')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(entrypoint), str(directories[working_directory])],
        cwd=directories[working_directory], env=environment, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "inactive configuration; no backend requests" in result.stdout
