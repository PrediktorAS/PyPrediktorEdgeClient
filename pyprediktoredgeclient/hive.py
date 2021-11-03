import os
import sys
import pkg_resources
from clr import System

# Check for the DLLS
if not pkg_resources.resource_exists(__name__, "dlls"):
	raise Exception("DLLS Not present in folder")

# Check that it is a folder
if not pkg_resources.resource_isdir(__name__, "dlls"):
	raise Exception("DLLS is not a folder")

# Check each file
for f in ['ApisNetUtilities.dll', 'HiveNetApi.dll', 'Microsoft.Win32.Registry.dll', 'netstandard.dll', 'Prediktor.Log.dll', 'SentinelRMSCore.dll']:
	if not pkg_resources.resource_exists(__name__, "dlls/{}".format(f)):
		raise Exception("DLL {} is not present".format(f))


try:
	System.Reflection.Assembly.LoadFile(pkg_resources.resource_stream(__name__, "dlls/HiveNetApi.dll"))
except Exception as e:
	raise Exception("DLLS: {} Not found", e.args)

import Prediktor

def Instances():
	return Prediktor.APIS.Hive.HiveInstanceService.GetRegisteredInstances()

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
		return "<Apis.Hive instance: {}>".format(self)

	def __len__(self):
		return len(self.api.GetModules())

	def __getitem__(self, key):
		return self.get_module(key)

	def __iter(self):
		return self.api.GetModules()

	def modules(self):
		"""Return a list containing all the modules in this hive instance"""
		return [ Module(self, obj) for obj in self.api.GetModules() ]

	def get_module(self, key):
		"""Return the module with the specified name or index"""
		objs = self.api.GetModules()
		if isinstance(key, Module):
			return key

		if isinstance(key, int):
			return Module(self, objs[key])

		if isinstance(key, str):
			for obj in self.api.GetModules():
				if str(obj) == key:
					return Module(self, obj)

			raise Error("Invalid module name: ''".format(key))
		raise Error("Invalid index type: {}".format(type(key).__name__))

	def types(self):
		"""Return a list containing the name of all known module+types. These
		names can be used as input to Hive.add_module().
		"""
		return [ obj for obj in self.api.ModuleTypes ]

	def add_module(self, type, name=None):
		"""Create and return a new Hive.Module in the Hive.

		Arguments:
		type: the name of a module type
		name: the name of the new module (default is None, i.e. use a generated name based on moduletype)
		"""
		if name is not None:
			type.set_InstanceName(name)
		obj = self.api.AddModule(type)
		return Module(self, obj)



class Module:
	"""Class used to access a specific module in an ApisHive instance. The
	Module is a wrapper around Prediktor.APIS.HiveWrapper.Module, which can
	be accessed through the 'Module.api' member.
	"""
	def __init__(self, hive, api):
		self.hive = hive
		self.api = api

	def __str__(self):
		return self.name()

	def __repr__(self):
		return "<Apis.Hive.Module: >".format(self)

	def __len__(self):
		return len(self.api.GetItems())

	def __getitem__(self, key):
		return self.get_item(key)

	def __iter(self):
		return self.api.GetItems()

	def name(self):
		return self.api.Name

	def items(self):
		"""Return a list containing all the items in this module"""
		return [ Item(self, obj) for obj in self.api.GetItems() ]

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
			raise Error("Invalid item name: '{}'".format(key))

		raise Error("Invalid index type: {}".format(type(key).__name__))

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
		return "{}={}".format(self.name(), self.value())

	def __repr__(self):
		return "<Apis.Hive.Module.Property: {}>".format(self)

	def name(self):
		return self.api.Name

	def desc(self):
		return self.api.Description

	def value(self):
		return self.api.Value

	def update(self, value):
		self.api.Value = value


class Item:
	def __init__(self, module, api):
		self.module = module
		self.api = api

	def __str__(self):
		return self.name()

	def __repr__(self):
		return "<Apis.Hive.Module.Property: >".format(self)

	def __len__(self):
		return len(self.api.GetAttributes())

	def __getitem__(self, key):
		return self.get_attr(key)

	def __iter(self):
		return self.api.GetAttributes()

	def name(self):
		return self.api.Name

	def value(self):
		return self['Value'].value()

	def attrs(self):
		return [ Attr(self, obj) for obj in self.api.GetAttributes() ]

	def get_attr(self, key):
		"""Return the attr with the specified name or index"""
		if isinstance(key, Attr):
			return key

		if isinstance(key, int):
			return Attr(self, self.api.GetAttributes()[key])

		if isinstance(key, str):
			for obj in self.api.GetAttributes():
				if obj.Name == key:
					return Attr(self, obj)
			raise Error("Invalid attribute name: '{}'".format(key))

		raise Error("Invalid index type: {}".format(type(key).__name__))


class Attr:
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def __str__(self):
		return "{}={}".format(self.name(), self.value())

	def __repr__(self):
		return "<Apis.Hive.Module.Attr: {}>".format(self)

	def name(self):
		return self.api.Name

	def value(self):
		return self.api.Value
