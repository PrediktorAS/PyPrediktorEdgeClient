__all__ = 'Instances', 'Error', 'Hive', 'Module', 'Attr', 'Property', 'Item', 'ItemVQT'

import pkg_resources
import clr
import functools
import datetime
import collections
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

AttrFlags = Prediktor.APIS.Hive.Flags

ItemVQT = collections.namedtuple('ItemVQT', 'item_id value quality time')

class Error(Exception):
	"""Generic exception used to report problems in Apis.py"""
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg


class Hive:
	"""Class used to access one ApisHive instance. The instance is a
	wrapper around a Prediktor.Apis.HiveWrapper.Hive instance, which
	can be accessed through the 'Hive.api' member.

	A Hive instance is iterable; iterating over the instance will return
	each module of the instance.

	A Hive instance is indexable by module name.
	"""

	def __init__(self, instance_name=None, server_name=None):
		"""Connect to a hive instance, starting the instance if needed.

		Arguments:
		instance_name: optional name of the instance (default is None, i.e. the "ApisHive" instance)
		server_name: optional name of the server hostting the instance (default is None, i.e. "localhost")
		"""
		self.api = Prediktor.APIS.Hive.Hive.CreateServer(instance_name, server_name)
		self._modtypes = { str(obj):obj for obj in self.api.ModuleTypes }


	def __str__(self):
		return self.api.ConfigurationName

	def __repr__(self):
		return f"<Apis.Hive instance: {self}>"

	def __len__(self):
		return len(self.api.GetModules())

	def __getitem__(self, key):
		return self.get_module(key)

	def __delitem__(self, key):
		return self.get_module(key).delete()

	def __iter__(self):
		return self.api.GetModules()

	@property
	def modules(self):
		"""Return a list containing all the modules in this hive instance"""
		return [ Module(self, obj) for obj in self.api.GetModules() ]

	def get_module(self, key):
		"""Return the module with the specified name or index"""
		if isinstance(key, Module):
			return key

		objs = self.api.GetModules()

		if isinstance(key, int):
			return Module(self, objs[key])

		if isinstance(key, str):
			for obj in self.api.GetModules():
				if str(obj) == key:
					return Module(self, obj)

			raise Error(f"Invalid module name: '{key}'")
		raise Error(f"Invalid index type: {type(key).__name__}")

	@property
	def module_types(self):
		"""Return a list containing the name of all known module+types. These
		names can be used as input to Hive.add_module().
		"""
		return list(self.api.ModuleTypes)


	def add_module(self, module_type, name=None):
		"""Create and return a new Hive.Module in the Hive.

		Arguments:
		type: the name of a module type
		name: the name of the new module (default is None, i.e. use a generated name based on moduletype)
		"""
		if isinstance(module_type, str):
			for mt in self.module_types:
				if mt.ClassName == module_type:
					module_type = mt
					break
			else:
				raise ValueError(f"Unknown module type {module_type}")

		if name is not None:
			module_type.set_InstanceName(name)
		obj = self.api.AddModule(module_type)
		return Module(self, obj)

	def get_values(self, items, since=None):
		"""
		Get a list of value-quality-itmestamps from the connected hive

		Arguments:
		items: A list of Item objects of itemId's as stings
		since (Optional): the oldest time of the values to retrieve
		"""
		if not since:
			since = System.DateTime.MinValue

		itemIds = [i.item_id if isinstance(i, Item) else str(i) for i in items]
		handles = self.api.LookupItemHandles(itemIds)

		#argument placeholders
		h_out = System.Array[System.Int32]([])
		v_out = System.Array[System.Object]([])
		q_out = System.Array[System.UInt16]([])
		t_out = System.Array[System.DateTime]([])
		err_out =  System.Array[System.Int32]([])
		check_out = System.Boolean(False)
		last_read=System.DateTime.Now

		void, h, v, q, t, err, check, tor = self.api.ReadItems(since, handles,  h_out, v_out, q_out, t_out, err_out, check_out, last_read)
		return [ItemVQT(itemIds[i], v[i], q[i], t[i]) for i in range(len(h))]

class Module:
	"""Class used to access a specific module in an ApisHive instance. The
	Module is a wrapper around Prediktor.APIS.HiveWrapper.Module, which can
	be accessed through the 'Module.api' member.
	"""
	def __init__(self, hive, api):
		self.hive = hive
		self.api = api

	def __str__(self):
		return self.name

	def __repr__(self):
		return "<Apis.Hive.Module: >".format(self)

	def __len__(self):
		return len(self.api.GetItems())

	def __getitem__(self, key):
		return self.get_item(key)

	def __delitem__(self, key):
		self.get_item(key).api.DeleteItem()

	def __iter__(self):
		return self.api.GetItems()

	@property
	def name(self):
		return self.api.Name

	@property
	def items(self):
		"""Return a list containing all the items in this module"""
		return [ Item(self, obj) for obj in list(self.api.GetItems()) ]

	def get_item(self, key):
		"""Return the item with the specified name or index"""
		if isinstance(key, Item):
			return key

		if isinstance(key, int):
			return Item(self, self.api.GetItems()[key])

		if isinstance(key, str):
			for obj in self.api.GetItems():
				if obj.Name == key:
					return Item(self, obj)
			raise Error(f"Invalid item name: '{key}'")

		raise Error(f"Invalid index type: {type(key).__name__}")

	@property
	def item_types(self):
		"""Return the available item types for this  module"""
		return list(self.api.GetItemTypes())


	def add_item(self, item_type, item_name):
		"""Add a new item to the hive"""
		if isinstance(item_type, str):
			for it in self.item_types:
				if it.Name==item_type:
					item_type = it
					break
			else:
				raise ValueError(f"unknown item type {item_type}")
		
		template = it.GetNewItemTemplate(item_name)
		item, item_error, attr_error, check = self.api.AddItems([template], None, None, None)
		if check:
			for i, a_e in enumerate(attr_error):
				if a_e > 0:
					t_attr = template.Attributes[i]
					raise Error(f"Error setting {t_attr.Name}")

		return Item(self, item[0])

	@property
	def properties(self):
		return [ Property(self, obj) for obj in self.api.GetProperties() ]

	def get_property(self, name):
		for obj in self.api.GetProperties():
			if str(obj) == name:
				return Property(self, obj)

	def delete(self):
		return self.api.DeleteModule()

class Property:
	def __init__(self, module, api):
		self.module = module
		self.api = api

	def __str__(self):
		return f"{self.name}={self.value}"

	def __repr__(self):
		return f"<Apis.Hive.Module.Property: {self}>"

	@property
	def name(self):
		return self.api.Name

	def desc(self):
		return self.api.Description

	@property
	def value(self):
		return self.api.Value

	def update(self, value):
		self.api.Value = value


class Item:
	def __init__(self, module, api):
		super().__setattr__('module', module)
		super().__setattr__('api', api)
		# self.module = module
		# self.api = api

	def __str__(self):
		return self.name

	def __repr__(self):
		return f"<Apis.Hive.Module.Item: {self.name}>"

	def __len__(self):
		return len(self.attr)

	def __getitem__(self, key):
		return self.get_attr(key).value

	__getattr__ = __getitem__

	def __setitem__(self, key, value):
		attr = self.get_attr(key)
		attr.value = value

	def __setattr__(self, key, value):
		try:
			attr = self.get_attr(key)
			attr.value = value

		except Error:
			super().__setattr__(key, value)

	def __iter__(self):
		return self.api.GetAttributes()

	@property
	def name(self):
		"The item name. Unique within a module"
		return self.api.Name

	@property
	def item_id(self):
		"The item-id. . Unique within a hive"
		return self.api.ItemID


	def get_attr(self, key):
		"""Return the attr with the specified name or index"""
		if isinstance(key, Attr):
			return key
		if isinstance(key, str):
			for attr in self.api.GetAttributes():
				if attr.Name == key:
					return Attr(self, attr)
		if isinstance(key, int):
			return Attr(self, self.api.GetAttributes()[key])
		raise Error(f"Invalid index: {repr(key)}")



class Attr:
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def __str__(self):
		return "{self.name}={self.value}"

	def __repr__(self):
		return f"<Apis.Hive.Module.Attr: {self}>"

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
				if str(val)==value:
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


