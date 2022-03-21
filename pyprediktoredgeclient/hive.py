__all__ = 'Instances', 'Error', 'Hive', 'Module', 'Attr', 'Property', 'Item', 'ItemVQT', 'EventServer'

from itertools import chain
from typing import Tuple, List, Union, AnyStr
import pkg_resources
import clr
import functools
import datetime
import collections
import System

from .util import (
	AttrFlags, BaseContainer, Prediktor, Error, ItemVQT, Quality, _normalize_arguments, _normalize_input, to_pydatetime, 
	fm_pydatetime, HiveAttribute)

from .hiveservices import HiveInstance
from .semantic_service import SemanticService

class Hive:
	"""Class used to access one ApisHive instance. The instance is a
	wrapper around a Prediktor.Apis.HiveWrapper.Hive instance, which
	can be accessed through the 'Hive.api' member.

	A Hive instance is iterable; iterating over the instance will return
	each module of the instance.

	A Hive instance is indexable by module name.
	"""


	def __init__(self, instance=None, host_name=None):
		"""Connect to a hive instance, starting the instance if needed.

		Arguments:
		instance_name: optional name of the instance (default is None, i.e. the "ApisHive" instance)
		host_name: optional name of the server hostting the instance (default is None, i.e. "localhost")
		"""
		instance_name = instance.prog_id if hasattr(instance, 'prog_id') else instance

		self.api = Prediktor.APIS.Hive.Hive.CreateServer(instance_name, host_name)
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

	def __contains__(self, mod):
		try:
			return isinstance(self.get_module(mod), Module)
		except Error:
			return False



	@property
	def name(self):
		return self.api.ConfigurationName

	@property
	def runstate(self):
		return self.api.RunningState

	@property
	def modules(self):
		"""Return a list containing all the modules in this hive instance"""
		return [ Module(self, obj) for obj in self.api.GetModules() ]

	def get_eventserver(self):
		return EventServer(self, self.api.GetEventServer())

	def get_eventbroker(self):
		return EventBroker(self)

	def get_endpoints(self):
		return EndpointList(self, self.api.GetEndpointsConfig())

	def get_module(self, key):
		"""Return the module with the specified name or index"""
		if isinstance(key, Module):
			return key

		modules = self.api.GetModules()

		if isinstance(key, int):
			return Module(self, modules[key])

		if isinstance(key, str):
			search_key = _normalize_input(key)
			for mod in modules:
				if _normalize_input(mod.Name) == search_key:
					return Module(self, mod)

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
		search_key = _normalize_input(name)
		for attr in self._get_attrib():
			if _normalize_input(attr.Name) == search_key:
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
		search_key = _normalize_input(type_name)
		for mt in self._modtypes.values():
			if _normalize_input(mt.ClassName) == search_key:
				return ModuleType(self,  mt)
		else:
			raise Error(f"Unknown module type {type_name}")



	def add_module(self, module_type, name:str=None, properties: dict = None, **kw):
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

		raw_mod = self.api.AddModule(module_type.api)
		mod = Module(self, raw_mod)
		mod.set_properties(properties, **kw)
		mod.api.ApplyCurrentRunningState()
		return mod

	def find_module_index(self, mod_name):
		if isinstance(mod_name, Module):
			search_name = _normalize_input(mod_name.name)
		else:
			search_name = _normalize_input(mod_name)

		for i, mod in enumerate(self.modules):
			if _normalize_input(mod.name) == search_name:
				return i

		raise Error(f"Module not found: {mod_name}")

	# def get_module(self, key):
	# 	if isinstance(key, str):
	# 		key = self.find_module_index(key)
	# 	return self.modules[key]

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

	@property
	def semantics_service(self):
		return SemanticService(self)

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


class Module(BaseContainer):
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
		return self.get_property(key).value

	def __setattr__(self, key, value):
		try:
			prop = self.get_property(key)
			prop.value = value
		except Error:
			super().__setattr__(key, value)

	def set_properties(self, properties: dict = None, **kw):
		"Set several properties at once"
		new_val = _normalize_arguments(properties, kw)
		for raw_prop in self.api.GetProperties():
			prop_name = _normalize_input(raw_prop.Name, True)
			if prop_name in new_val:
				prop = Property(self, raw_prop)
				prop.value = new_val[prop_name]

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
			search_key = _normalize_input(key)
			for obj in self.api.GetItems():
				if _normalize_input(obj.Name, True) == key:
					return Item(self, obj)
			raise Error(f"Invalid item name: '{key}'")

		raise Error(f"Invalid index type: {type(key).__name__}")

	@property
	def item_types(self):
		"""Return the available item types for this  module"""
		return list(self.api.GetItemTypes())

	def get_item_type(self, name: str):
		search_key = _normalize_input(name)
		for item_type in self.api.GetItemTypes():
			if _normalize_input(item_type.Name) == search_key:
				return item_type
		raise Error(f'Unknown item type {name}')

	def _add_items(self, template):
		raw_items, item_error, attr_error, check = self.api.AddItems(template, None, None, None)
		if check:
			for i, a_e in enumerate(attr_error):
				if a_e > 0:
					t_attr = template.Attributes[i]
					raise Error(f"Error setting {t_attr.Name}")
		return [Item(self, it) for it in raw_items]

	def add_item(self, item_type, item_name:str, attrs: dict = None, **kw):
		"""Add a new item to the hive"""
		if isinstance(item_type, str):
			item_type = self.get_item_type(item_type)
		
		template = item_type.GetNewItemTemplate(item_name)
		item = self._add_items([template])[0]
		item.set_attributes(attrs, **kw)
		return item

	def add_items(self, item_type, count:Union[int,range], namefmt:str, attrs: dict = None, **kw):
		if isinstance(item_type, str):
			item_type = self.get_item_type(item_type)
		
		if isinstance(count, int):
			count = range(count)

		templates = [item_type.GetNewItemTemplate(namefmt.format(i)) for i in count]
		items = self._add_items(templates)
		if attrs or kw:
			for item in items:
				item.set_attributes(attrs, **kw)
		return items

	def _get_property(self, name:str):
		norm_name = _normalize_input(name)
		for obj in self.api.GetProperties():
			if _normalize_input(obj.Name) == norm_name:
				return obj
		raise Error(f"property '{name}' not found")

	@property
	def properties(self):
		return [ Property(self, obj) for obj in self.api.GetProperties() ]

	def get_property(self, name:str):
		return Property(self, self._get_property(name))

	def delete(self):
		return self.api.DeleteModule()

class Property(HiveAttribute):
	def __init__(self, module, api):
		self.module = module
		self.api = api

	def __repr__(self):
		return f"<Apis.Hive.Module.Property: {self}>"

class Item(BaseContainer):
	def __init__(self, module, api):
		super().__setattr__('module', module)		#due to __settattr__
		if (api.Handle == -1):
			api = module.get_item(api.Name).api
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

	def set_attributes(self, attributes: dict = None, **kw):
		"Set several attributes at once"
		new_val = _normalize_arguments(attributes, kw)
		for raw_attr in self.api.GetAttributes():
			attr_name = _normalize_input(raw_attr.Name, True)
			if attr_name in new_val:
				attr = Attr(self, raw_attr)
				attr.value = new_val[attr_name]

	def __iter__(self):
		return self.api.GetAttributes()

	@property
	def name(self):
		"The item name. Unique within a module"
		return self.api.Name

	@property
	def item_id(self):
		"The item-id. Unique within a hive"
		return self.api.ItemID

	@property
	def itemtype(self):
		"The item-type of the item"
		for obj in self.module.api.GetItemTypes():
			if (obj.ItemTypeID == self.api.ItemTypeID):
				return obj

	def has_attr(self, name: AnyStr) -> bool:
		for attr in self.api.GetAttributes():
			if attr.Name == name:
				return True
		return False

	def get_attr(self, key):
		"""Return the attr with the specified name or index"""
		if isinstance(key, Attr):
			return key
		if isinstance(key, str):
			norm_name = _normalize_input(key)
			for attr in self.api.GetAttributes():
				if _normalize_input(attr.Name, True) == norm_name:
					return Attr(self, attr)
		if isinstance(key, int):
			return Attr(self, self.api.GetAttributes()[key])
		raise Error(f"Invalid index: {repr(key)}")


	def get_item_attribute(self, attrname: str):
		norm_name = _normalize_input(attrname)
		for attr in self.api.GetAttributes():
			if _normalize_input(attr.Name, True) == norm_name:
				return Attr(self, attr)
		tmpl = self.itemtype.GetNewItemTemplate("")
		for attr in tmpl.Attributes:
			if _normalize_input(attr.Name) == norm_name:
				return Attr(self, attr)
		return self.module.hive.get_item_attribute(attrname)

	def add_attr(self, attr, value=None):
		"""
		Add an attribute to an Apis Item.

		Arguments:
		attr: an Attr (i.e from another item) or a string attribute name 
		value: Optional value
		"""

		hive = self.module.hive
		if isinstance(attr, str):
			new_attr = self.get_item_attribute(attr)
		elif isinstance(attr, Attr):
			new_attr = self.get_item_attribute(attr.name)
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




class Attr(HiveAttribute):
	def __init__(self, item, api):
		self.item = item
		self.api = api

	def __repr__(self):
		return f"<Apis.Hive.Item.Attr: {self}>"


class EventServer:
	"""Class used to access the EventServer (and Chronical) in an APIS HIVE instance"""

	class Datatype:
		def __init__(self, owner, id, name):
			self.owner = owner
			self.id = id
			self.name = name

	class EventSource:
		def __init__(self, owner, id, name, nodeid = None):
			self.owner = owner
			self.id = id
			self.name = name
			if nodeid is None:
				all = owner.api.GetSourceAttributes(id)
				for a in all:
					if a.Id == owner.attributes["UA_NODEID"]:
						nodeid = a.Value
						break
			self.nodeid = nodeid

	class EventType:
		def __init__(self, owner, id, name, parent, flags, nodeid = None):
			self.owner = owner
			self.id = id
			self.name = name
			self.parent = parent
			self.flags = flags
			if nodeid is None:
				all = owner.api.GetEventTypeAttributes(id)
				for a in all:
					if a.Id == owner.attributes["UA_NODEID"]:
						nodeid = a.Value
						break
			self.nodeid = nodeid

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

	def __init__(self, hive, api):
		self.hive = hive
		self.api = api
		self.browse_flags = Prediktor.APIS.Hive.EventSearchOptions
		self.attributes = {a.Name:a.Id for a in api.GetAttributeTypes()}
	
	def get_config(self):
		result = {}
		for obj in self.api.GetOptions():
			result[obj.Name] = obj.Value
		return result

	def get_datatypes(self) -> List[Datatype]:
		tmp = self.api.GetEventDataTypes()
		result = []
		for i in tmp:
			result.append(EventServer.Datatype(self, i.Datatype, i.Name))
		return result

	def get_eventtypes(self) -> List[EventType]:
		id = 1
		result = []
		while (True):
			try:
				tmp = self.api.GetEventType(id)
			except Prediktor.APIS.Hive.HiveException as e:
				if (e.HResult != -536870906):
					print(f"Unexpected error: {e}")
				break
			result.append(EventServer.EventType(self, tmp.Id, tmp.Name, tmp.ParentId, tmp.Flags))
			id += 1
		return result

	def get_eventfields(self) -> List[EventField]:
		id = 1
		result = []
		while (True):
			try:
				tmp = self.api.GetEventField(id)
			except Prediktor.APIS.Hive.HiveException as e:
				if (e.HResult != -536870906):
					print(f"Unexpected error: {e}")
				break
			result.append(EventServer.EventField(self, tmp.Id, tmp.Name, tmp.EventTypeId, tmp.Datatype, tmp.Flags))
			id += 1
		return result

	def browse(self, pattern, flags, max_count = 1000, parent=0) -> List[EventSource]:
		tmp = self.api.FindSources(parent, flags, pattern, max_count, None, None)
		return [EventServer.EventSource(self, s.Id, s.Path) for s in tmp]

	def query(self, starttime, endtime, eventsource, eventtype, filter, maxrows = 1000):
		if isinstance(eventsource, Prediktor.APIS.Hive.EventSourcePath):
			eventsource = eventsource.Id
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

class EndpointList:
	"""Class used to access the EventServer (and Chronical) in an APIS HIVE instance"""
	def __init__(self, hive, api):
		self.hive = hive
		self.api = api

	def __len__(self):
		return len(self.all)

	def __getitem__(self, key):
		return all[key]

	@property
	def all(self):
		return [Endpoint(self, self.api.GetEndpointData(e.Id)) for e in self.api.GetApisEndpointInfos()]

	def add(self):
		tmp = self.api.AddEndpoint()
		return Endpoint(self, self.api.GetEndpointData(tmp.Id))

class Endpoint:
	def __init__(self, eplist, api):
		self.eplist = eplist
		self.api = api
		self.props = {p.Name:p for p in api.Properties}
		self.writer = Prediktor.APIS.Hive.EndpointWriter(self.api.Id)

	def __getitem__(self, key):
		return self.props[key]

	def __setitem__(self, key, value):
		prop = self[key]
		prop.Value = value
		self.writer.AddPropVal(prop.Id, prop.Value)

	def __len__(self):
		return len(self.props)

	def __iter__(self):
		return self.props()

	@property
	def properties(self):
		return self.props

	def get_property(self, key):
		return self.props[key]

	def save(self):
		self.eplist.api.WriteEndpointData(self.writer)

class EventBroker:
	def __init__(self, hive):
		self.hive = hive
		self.api = hive.api.GetEventBroker()

	def connect(self, evt, cmds):
		cmds = [c.Id for c in cmds]
		cmds = System.Array[Prediktor.APIS.Hive.ICommandId](cmds)
		tmp = Prediktor.APIS.HiveWrapper.EventConnection(evt.Id, cmds)
		self.api.AddCommands([tmp])
