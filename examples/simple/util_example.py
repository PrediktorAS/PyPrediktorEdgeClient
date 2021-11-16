# %%
from pyprediktoredgeclient import util, hiveservices
# %%
import datetime
now = datetime.datetime(2021, 10, 19, 6, 43,56)
dotnetDateTime = util.fm_pydatetime(now)
py_datetime = util.to_pydatetime(dotnetDateTime)
assert now==py_datetime

# %%
q = util.Quality(192)
assert str(q)=='good'


# %%
for i in hiveservices.list_instances():
    print(i, i.running, i.name, i.CLSID, i.prog_id)
# %%
test = hiveservices.get_instance('test')
# %%
test.running=False