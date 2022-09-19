"""
The classes and functions for accessing and manipulating Apis Honeystore databases
"""

import clr
import functools
import datetime
import collections
import collections.abc
import operator
import System
from build.lib.pyprediktoredgeclient.util import fm_pydatetime

from .util import (
	AttrFlags, Prediktor, Error, ItemVQT, Quality, 
	RecordType, get_enum_value, to_pydatetime, BaseAttribute, VariantType, RunningMode
)



class Honeystore:
	"""Class used to access one Apis Honeystore instance. The instance is a
	wrapper around a Prediktor.Apis.Honyestore instance, which
	can be accessed through the 'Honeystore.api' member.

	A Honeystore instance is iterable; iterating over the instance will return
	each database of the instance.
	"""

	DEFAULT_HIST_LENGTH = 60*60*24*365		# Also known as 'one year'
	DEFAULT_STR_LEN = 32		# Also known as 'one year'

	def __init__(self, host_name=None):
		"""Connect to a Honeystore 

		Arguments:
		server_name: optional name of the server hosting Honeystore (default is None, i.e. "localhost")
		"""
		if host_name:
			self.api = Prediktor.APIS.Honeystore.Honeystore.CreateServerEx(host_name)
		else:
			self.api = Prediktor.APIS.Honeystore.Honeystore.CreateServer() 

	def __str__(self):
		return self.name

	def __repr__(self):
		return f"<Apis.{self.__class__.__name__} instance: {self}>"

	def __len__(self):
		return len(self.api.GetDatabases())

	def __getitem__(self, key):
		return self.get_database(key)

	def __delitem__(self, key):
		return self.get_database(key).delete()

	def __iter__(self):
		return iter(self.databases)

	@property
	def name(self):
		return self.api.ConfigurationName

	def list_databases(self):
		return [Database(self, db) for db in self.api.GetDatabases()]

	databases = property(list_databases, doc="Return a list containing all the databases in this honeystore")

	def get_database(self, key):
		"""Return the database with the specified name or index"""
		if isinstance(key, Database):
			return key

		objs = self.api.GetDatabases()

		if isinstance(key, int):
			return Database(self, objs[key])

		if isinstance(key, str):
			for obj in objs:
				search_key = key.casefold()
				if obj.Name.casefold() == search_key:
					return Database(self, obj)
			raise Error(f"Invalid module name: '{key}'")

		raise Error(f"Invalid index type: {type(key).__name__}")

	def add_database(self, name, path, max_items=1000, cache_size=10040):
		"""
		Add a new database to the Honestore server.

		Arguments:
		name: str.       The name of the new database. 
		path: str.       The storage path for the database data
		max_items: int.  The inital maximum number of items in the database
		cache_size: int. The cache size in the database.
		"""
		db, path, max_items, cache_size = self.api.CreateDatabase(name, path, max_items, cache_size)
		return Database(self, db)

class Database:
	def __init__(self, honyestore, api):
		super().__setattr__('honeystore', honyestore)
		super().__setattr__('api', api)

	def __str__(self):
		return self.name

	def __repr__(self):
		return f"<Apis.Honeystore.Database: {self}>"

	def __len__(self):
		return len(self.api.GetItems())

	def __getitem__(self, key):
		return self.get_item(key)

	def __delitem__(self, key):
		self.get_item(key).api.DeleteItem()

	def __iter__(self):
		return self.api.GetItems()

	def __getattr__(self, key):
		return self.get_property(key).value

	def __setattr__(self, key, value):
		try:
			prop = self.get_property(key)
			prop.value = value
		except Error:
			super().__setattr__(key, value)

	@property
	def name(self):
		return self.api.Name

	@property
	def items(self):
		"""Return a list containing all the items in this database"""
		return [ Item(self, obj) for obj in list(self.api.GetItems()) ]

	def get_item(self, key):
		"""Return the item with the specified name or index"""
		if isinstance(key, Item):
			return key

		if isinstance(key, int):
			return Item(self, self.api.GetItems()[key])

		if isinstance(key, str):
			nkey = key.casefold()
			for obj in self.api.GetItems():
				if obj.Name.casefold() == nkey:
					return Item(self, obj)
			raise Error(f"Invalid honeystore item name: '{key}'")

		raise Error(f"Invalid index type: {type(key).__name__}")

	def add_item(self, item, var_type=VariantType.R8, record_type=RecordType.Eventbased, resolution=1000, array_size=0, history_length=0):
		"""Add a new item to the honeystore
		
		Arguments:
		item_name: a string or an object with an 'item_id' property
		var_type: The variable type to use. Either a string or a VariantType enum value
		record_type: The recordtype to use. Either a string or a RecordType enum value
		array_size: The arraylength of for vector or mulitidim data. If you pass a tuple here the elements
				in the tuple describes the dimensions
		history_length: integer. Lenght of horizon in seconds

		"""
		assert not array_size, "Array size has to be 0 at the moment."

		item_id = getattr(item, 'item_id', str(item))
		v_type = get_enum_value(VariantType, var_type)
		if v_type==VariantType.BSTR.value:
			rec_len = array_size or Honeystore.DEFAULT_STR_LEN
		elif array_size:
			rec_len = get_storage_size(var_type, array_size)
			v_type |= VariantType.ARRAY.value		#Promised in python.net 3.0
		else:
			rec_len = 0

		print(rec_len)

		item_data =  Prediktor.APIS.Honeystore.Structs.AddItemDefinitions()
		item_data.Name = item_id
		item_data.VarType = v_type
		item_data.RecType = get_enum_value(RecordType, record_type)
		item_data.HistoryLength = history_length or Honeystore.DEFAULT_HIST_LENGTH
		item_data.Resolution = resolution
		item_data.ValueSize = rec_len

		defs = System.Array[Prediktor.APIS.Honeystore.Structs.AddItemDefinitions]([item_data])

		new_items = self.api.AddItems(defs)
		return Item(self, new_items[0])

	def _get_property(self, name):
		for obj in self.api.GetProperties():
			if obj.Name == name:
				return obj
		raise Error(f"property '{name}' not found")

	@property
	def properties(self):
		return [ Property(self, obj) for obj in self.api.GetProperties() ]

	def get_property(self, name):
		return Property(self, self._get_property(name))

	def delete(self):
		return self.api.DeleteDatabase()

	def get_runningmode(self):
		return RunningMode(self.api.Mode)

	def set_runningmode(self, mode):
		self.api.Mode = get_enum_value(RunningMode, mode)

	mode = property(get_runningmode, set_runningmode)

class Property(BaseAttribute):
	def __init__(self, database, api):
		self.database = database
		self.api = api

	def get_eunumeration(self):
		return self.database.api.GetProperties()
		

class Item:
	def __init__(self, module, api):
		super().__setattr__('module', module)		#due to __settattr__
		super().__setattr__('api', api)

	def __str__(self):
		return self.name

	def __repr__(self):
		return f"<Apis.Honeystore.Item: {self.name}>"

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


	def add_attr(self, attr, value=None):
		"""
		Add an attribute to an Apis Item.

		Arguments:
		attr: an Attr (i.e from another item) or a string attribute name 
		value: Optional value
		"""

		hive = self.module.hive
		if isinstance(attr, str):
			new_attr = hive.get_item_attribute(attr)
		elif isinstance(attr, Attr):
			new_attr = hive.get_item_attribute(attr.name)
		else:
			raise Error('Invalid type for attribute name')

		if new_attr.flag ^ AttrFlags.ReadOnly:
			if value is not None:
				new_attr.value = value
			elif isinstance(attr, Attr):
				new_attr.value = attr.value

		attr_array = System.Array[Prediktor.APIS.Hive.IAttribute]([new_attr.api])
		set_attr = self.api.SetAttributes(attr_array)

		return Attr(self, set_attr[0])


	def delete_history(self, start, end):
		self.api.DeleteHistory(fm_pydatetime(start), fm_pydatetime(end))


class Attr(BaseAttribute):
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def get_eunumeration(self):
		return self.item.database.api.GetProperties()


	def __repr__(self):
		return f"<Apis.Honeystore.Item.Attr: {self}>"	


def get_array_size(array_dimensions):
	"""
	Get the storage size given the data type and array dimensions

	Arguments:
	array_dimensions: int or tuple of integers. If this argument is an int, an array is assumed. 
		otherwise the array dimension is the length of `array_dimensions`
	"""
	if isinstance(array_dimensions, int):
		return 1, array_dimensions
	try:
		return len(array_dimensions), functools.reduce(operator.mul, array_dimensions, 1)
	except TypeError:
		raise Error('array_dimensions must be int or sequence of int')


def get_storage_size(var_type, array_dimensions=None):
	"""
	Get the storage size given the data type and array dimensions

	Arguments:
	var_type: string, VariantType or int. The variable storage type
	array_dimensions: int or tuple of integers. If this argument is an int, an array is assumed. 
		otherwise the array dimension is the length of `array_dimensions`
	"""
	elem_size = Prediktor.APIS.Honeystore.Honeystore.Vartype2ValueSize(get_enum_value(VariantType, var_type))

	if array_dimensions is None:
		return 0
	dim, size = get_array_size(array_dimensions)
	return Prediktor.APIS.Honeystore.Honeystore.ValueSizeForArray(dim, size, elem_size)

