# %% Do the imports
from pyprediktoredgeclient import hive, hiveservices
import time

# %% List all hive instances UUIDs on the machine
uuids = hiveservices.instance_identifiers()

# %% List all instances as HiveInstace objects
instance_list = hiveservices.list_instances()

#check that the UUID list is the same length at the instance list
assert len(uuids) == len(instance_list)

#check that all instances in instance list has a corresponding UUID
for instance in instance_list:
    assert instance.CLSID in uuids

# %% Grag the instance 'test' and  turn it on and then off (or visa-versa)
pytestinstance = hiveservices.get_instance('pytestinstance')

runstate = test.running
test.running = not runstate
time.sleep(1.5)
assert test.running != runstate
test.running = runstate


# %%
