from dataclasses import dataclass
from jstreams import stream


@dataclass
class Point:
    name: str
    x: float
    y: float


# Suppose we have a list of Point objects
data: list[Point] = [
    Point("test", 1.0, 2.0),
    Point("test2", 5.0, 6.0),
    Point("test3", 3.0, 4.0),
    Point("test4", 7.0, 8.0),
    Point("test5", 11.0, 12.0),
    Point("test6", 9.0, 10.0),
    Point("test7", 13.0, 14.0),
]

# We can stream the list of data in many ways


# Suppose we want to extract a list of the x values from this list, we can do it in two different ways
# 1. The classic way
x_list_1 = [p.x for p in data]

# 2. Using jstreams
x_list_stream = stream(data).map(lambda p: p.x).to_list()

assert x_list_1 == x_list_stream
print("All the items", x_list_stream)

# At a first glance, the list comprehension seems way simpler, and if this is all you need, then
# a list comprehension is the way to go.

# Now, suppose we actually want to extract the x values from the list, for any y value less than 10. Again we can do this:
# 1. The classic way
x_list_2 = [p.x for p in data if p.y < 10]

# 2. Using jstreams
x_list_stream = stream(data).filter(lambda p: p.y < 10).map(lambda p: p.x).to_list()

# Again, here it seems like the list comprehension is simpler to use, but the code is more readable using jstreams

assert x_list_2 == x_list_stream
print("Less than y 10 items", x_list_stream)


# Let's say that we want now to use a conditional stop for the stream. Say, we want to extract all the Point objects
# from the list until we find an element that has x higher than 5. Let's try this:
# 1. The classic way
def extract(data_list: list[Point], value: float) -> list[Point]:
    data = []
    for p in data_list:
        if p.x > value:
            break
        data.append(p)
    return data


x_list_3 = extract(data, 5)


# 2. Using jstreams
x_list_float = stream(data).take_until(lambda p: p.x > 5).to_list()

# As we can see here, when things get complicated, the classic list comprehension can no longer be used.
# This is one of the good examples where 8 lines of code can be replaced with a single one.

print(x_list_3)
print(x_list_float)
assert x_list_3 == x_list_float
print("Less than x 5 items", x_list_float)
