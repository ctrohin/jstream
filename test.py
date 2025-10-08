import json
import time
from jstreams import take_while, take_until
from itertools import groupby, takewhile


max_val = 1000 * 1000 * 100
while_val = max_val - 10
it1 = range(max_val)
it2 = range(max_val)

start = time.time()
for e in takewhile(lambda x: x < while_val, it1):
    pass
end = time.time()
print(end - start)

start = time.time()
for e in take_until(it2, lambda x: x >= while_val):
    pass

end = time.time()
print(end - start)
