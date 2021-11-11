# %% Do the imports and connect to the 'test' hive
import datetime
from pyprediktoredgeclient import hive
test_hive = hive.Hive('Prediktor.ApisLoader.test')
assert test_hive.name=='test'

# %% Check if we have "ApisWorker" defined as a module-type
mod_class_names = [mod_type.class_name for mod_type in test_hive.module_types]
assert 'ApisWorker' in mod_class_names

worker_type = test_hive.get_module_type('ApisWorker')

# %% Delete the "testworker"-modules if they exists in the Hive
for mod in test_hive.modules:
    if "testworker" in mod.name:
        del test_hive[mod.name]

# %% Add a new "testworker"-module to the Hive
test_module= test_hive.add_module(worker_type, 'testworker')
test_module2 = test_hive.add_module('ApisWorker', 'testworker2')

# %% Make a list of time-type names. Check that 'Signal' and 'Variable' are among them
item_type_names = [item_type.Name for item_type in test_module.item_types]

assert 'Signal' in item_type_names
assert 'Variable' in item_type_names

# %% Add 100 items of the type 'Signal' to the worker module we have created. Set some properties
for i in range(100):
    new_item = test_module.add_item("Signal", f"TestItem{i}")
    new_item.Amplitude=1
    new_item.Bias = 1


# %% Grab an item using numeric index and name
item1=test_module[0]
item1_s = test_module[item1.name]
item_i = test_module[item1_s]

#check that all items are the same by comparing the item_id
assert item1.item_id == item1_s.item_id == item_i.item_id

#check that the items are the same by comparing the handles of the underlying IItem-object
assert item1.api.Handle == item1_s.api.Handle == item_i.api.Handle

#check that the amplitude and bias actually are 1.0
assert item1.Amplitude == 1.0 and item1.Bias == 1.0

item1.Amplitude = 2.0

# %%% Grab an attribute from the item and change the value
item1_amplitude_attr = item1.get_attr('Amplitude')

assert item1_amplitude_attr.value == 2.0

# if you set here it will also change when accessed through the item
item1_amplitude_attr.value = 1.5
assert item1.Amplitude == 1.5

# %% Check that read-ony attributes are indeed read only.
example_item = test_module[50]
try:
    example_item.Value = 2.3
    print("Fail, should not be allowed")
except AttributeError:
    print("OK, should not be allowed to set the value on a signalø")

# %% Check that enumerated values are handled correctly
example_item.Waveform = 'Sine'
assert example_item.Waveform == 'Sine'

example_item.Waveform = 'Triangle'
assert example_item.Waveform == 'Triangle'

# %%
some_items = [f"testworker.testitem{i}" for i in range(10, 40, 2)]
for vqt in test_hive.get_values(some_items):
    print(f"{vqt.item_id}: {vqt.value} ({vqt.quality}) @ {vqt.time}")

# %%
