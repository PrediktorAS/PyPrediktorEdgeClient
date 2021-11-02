from __future__ import print_function
import os
import sys
import clr

sys.path.append(os.path.join(os.getcwd(), 'dlls'))

clr.AddReference("HiveNetApi")
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
		self._modtypes = {}
		for obj in self.api.ModuleTypes:
			self._modtypes[str(obj)] = obj

	def __str__(self):
		return self.api.ConfigurationName

	def __repr__(self):
		return "<Apis.Hive instance: " + str(self) + ">"

	def __len__(self):
		return len(self.api.GetModules())

	def __getitem__(self, key):
		return self.get_module(key)

	def __iter(self):
		return self.api.GetModules()

	def modules(self):
		"""Return a list containing all the modules in this hive instance"""
		tmp = []
		for obj in self.api.GetModules():
			tmp.append(Module(self, obj))
		return tmp

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
			raise Error("Invalid module name: '" + key + "'")
		raise Error("Invalid index type: " + type(key).__name__)

	def types(self):
		"""Return a list containing the name of all known module+types. These
		names can be used as input to Hive.add_module().
		"""
		tmp = []
		for obj in self.api.ModuleTypes:
			tmp.append(obj)
		return tmp

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
		return "<Apis.Hive.Module: " + str(self) + ">"

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
		tmp = []
		for obj in self.api.GetItems():
			tmp.append(Item(self, obj))
		return tmp

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
			raise Error("Invalid item name: '" + key + "'")

		raise Error("Invalid index type: " + type(key).__name__)

	def properties(self):
		tmp = []
		for obj in self.api.GetProperties():
			tmp.append(Property(self, obj))
		return tmp

	def get_property(self, name):
		props = {}
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
		return self.name() + "=" + str(self.value())

	def __repr__(self):
		return "<Apis.Hive.Module.Property: " + str(self) + ">"

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
		return "<Apis.Hive.Module.Property: " + str(self) + ">"

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
		tmp = []
		for obj in self.api.GetAttributes():
			tmp.append(Attr(self, obj))
		return tmp

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
			raise Error("Invalid attribute name: '" + key + "'")

		raise Error("Invalid index type: " + type(key).__name__)


class Attr:
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def __str__(self):
		return self.name() + "=" + str(self.value())

	def __repr__(self):
		return "<Apis.Hive.Module.Attr: " + str(self) + ">"

	def name(self):
		return self.api.Name

	def value(self):
		return self.api.Value
