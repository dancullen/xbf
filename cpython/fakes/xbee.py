""" xbee.py is a mock/fake implementation of the Digi XBee 3 MicroPython xbee module for use in CPython3 unit tests. """

from typing import Any, Optional


class _Relay:

    SERIAL = 0
    BLUETOOTH = 1
    MICROPYTHON = 2

    def __init__(self):
        self.incoming = []  # Stores messages of format:  { "sender": 0, "message" : b"" }
        self.outgoing = []  # Stores messages of format: { "dest": 0, "data": b"" }

    def receive(self) -> Optional[dict]:
        if len(self.incoming) == 0:
            return None
        return self.incoming.pop(0)

    def send(self, dest: int, data: Any) -> None:
        self.outgoing.append({"dest": dest, "data": data})


relay = _Relay()

_registers = {}


def atcmd(cmd, value=None):
    global _registers
    if value is not None:
        _registers[cmd] = value
    return _registers.get(cmd, None)
