from enum import IntEnum

REQUEST_MAX_DATA = 29
RESPONSE_MAX_DATA = 31


class ReqType(IntEnum):
    SBW_REQ_START = 0
    SBW_REQ_STOP = 1
    SBW_REQ_HALT = 2
    SBW_REQ_RELEASE = 3
    SBW_REQ_WRITE = 4
    SBW_REQ_READ = 5
    SBW_REQ_POWER = 6
    SBW_REQ_IOSET = 7
    SBW_REQ_IOGET = 8


class ReturnCode(IntEnum):
    SBW_RC_OK = 0
    SBW_RC_ERR_GENERIC = 1
    SBW_RC_ERR_UNKNOWN_REQ = 2
    SBW_RC_ERR_UNSUPPORTED = 3


class TargetPowerState(IntEnum):
    TARGET_POWER_OFF = 0
    TARGET_POWER_ON = 1


class IOSetState(IntEnum):
    IOSET_OUT_LOW = 0
    IOSET_OUT_HIGH = 1
    IOSET_IN = 2


class IOGetState(IntEnum):
    IOGET_LOW = 0
    IOGET_HIGH = 1
