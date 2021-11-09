# %%
from pyprediktoredgeclient import util
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
