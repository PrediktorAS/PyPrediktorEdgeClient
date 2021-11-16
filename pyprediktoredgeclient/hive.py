__all__ = 'Instances', 'Error', 'Hive', 'Module', 'Attr', 'Property', 'Item', 'ItemVQT'

from itertools import chain
from typing import Tuple
import pkg_resources
import clr
import functools
import datetime
import collections
import System

from .util import AttrFlags, Prediktor, Error, ItemVQT, Quality, to_pydatetime, fm_pydatetime, BaseAttribute
from .hiveservices import HiveInstance

class Hive:
	"""Class used to access one ApisHive instance. The instance is a
	wrapper around a Prediktor.Apis.HiveWrapper.Hive instance, which
	can be accessed through the 'Hive.api' member.

	A Hive instance is iterable; iterating over the instance will return
	each module of the instance.

	A Hive instance is indexable by module name.
	"""


	def __init__(self, instance=None, server_name=None):
		"""Connect to a hive instance, starting the instance if needed.

		Arguments:
		instance_name: optional name of the instance (default is None, i.e. the "ApisHive" instance)
		server_name: optional name of the server hostting the instance (default is None, i.e. "localhost")
		"""
		instance_name = instance.prog_id if hasattr(instance, 'prog_id') else instance

		self.api = Prediktor.APIS.Hive.Hive.CreateServer(instance_name, server_name)
		self._modtypes = { str(obj):obj for obj in self.api.ModuleTypes }

	def __str__(self):
		return self.name

	def __repr__(self):
		return f"<Apis.Hive instance: {self}>"

	def __len__(self):
		return len(self.api.GetModules())

	def __getitem__(self, key):
		return self.get_module(key)

	def __delitem__(self, key):
		return self.get_module(key).delete()

	def __iter__(self):
		return iter(self.modules)

	@property
	def name(self):
		return self.api.ConfigurationName

	@property
	def modules(self):
		"""Return a list containing all the modules in this hive instance"""
		return [ Module(self, obj) for obj in self.api.GetModules() ]

	def get_eventserver(self):
		return EventServer(self, self.api.GetEventServer())

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


	def _get_attrib(self):
		return chain(self.api.GetSupportedAttributes(), self.api.GetGlobalAttributes())

	def get_item_attributes(self):
		"""
		Get all attributes available to items in the system
		"""
		return [Attr(None, attr) for attr in self._get_attrib()]

	def get_item_attribute(self, name):
		"""
		Get an attribute that can be used to set on an Item
		"""
		for attr in self._get_attrib():
			if attr.Name == name:
				return Attr(None, attr)
		raise Error(f'Attribute {name} not found.')

	@property
	def module_types(self):
		"""Return a list containing the name of all known module+types. These
		names can be used as input to Hive.add_module().
		"""
		return [ModuleType(self, mt) for mt in self._modtypes.values()]

	def get_module_type(self, type_name):
		"""Return a list containing the name of all known module+types. These
		names can be used as input to Hive.add_module().
		"""
		for mt in self._modtypes.values():
			if mt.ClassName == type_name:
				return ModuleType(self,  mt)
		else:
			raise Error(f"Unknown module type {type_name}")


	def add_module(self, module_type, name=None):
		"""Create and return a new Hive.Module in the Hive.

		Arguments:
		type: the name of a module type
		name: the name of the new module (default is None, i.e. use a generated name based on moduletype)
		"""
		if isinstance(module_type, str):
			module_type = self.get_module_type(module_type)
		elif not isinstance(module_type, ModuleType):
			raise Error(f"Invalid argument for module_type {type(module_type)}")

		if name is not None:
			module_type.api.InstanceName = name

		obj = self.api.AddModule(module_type.api)
		obj.ApplyCurrentRunningState()
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

		pack_result = lambda i:ItemVQT(itemIds[i], v[i], Quality(q[i]), to_pydatetime(t[i]))

		return [pack_result(i) for i in range(len(h))]

class ModuleType:
	"""
	The class wraps an Apis module-type
	"""
	def __init__(self, hive, api):
		self.hive = hive
		self.api = api

	class_name = property(lambda self:self.api.ClassName)
	description = property(lambda self:self.api.Description)
	GUID = property(lambda self:self.api.GUID)



class Module:
	"""Class used to access a specific module in an ApisHive instance. The
	Module is a wrapper around Prediktor.APIS.HiveWrapper.Module, which can
	be accessed through the 'Module.api' member.
	"""
	def __init__(self, hive, api):
		super().__setattr__('hive', hive)
		super().__setattr__('api', api)

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


	def __getattr__(self, key):
		self.get_property(key).value

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

	def get_item_type(self, name):
		for item_type in self.api.GetItemTypes():
			if item_type.Name == name:
				return item_type
		raise Error(f'Unknown item type {name}')

	def add_item(self, item_type, item_name):
		"""Add a new item to the hive"""
		if isinstance(item_type, str):
			item_type = self.get_item_type(item_type)
		
		template = item_type.GetNewItemTemplate(item_name)
		item, item_error, attr_error, check = self.api.AddItems([template], None, None, None)
		if check:
			for i, a_e in enumerate(attr_error):
				if a_e > 0:
					t_attr = template.Attributes[i]
					raise Error(f"Error setting {t_attr.Name}")

		return Item(self, item[0])

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
		return self.api.DeleteModule()

class Property(BaseAttribute):
	def __init__(self, module, api):
		self.module = module
		self.api = api

	def __repr__(self):
		return f"<Apis.Hive.Module.Property: {self}>"


class Item:
	def __init__(self, module, api):
		super().__setattr__('module', module)		#due to __settattr__
		super().__setattr__('api', api)

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

	def get_externalitems(self):
		"""
		Get the external items from an item and return as a list of `Item`s
		"""
		modules = {mod.name:mod for mod in self.module.hive.modules}
		def getitems():
			for extitem in self.api.GetExternalItems():
				yield Item(modules[extitem.Item.Module.Name], extitem.Item)
		return list(getitems())

	def set_externalitems(self, ext_items):
		"""
		Set external items.

		Arguements:
		ext_items: The external items, either as a string or as an Item 
		"""
		hive = self.module.hive
		def normalize(items):
			for item in items:
				if isinstance(item, str):
					yield item
				elif hasattr(item, 'item_id'):
					yield item.item_id
				else:
					raise Error(f"Item {repr(item)} can't be used")
		items = hive.api.LookupItems(list(normalize(ext_items)))
		new_ext_items = [item.GetAsExternalItem(i+1) for (i,item) in enumerate(items)]
		self.api.SetExternalItems(new_ext_items)

	external_items = property(get_externalitems,set_externalitems, doc="Set or get external items")




class Attr(BaseAttribute):
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def __repr__(self):
		return f"<Apis.Hive.Module.Attr: {self}>"


class EventServer:
	"""Class used to access the EventServer (and Chronical) in an APIS HIVE instance"""
	def __init__(self, hive, api):
		self.hive = hive
		self.api = api
		self.browse_flags = Prediktor.APIS.Hive.EventSearchOptions
	
	def get_config(self):
		result = {}
		for obj in self.api.GetOptions():
			result[obj.Name] = obj.Value
		return result

	def get_datatypes(self):
		tmp = self.api.GetEventDataTypes()
		result = {}
		for i in tmp:
			result[i.Datatype] = EventServer.Datatype(self, i.Datatype, i.Name)
		return result

	def get_eventtypes(self):
		id = 1
		result = {}
		while (True):
			try:
				tmp = self.api.GetEventType(id)
			except Prediktor.APIS.Hive.HiveException as e:
				if (e.HResult != -536870906):
					print(f"Unexpected error: {e}")
				break
			result[tmp.Id] = EventServer.EventType(self, tmp.Id, tmp.Name, tmp.ParentId, tmp.Flags)
			id += 1
		return result

	def get_eventfields(self):
		id = 1
		result = {}
		while (True):
			try:
				tmp = self.api.GetEventField(id)
			except Prediktor.APIS.Hive.HiveException as e:
				if (e.HResult != -536870906):
					print(f"Unexpected error: {e}")
				break
			result[tmp.Id] = EventServer.EventField(self, tmp.Id, tmp.Name, tmp.EventTypeId, tmp.Datatype, tmp.Flags)
			id += 1
		return result

	def browse(self, pattern, flags, max_count = 1000):
		return self.api.FindSources(0, flags, pattern, max_count, None, None)

	def query(self, starttime, endtime, eventsource, eventtype, filter, maxrows = 1000):
		list = Prediktor.APIS.Hive.EventServer.EventList()
		fields = System.Array[System.Int32]([1,2,3,4,5,6,7,8])
		batchsize = 65535
		if (batchsize > maxrows):
			batchsize = maxrows
		qry = self.api.QueryFirst2(list, True, fm_pydatetime(starttime), fm_pydatetime(endtime), eventsource, eventtype, 0, 0, 0, 1000, filter, batchsize, fields)
		more = qry.MoreData
		while more and list.Count < maxrows:
			more = self.api.QueryNext(qry.Handle)
			count = list.Count
		self.api.QueryDone(qry.Handle)
		return list.Detach()

	class Datatype:
		def __init__(self, owner, id, name):
			self.owner = owner
			self.id = id
			self.name = name

	class EventType:
		def __init__(self, owner, id, name, parent, flags):
			self.owner = owner
			self.id = id
			self.name = name
			self.parent = parent
			self.flags = flags

		def get_fields(self, inherited = False):
			return self.owner.api.GetEventFields(self.id, inherited)

	class EventField:
		def __init__(self, owner, id, name, eventtype, vt, flags):
			self.owner = owner
			self.id = id
			self.name = name
			self.eventtype = eventtype
			self.vt = vt
			self.flags = flags
