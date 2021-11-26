# ToDo Feature list

- [-] ToDo list (this)
- [x] [hiveservices](##hive-services)
- [x] Proper handling of module properties, similar to item attributes
- [x] Improved VQT/ItemVQT/TimeSeries
- [-] Jupyter docbook w/tests
- [x] Set/get external_items
- [x] Add attributes to items
- [x] Get global-attributes from an Hive
- [x] Flexible loading of Apis-dlls
- [x] honeystore
- [ ] timeseries
- [ ] More demo cases
- [ ] Config load and restore
- [ ] itemquery
- [ ] chronical
- [ ] common base classes

x Done

-Started


## Hive services

This module will contain functions to control the available hive-services. In addition add and remove of hive-services are possible

```python
>>> from pyprediktoredgeclient import hiveservices, hive
>>> hiveservices.list_services()
<Prediktor.ApisService ... ... >
...
>>> test_hive_instance = hiveservices.get_service("test")
>>> test_hive_instance.start()
>>> from pyprediktoredgeclient import hive
>>> test = hive.Hive(test_hive_instance)
```

## Improved VQT/ItemVQT/TimeSeries

The data-classes for VQT/ItemVQT/TimeSeries should be based on typing.NamedTuple

## Jupyter docbook w/tests

**HOLD**

## Set/get external_items

Add the property `.external_items` to the Item class. Typical usage:

```python
>>> my_variable = worker_module['my_var']
>>> my_variable.external_items = ['opc1.inputvar', 'opc1.setpoint']
>>> my_variable.Expression = 'ex1+ex2'

```

## Add attributes to items

Introduce the possibility to add attributes to items from the global attribute list

```python
>>> my_variable = worker_module['my_var']
>>> my_variable.add_attribute('Logger', True)
>>> my_variable.add_attribute(Description4, "My description")
>>> assert my_variable.Description4 == "My description"
```


## Flexible loading of Apis-dlls

Right now the Apis Edge related .dll's are hosted in a subfolder under the installation folder. A better option would be to 
use the Win32 registry to determine the location of possible installed Apis .dll's (i.e. in \program files\apis\bin64 or some other location). If found, these 
modules can be loaded instead of the supplied modules. This feature will only be available on Windows

## A honeystore interface

This interface can be modelled using the same principles as the `hive` classes.

```python
>>> from pyprediktoredgeclient import honeystore
>>> hs = honeystore.HoneyStore('localhost')
>>> for db in hs.list_databases():
...    print(db.name)

logger
test
signals
>>> logger = hs['logger']
>>> logger.runmode
'online-no-cache'
>>> logger.runmode = 'online'
>>> logger.add_item('myitem', #how to datatype?#...)
```


## Access methods for timeseries.

This is a separate module that allows access to time-series. The read access can either be 
through the hive interface or through the OPCHDA interface

```python
>>> from pyprediktoredgeclient import honeystore, timeseries
>>> hs = honeystore.HoneyStore('localhost')
>>> logger = hs['logger']
>>> start = datetime.now() - ...
>>> ts = timeseries.read(logger, ['myitem', 'otheritem'], from=start, agg='interpolated')
>>> ts
<Apis.Timeseries: 'myitem', len=442>
<Apis.Timeseries: 'otheritem', len=442>
```

## More demo cases

Some interesting demo-cases could be:
* Pandas integration
* Bokeh integration
* Simple Web-api

## Common base classes


