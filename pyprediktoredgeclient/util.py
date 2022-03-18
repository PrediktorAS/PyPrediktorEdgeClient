import chunk
from platform import node
import uuid
import pkg_resources

from datetime import datetime
import functools
import collections
import os
import io
import sys
from typing import NamedTuple, Any, List
import winreg
from enum import Enum

import clr
import System

dlls = [
    'HiveNetApi.dll',
    'ApisNetUtilities.dll',
    'Microsoft.Win32.Registry.dll',
    'HoneystoreNetApi.dll',
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


imported_assemblies=[]

def get_instance_CLSID(name=None):
    try:
        key = f"\\Prediktor.ApisLoader.{name or '1'}\\CLSID"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key) as regpth:
            return regpth.QueryValue(regpth, None)
    except WindowsError:
        raise Error(f"Unknown instance name {name}")



def get_install_dir():
    """
    Get the relevant registry keys from windows for the install location of apis
    """

    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"\CLSID\{51F92300-CA68-11d2-85C3-0000E8404A66}\LocalServer32") as reg:
            pth = winreg.QueryValue(reg, None).strip('"')
            return os.path.dirname(pth)
    except:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Prediktor\Apis") as reg:
            l, t = winreg.QueryValueEx(reg, "HiveInstallRoot")
            return os.path.join(l, 'Bin64')

def import_apis_asm():
    """
    Locate and import the APIS assemblies. The import process goes throught the following steps:
    1. If the environment variable 'APIS_INSTALL_LOCATION' is defined - use that as the import location
    2. If running on a windows platform check for possible, common installation locations
    3. Install the packages from the install kit
    """

    loc = os.environ.get('APIS_INSTALL_LOCATION')

    if loc is None and sys.platform == 'win32':
        loc = get_install_dir()

    if loc is None:

        # Check for the DLLS
        if not pkg_resources.resource_exists(__name__, "dlls"):
            raise Exception("DLLS Not present in folder")

        # Check that the DLL-reference is a folder
        if not pkg_resources.resource_isdir(__name__, "dlls"):
            raise Exception("DLLS is not a folder")

        loc = pkg_resources.resource_string(__name__, "dlls")


    # Check and add  references to each dll-file
    for dll_name in dlls:
        dll_path = os.path.join(loc, dll_name)
        if os.path.exists(dll_path):
            clr.AddReference(dll_path)
            imported_assemblies.append(dll_path)
        elif dll_name != 'SentinelRMSCore.dll':
            raise Exception(f"DLL {dll_name} is not present")

    return loc

importlocation = import_apis_asm()

# At this point, we should be able to import "Prediktor" from the DLL
import Prediktor


def get_apis_instances():
	return Prediktor.APIS.Hive.HiveInstanceService.GetRegisteredInstances()

def prog_id(name=None):
    if name is None:
        return Prediktor.APIS.Hive.HiveInstanceService.ProgIdDefaultInstance
    prefix = Prediktor.APIS.Hive.HiveInstanceService.ProgId_Prefix
    return f"{prefix}{name}"

AttrFlags = Prediktor.APIS.Hive.Flags

RunState = Prediktor.APIS.Hive.ApisRunState


class OPC_quality(Enum):
    bad = 0
    badConfigurationError = 4
    badNotConnected = 8
    badDeviceFailure = 12
    badSensorFailure = 16
    badLastKnownValue = 20
    badCommFailure = 24
    badOutOfService = 28
    badWaitingForInitialData = 32
    uncertain = 64
    uncertainLastUsableValue = 68
    uncertainSensorNotAccurate = 80
    uncertainEUExceeded = 84
    uncertainSubNormal = 88
    good = 192
    goodLocalOverride = 216

    extraData = 65536
    interpolated = 131072
    raw = 262144
    calculated = 524288
    noBound = 1048576
    noData = 2097152
    dataLost = 4194304
    conversion = 8388608
    partial = 16777216


OPC_quality_index = {v:k for (k,v) in OPC_quality.__members__.items()}


class VariantType(Enum):
	EMPTY = 0		# Indicates that a value was not specified.
	NULL = 1		# Indicates a null value,similar to a null value in SQL.
	I2 = 2			# Indicates a short integer.
	I4 = 3			# Indicates a long integer.
	R4 = 4			# Indicates a float value.
	R8 = 5			# Indicates a double value.
	CY = 6			# Indicates a currency value.
	DATE = 7		# Indicates a DATE value.
	BSTR = 8		# Indicates a BSTR string.
	DISPATCH = 9	# Indicates an IDispatch pointer.
	ERROR = 10		# Indicates an SCODE.
	BOOL = 11		# Indicates a Boolean value.
	VARIANT = 12	# Indicates a VARIANT far pointer.
	UNKNOWN = 13	# Indicates an IUnknown pointer.
	DECIMAL = 14	# Indicates a decimal value.
	I1 = 16	    	# Indicates a char value.
	UI1 = 17		# Indicates a byte.
	UI2 = 18		# Indicates an unsignedshort.
	UI4 = 19		# Indicates an unsignedlong.
	I8 = 20 		# Indicates a 64-bit integer.
	UI8 = 21		# Indicates an 64-bit unsigned integer.
	INT = 22		# Indicates an integer value.
	UINT = 23		# Indicates an unsigned integer value.
	VOID = 24		# Indicates a C style void.
	HRESULT = 25	# Indicates an HRESULT.
	PTR = 26		# Indicates a pointer type.
	SAFEARRAY = 27	# Indicates a SAFEARRAY. Not valid in a VARIANT.
	CARRAY = 28 	# Indicates a C style array.
	USERDEFINED = 29	# Indicates a user defined type.
	LPSTR = 30		# Indicates a null-terminated string.
	LPWSTR = 31 	# Indicates a wide string terminated by null.
	RECORD = 36	    # Indicates a user defined type.
	FILETIME = 64	# Indicates a FILETIME value.
	BLOB = 65		# Indicates length prefixed bytes.
	STREAM = 66	    # Indicates that the name of a stream follows.
	STORAGE = 67	# Indicates that the name of a storage follows.
	STREAMED_OBJECT = 68	# Indicates that a stream contains an object.
	STORED_OBJECT = 69	# Indicates that a storage contains an object.
	BLOB_OBJECT = 70	# Indicates that a blob contains an object.
	CF = 71 		# Indicates the clipboard format.
	CLSID = 72		# Indicates a class ID.
	VECTOR = 4096	# Indicates a simple,counted array.
	ARRAY = 8192	# Indicates a SAFEARRAY pointer.
	BYREF = 16384   # Indicates that a value is a reference.


class RecordType(Enum):
	Uninitialized = 0		# Uninitialized value, indicating the RecordType has not not been set.
	Sampled = 1			# Item value only is sampled, at a specific resolution. (No quality data is stored.)
	SampledWithQuality = 2	# Item value and quality, is sampled at a specific resolution.
	Eventbased = 3			# Item value, quality and timetamp, is stored at a free resolution.

class RunningMode(Enum):
	Online = 1			# The database is online in normal operation. Reading and writing can be done.
	Admin = 2			# The database is in administrative mode. No r/w, properties can be changed.
	Disabled = 5		# The database has been disabled. 
	OnlineNoCache = 6	# The database is on-line without caching operation. Reading and imports can be done, no write	

def get_enum_value(enum, key):
	if isinstance(key, enum):
		return key.value
	elif isinstance(key, str):
		norm_key = key.casefold()
		for e in enum:
			if e.name.casefold()==norm_key:
				return e.value
		raise KeyError(f'No match for {key} found in {enum}.')
	raise Error('Unknown key type. Expected str or enum.')

def to_pydatetime(dt: System.DateTime):
    "convert a .NET DateTime to a python datetime object"
    tmp = datetime(dt.Year, dt.Month, dt.Day, dt.Hour, dt.Minute, dt.Second, dt.Millisecond * 1000)

def fm_pydatetime(dt: datetime):
    "convert a python datetime object to .NET DateTime object"
    tmp = System.DateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    millis = int(dt.microsecond / 1000)
    return tmp.AddMilliseconds(millis)

def _normalize_arguments(attr, kw):
    """Internal function. Normalize arguments as dicts {name:value} and return new dict
    with lowercase names. If the Attr argument is None, an empty dict is returned instead.
    The argument kw must be a dict.
    """
    new_attr = list((attr or {}).items()) + list(kw.items())
    return dict((k.casefold(), v) for k,v in new_attr)

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
		return self.name

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
			raise AttributeError(f"Attribute {self.name} is read only")

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


class HiveAttribute(BaseAttribute):
	"""
	Attribtes/properties for use in Hive-module propertiess and Hive Item attributes
	"""
	def __str__(self):
		return f"{self.name}={self.value}"


class BaseContainer:
    pass



