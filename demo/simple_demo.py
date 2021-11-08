# %%
import datetime
from pyprediktoredgeclient import hive
test_hive = hive.Hive('Prediktor.ApisLoader.test')
test_hive

# %%
mod_names = [mod.name for mod in test_hive.modules]
for mod_name in mod_names:
    print(mod_name)
# %%
if "testworker" in mod_names:
    del test_hive['testworker']
# %%

test_module= test_hive.add_module('ApisWorker', 'testworker')
# %%
[item_type.Name for item_type in test_module.item_types]
# %%
for i in range(100):
    new_item = test_module.add_item("Signal", f"TestItem{i}")
    new_item.Amplitude=1
    new_item.Bias = 1
# %%
print(test_module.items)
# %%%
example_item = test_module["TestItem10"]
example_item.Value
# %%
try:
    example_item.Value = 2.3
    print("Fail, should not be allowed")
except AttributeError:
    print("OK, should not be allowed to set the value on a signalø")

example_item.Waveform
# %%
some_items = [f"testworker.testitem{i}" for i in range(10, 40, 2)]
for vqt in test_hive.get_values(some_items):
    print(f"{vqt.item_id}: {vqt.value} ({vqt.quality}) @ {vqt.time.ToString()}")

# %%
