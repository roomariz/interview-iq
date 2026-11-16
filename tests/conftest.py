"""Automated tests cannot contact paid providers or other external services."""

import socket

import pytest


@pytest.fixture(autouse=True, scope="session")
def block_external_network():
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded(original):
        def connect(sock, address):
            # Windows asyncio uses a loopback socket pair internally.
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original(sock, address)
            raise RuntimeError("External network access is disabled during automated tests")
        return connect

    # Keep the guard until process exit, including background worker shutdown.
    socket.socket.connect = guarded(original_connect)
    socket.socket.connect_ex = guarded(original_connect_ex)
