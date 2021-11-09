# ToDo Feature list

0. ToDo list (this)
1. hiveservices
2. Proper handling of module properties, similar to item attributes
2. Improved VQT/ItemVQT/TimeSeries
3. Jupyter docbook w/tests
4. Flexible loading of Apis-dlls
4. honeystore
5. timeseries
6. More demo cases
7. Config load and restore
6. itemquery

## Hive services (hiveservices)

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
