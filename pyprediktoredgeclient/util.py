import pkg_resources

from datetime import datetime
import functools
import collections
from typing import NamedTuple, Any, List

import clr
import System

dlls = [
    'HiveNetApi.dll',
    'ApisNetUtilities.dll',
    'Microsoft.Win32.Registry.dll',
    'netstandard.dll',
    'Prediktor.Log.dll',
    'SentinelRMSCore.dll'
    ]

# Check for the DLLS
if not pkg_resources.resource_exists(__name__, "dlls"):
    raise Exception("DLLS Not present in folder")

# Check that the DLL-reference is a folder
if not pkg_resources.resource_isdir(__name__, "dlls"):
    raise Exception("DLLS is not a folder")

# Check and add  references to each dll-file
for f in dlls:
    if not pkg_resources.resource_exists(__name__, "dlls/{}".format(f)):
        raise Exception("DLL {} is not present".format(f))

    clr.AddReference(pkg_resources.resource_filename(__name__, "dlls/{}".format(f)))

# At this point, we should be able to import "Prediktor" from the DLL
import Prediktor

def Instances():
	return Prediktor.APIS.Hive.HiveInstanceService.GetRegisteredInstances()

def prog_id(name=None):
    if name is None:
        return Prediktor.APIS.Hive.HiveInstanceService.ProgIdDefaultInstance
    prefix = Prediktor.APIS.Hive.HiveInstanceService.ProgId_Prefix
    return f"{prefix}{name}"

AttrFlags = Prediktor.APIS.Hive.Flags



OPC_quality = dict(
    bad = 0,
    badConfigurationError = 4,
    badNotConnected = 8,
    badDeviceFailure = 12,
    badSensorFailure = 16,
    badLastKnownValue = 20,
    badCommFailure = 24,
    badOutOfService = 28,
    badWaitingForInitialData = 32,
    uncertain = 64,
    uncertainLastUsableValue = 68,
    uncertainSensorNotAccurate = 80,
    uncertainEUExceeded = 84,
    uncertainSubNormal = 88,
    good = 192,
    goodLocalOverride = 216,

    extraData = 65536,
    interpolated = 131072,
    raw = 262144,
    calculated = 524288,
    noBound = 1048576,
    noData = 2097152,
    dataLost = 4194304,
    conversion = 8388608,
    partial = 16777216
)

OPC_quality_index = {v:k for (k,v) in OPC_quality.items()}

def to_pydatetime(dt):
    "convert a .NET DateTime to a python datetime object"
    return datetime(dt.Year, dt.Month, dt.Day, dt.Hour, dt.Minute, dt.Second)

def fm_pydatetime(dt):
    "convert a python datetime object to .NET DateTime object"
    return System.DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


class Error(Exception):
	"""Generic exception used to report problems in Apis.py"""
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg


class Quality(int):
    def __new__(cls, value=192):
        return super().__new__(cls, value)

    def __repr__(self):
        return f"<Quality instance: {str(self)}>"


    def __str__(self):
        val = int(self)

        da=val & 0xff
        hda = val & 0x8fffff00

        if not hda:
            return f"{OPC_quality_index[da]}"
        return f"{OPC_quality_index[da]} | {OPC_quality_index[hda]}"

    @staticmethod
    def factory(name):
        if isinstance(name, Quality):
            return name
        if isinstance(name, str):
            return Quality(OPC_quality[name])
        if isinstance(name, collections.Sequence):
            functools.reduce(lambda a,b: a | b, map(Quality.factory, name))
       


class VQT(NamedTuple):
    """
    A class for Value-Quality-Timestamp
    """
    value: Any
    quality: Quality
    time: datetime

class ItemVQT(NamedTuple):
    """
    A class for item-id, value, quality and timestamp
    """
    item_id: str
    value: Any
    quality: Quality
    time: datetime

class Timeseries(NamedTuple):
    """
    A class for item-id, value, quality and timestamp
    """
    item_id: str
    hs_database: str
    timeseries: List[VQT]










