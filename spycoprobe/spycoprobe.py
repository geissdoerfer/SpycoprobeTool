import serial
import numpy as np
import struct
import logging
from typing import Union
from serial.tools import list_ports

from spycoprobe.intelhex import IntelHex16bitReader
from spycoprobe.protocol import ReqType
from spycoprobe.protocol import ReturnCode
from spycoprobe.protocol import TargetPowerState
from spycoprobe.protocol import IOSetState

from spycoprobe.protocol import REQUEST_MAX_DATA
from spycoprobe.protocol import RESPONSE_MAX_DATA


class DeviceNotFoundError(Exception):
    pass


INTERFACE_NAMES = ["Spycoprobe SBW", "Rioteeprobe SBW"]


def find_device():
    hits = list()
    for port in list_ports.comports():
        if port.interface in INTERFACE_NAMES:
            hits.append(port.device)

    if not hits:
        raise DeviceNotFoundError("Couldn't find a Spycoprobe USB device.")
    elif len(hits) == 1:
        logging.info(f"Found spycoprobe at {hits[0]}")
        return hits[0]
    else:
        raise DeviceNotFoundError(f"Found multiple spycoprobes at {' and '.join(hits)}")


class SpycoProbe(object):
    def __init__(self, port=None, baudrate=1000000, timeout=1.0):
        if port is None:
            self._port = find_device()
        else:
            self._port = port
        self._baudrate = baudrate
        self._timeout = timeout

    def __enter__(self):
        self._ser = serial.Serial(self._port, self._baudrate, timeout=self._timeout)
        return self

    def __exit__(self, *exc):
        self._ser.close()

    def _recv_rsp(self):
        """Receive a packet from CDC ACM serial and decode it."""
        rsp = ""
        while len(rsp) == 0:
            rsp = self._ser.read_all()

        rc = int(rsp[0])
        if rc != ReturnCode.SBW_RC_OK:
            raise Exception(f"Probe replied with RC {rc}")

        if len(rsp) > 1:
            # Extract length of payload
            dlen = int(rsp[1])
            # Extract payload
            data = np.frombuffer(rsp[2:], dtype=np.uint16, count=dlen)
            return data

    def start(self):
        """Puts device under JTAG control."""
        pkt = struct.pack("=B", int(ReqType.SBW_REQ_START))
        self._ser.write(pkt)
        self._recv_rsp()

    def stop(self):
        """Releases device from JTAG control."""
        pkt = struct.pack("=B", int(ReqType.SBW_REQ_STOP))
        self._ser.write(pkt)
        self._recv_rsp()

    def halt(self):
        """Halt CPU execution."""
        pkt = struct.pack("=B", int(ReqType.SBW_REQ_HALT))
        self._ser.write(pkt)
        self._recv_rsp()

    def release(self):
        """Continue CPU execution."""
        pkt = struct.pack("=B", int(ReqType.SBW_REQ_RELEASE))
        self._ser.write(pkt)
        self._recv_rsp()

    def target_power(self, state: bool):
        if state:
            pkt = struct.pack(f"=BBIH", ReqType.SBW_REQ_POWER, 1, 0x0, TargetPowerState.TARGET_POWER_ON)
        else:
            pkt = struct.pack(f"=BBIH", ReqType.SBW_REQ_POWER, 1, 0x0, TargetPowerState.TARGET_POWER_OFF)
        self._ser.write(pkt)
        self._recv_rsp()

    def gpio_set(self, pin_no, state: IOSetState):
        pkt = struct.pack(f"=BBI2H", ReqType.SBW_REQ_IOSET, 2, 0x0, pin_no, state)
        self._ser.write(pkt)
        self._recv_rsp()

    def gpio_get(self, pin_no) -> bool:
        pkt = struct.pack(f"=BBIH", ReqType.SBW_REQ_IOGET, 2, 0x0, pin_no)
        self._ser.write(pkt)
        return bool(self._recv_rsp()[0])

    def write_mem(self, addr, data: Union[int, np.ndarray]):
        """Write a word to NVM or RAM."""
        if hasattr(data, "__len__"):
            if len(data) > REQUEST_MAX_DATA:
                raise ValueError("Data length exceeds request packet size")
            pkt = struct.pack(f"=BBI{len(data)}H", ReqType.SBW_REQ_WRITE, len(data), addr, *data)
        else:
            pkt = struct.pack(f"=BBIH", ReqType.SBW_REQ_WRITE, 1, addr, data)
        self._ser.write(pkt)
        self._recv_rsp()

    def read_mem(self, addr, dlen: int = 1):
        """Read a word from NVM or RAM."""
        if dlen > RESPONSE_MAX_DATA:
            raise ValueError("Data length exceeds response packet size")
        pkt = struct.pack(f"=BBI", ReqType.SBW_REQ_READ, dlen, addr)
        self._ser.write(pkt)
        return self._recv_rsp()

    def flash(self, image, verify: bool):
        ih = IntelHex16bitReader()
        ih.loadhex(image)

        self.halt()
        for pkt in ih.iter_packets(REQUEST_MAX_DATA):
            self.write_mem(pkt.address, pkt.values)
            if verify:
                rb = self.read_mem(pkt.address, len(pkt))
                if (rb != pkt.values).any():
                    print(rb, pkt.values)
                    raise Exception(f"Verification failed at 0x{pkt.address:08X}!")
        self.release()
