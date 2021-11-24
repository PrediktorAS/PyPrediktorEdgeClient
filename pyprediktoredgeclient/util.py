import pkg_resources

from datetime import datetime
import functools
import collections
import os
import sys
from typing import NamedTuple, Any, List

import clr
import System

dlls = [
    'HiveNetApi.dll',
    'ApisNetUtilities.dll',
    'Microsoft.Win32.Registry.dll',
    #'netstandard.dll',
    'Prediktor.Log.dll',
    'SentinelRMSCore.dll'
    ]

if sys.platform == 'win32':
    import winreg

    def hive_clsid(instance = None):
        instance = "1" if instance is None else instance
        path = f"Prediktor.ApisLoader.{instance}\\CLSID"
        return winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, path)

    def hive_appid(instance = None):
        path = "AppId\\ApisHive.exe"  if instance is None else f"AppId\\ApisHive.{instance}.exe"
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        v, _ = winreg.QueryValueEx(key, "AppID")
        return v

    def hive_executable():
        path = f"CLSID\\{hive_clsid()}\\LocalServer32"
        v = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, path)
        return v.strip('"')

    def hive_bindir():
        return os.path.dirname(hive_executable())

    def hive_basedir():
        tmp = hive_bindir()
        if (os.path.basename(tmp).lower() == "dbg"):
            tmp = os.path.dirname(tmp)
        return os.path.dirname(tmp)

    def hive_configdir(name = "ApisHive"):
        return os.path.join(hive_basedir(), "Config", name)

    def hive_chronicaldir(name = "ApisHive"):
        return os.path.join(hive_basedir(), "Chronical", name)


def _import():
    if sys.platform == 'win32':
        dir = hive_bindir()
        for dll in dlls:
            pth = os.path.join(dir, dll)
            clr.AddReference(pth)
        return dir

    # Check for the DLLS
    if not pkg_resources.resource_exists(__name__, "dlls"):
        raise Exception("DLLS Not present in folder")

    # Check that the DLL-reference is a folder
    if not pkg_resources.resource_isdir(__name__, "dlls"):
        raise Exception("DLLS is not a folder")

    # Check and add  references to each dll-file
    for f in dlls:
        if not pkg_resources.resource_exists(__name__, f"dlls/{f}"):
            raise Exception("DLL {} is not present".format(f))

        clr.AddReference(pkg_resources.resource_filename(__name__, f"dlls/{f}"))

    return pkg_resources.resource_string(__name__, "dlls")

importlocation = _import()

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

RunState = Prediktor.APIS.Hive.ApisRunState

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

def to_pydatetime(dt: System.DateTime):
    "convert a .NET DateTime to a python datetime object"
    tmp = datetime(dt.Year, dt.Month, dt.Day, dt.Hour, dt.Minute, dt.Second, dt.Millisecond * 1000)

def fm_pydatetime(dt: datetime):
    "convert a python datetime object to .NET DateTime object"
    tmp = System.DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    millis = int(dt.microsecond / 1000)
    return tmp.AddMilliseconds(millis)

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
    A class for item-id, and a sequence of (value, quality and timestamp) tuples
    """
    item_id: str
    hs_database: str
    timeseries: List[VQT]


class BaseAttribute:
	def __str__(self):
		return f"{self.name}={self.value}"

	@property
	def name(self):
		return self.api.Name

	@property
	def flag(self):
		return self.api.Flag

	def get_value(self):
		v = self.api.Value
		if self.flag & AttrFlags.Enumerated:
			attr_enum = self.api.GetEnumeration()
			for i,val in enumerate(attr_enum.Values):
				if val==v:
					return attr_enum.Names[i]
			raise Error(f"Enumerated property with value '{v}' not found on {self.name}")
		return v

	def set_value(self, value):
		if self.flag & AttrFlags.ReadOnly:
			raise AttributeError(f"Attribute {self.name} on {self.item} is read only")

		if self.flag & AttrFlags.Enumerated:
			attr_enum = self.api.GetEnumeration()
			for i,val in enumerate(attr_enum.Names):
				if str(val).lower()==str(value).lower():
					self.api.Value = attr_enum.Values[i]
					break
			else:
				raise Error(f"Enumerated property for {value} not found on attribute {self.name}.")
		else:
			try:
				self.api.Value = value
			except Exception as e:
				#Wrap the exception from below in an Error. 
				raise Error(f"Exception from Apis {e}")

	value = property(get_value, set_value, doc="Access the property value")







