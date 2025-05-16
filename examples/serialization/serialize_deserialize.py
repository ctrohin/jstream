from dataclasses import dataclass
import sys

sys.path.append(".")

from jstreams import (
    json_serializable,
    json_serialize,
    json_deserialize,
    json_standard_serializable,
    json_serialize_return,
)


# Serialization can be applied to any object, including dataclasses and plain objects.
# The decorator `@json_serializable` is used to mark a class as serializable.
@json_serializable()
@dataclass
class Data:
    int_val: int
    str_val: str


@json_serializable()
class PlainObject:
    def __init__(self, val: int):
        self.val = val


# We create an instance of the Data class and serialize it to JSON.
data_obj = Data(10, "test")
serialized = json_serialize(data_obj)

print(serialized)

# The serialized JSON string can be deserialized back to the original object using the `json_deserialize` function.
deserialized_obj = json_deserialize(Data, serialized)
assert data_obj == deserialized_obj
print("Initial object", data_obj)
print("Deserialized object", deserialized_obj)


# The `json_serializable` decorator can also be applied to nested dataclasses.
# In this example, we create a ComplexData class that contains a Data object and a PlainObject.
# The `json_serializable` decorator is applied to the ComplexData class as well.
# This allows us to serialize and deserialize the ComplexData object, which contains nested objects.
@json_serializable()
@dataclass
class ComplexData:
    data: Data
    additional_int_val: int
    plain: PlainObject


# We create an instance of the ComplexData class and serialize it to JSON.
complex_data = ComplexData(Data(1, "test"), 20, PlainObject(30))
complex_serialized = json_serialize(complex_data)
print(complex_serialized)
deserialized_complex_data = json_deserialize(ComplexData, complex_serialized)
# We can assert that the original complex data object and the deserialized object are equal.
assert complex_data == deserialized_complex_data
print("Initial complex data", complex_data)
print("Deserialized complex data", deserialized_complex_data)


@json_standard_serializable()
class StandardData:
    def __init__(self, int_val: int, str_val: str):
        self.int_val = int_val
        self.str_val = str_val


# APIs usually return data in a standard format, such as JSON. The key names are usually camelCase.
# Since we want to both respect the PEP8 naming convention and the API standard, we can use the `json_standard_serializable` decorator.
# This decorator will, by default, convert the attribute names to camelCase when serializing and back to snake_case when deserializing.
api_data = {
    "intVal": 10,
    "strVal": "test",
}
standard_data = json_deserialize(StandardData, api_data)
print("Deserialized standard data", standard_data)
assert standard_data.int_val == 10
assert standard_data.str_val == "test"


# We can also use the json_serialize_return decorator to serialize the return value of a function.
@json_serialize_return()
def get_data() -> StandardData:
    return StandardData(10, "test")


# This is useful when we want to return a standard data object from an API endpoint or a function.
# The return value will be automatically serialized to JSON format.
val = get_data()
print("Serialized return value", val)
assert val == {"intVal": 10, "strVal": "test"}
