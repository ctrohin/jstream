from types import MappingProxyType
from typing import (
    Any,
    Callable,
    TypeVar,
    Iterable,
    Union,
    Protocol,
    runtime_checkable,
    get_type_hints,
    get_origin,
    get_args,
)
import inspect

# TypeVar to represent the class being decorated.
_T = TypeVar("_T")


# Define a Protocol for objects that have to_dict and from_dict methods.
# Define a Protocol for objects that have a to_dict method.
# This helps in type checking the duck-typed call to value.to_dict().
@runtime_checkable
class SerializableObject(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Any:  # Return Any, actual type is _T
        ...


def _process_value(value: Any) -> Any:
    """Helper function to recursively process values for serialization."""
    if isinstance(value, SerializableObject) and callable(
        getattr(value, "to_dict", None)
    ):
        # If the object conforms to SerializableObject and has a callable to_dict
        return value.to_dict()
    elif isinstance(value, list):
        return [_process_value(item) for item in value]
    elif isinstance(value, tuple):
        # Preserve tuple type by creating a new tuple with processed items
        return tuple(_process_value(item) for item in value)
    elif isinstance(value, dict):
        return {k: _process_value(v) for k, v in value.items()}
    # Basic types (int, str, float, bool, None) and other unhandled types are returned as-is.
    return value


def _deserialize_value(target_type: Any, data_value: Any) -> Any:
    """
    Helper function to recursively deserialize a data value to a target type.
    """
    if target_type is Any:  # No specific type hint, return as is
        return data_value

    origin = get_origin(target_type)
    args = get_args(target_type)

    if origin is Union:  # Handles Optional[X] (Union[X, NoneType]) and other Unions
        if data_value is None:
            # If None is a valid type in the Union (e.g., Optional), return None.
            if any(arg is type(None) for arg in args):
                return None
            # If None is not allowed by the Union but data is None, this is a potential mismatch.
            # For now, we let it fall through; specific error handling could be added.

        # Try to deserialize with non-None types in the Union.
        for arg_type in args:
            if arg_type is type(None):
                continue
            try:
                # Attempt to deserialize with this type from the Union.
                return _deserialize_value(arg_type, data_value)
            except (TypeError, ValueError, AttributeError, KeyError):
                # If deserialization with this arg_type fails, try the next one.
                continue
        # If no type in Union matches or successfully deserializes, return raw data_value.
        # This might be the correct behavior if data_value is already of a compatible simple type.
        return data_value

    if origin in (list, tuple) and args:  # Handles list[X], tuple[X, Y, ...]
        item_type = args[0]  # Assuming list[X] or tuple[X, ...]
        if isinstance(data_value, list):  # Expecting a list from JSON-like data
            processed_list = [
                _deserialize_value(item_type, item) for item in data_value
            ]
            return processed_list if origin is list else origin(processed_list)
        else:
            # Data doesn't match expected list type, return as is or raise error.
            return data_value  # Or raise TypeError(f"Expected list for {target_type}, got {type(data_value)}")

    if origin is dict and args and len(args) == 2:  # Handles dict[KeyType, ValueType]
        # key_type = args[0] # Assuming key_type is simple (e.g. str) for JSON-like dicts
        value_type = args[1]
        if isinstance(data_value, dict):
            return {k: _deserialize_value(value_type, v) for k, v in data_value.items()}
        else:
            # Data doesn't match expected dict type
            return data_value  # Or raise TypeError

    # Check for a class that has from_dict (could be target_type itself if not a generic)
    # This handles direct SerializableObject types.
    # Note: `origin` is None for non-generic types like `MyClass`.
    actual_type_to_check = origin if origin else target_type
    if (
        hasattr(actual_type_to_check, "from_dict")
        and callable(getattr(actual_type_to_check, "from_dict"))
        and isinstance(data_value, dict)
    ):
        return actual_type_to_check.from_dict(data_value)

    # If it's a basic type, or no special handling matched, return data_value.
    # This assumes data_value is already of the correct basic type (e.g. int, str).
    return data_value


def serializable(ignore_unknown_fields: bool = True) -> Callable[[type[_T]], type[_T]]:
    """
    A class decorator that adds a to_dict() method to the decorated class.
    This method serializes an instance into a dictionary, including attributes
    from both __dict__ (standard instance attributes) and __slots__ (if used).

    Serialization is recursive:
    - Objects that have a 'to_dict' method (e.g., other @serializable instances)
      are serialized by calling their to_dict() method.
    - Lists and tuples are iterated, and their items are processed recursively.
    - Dictionaries are iterated, and their values are processed recursively.

    By convention, attributes are excluded from serialization if their names:
    - Start with a single underscore (e.g., _protected_attribute).
    - Start with double underscores (e.g., __private_attribute, which undergoes
      name mangling to _ClassName__private_attribute and is thus also excluded).
    This helps in respecting encapsulation and not serializing internal state.
    """

    def decorator(cls: type[_T]) -> type[_T]:
        def to_dict(self: _T) -> dict[str, Any]:
            serialized_data: dict[str, Any] = {}

            # This map will store all potential attributes to serialize,
            # gathered from __dict__ and __slots__.
            attributes_map: dict[str, Any] = {}

            # 1. Gather attributes from __dict__ if it exists
            if hasattr(self, "__dict__"):
                attributes_map.update(self.__dict__)

            # 2. Gather attributes from __slots__ if the class defines them
            # getattr() is used to fetch slot values. This correctly handles
            # attributes defined only in __slots__ and also cases where __slots__
            # might include '__dict__' (allowing both slotted and dynamic attributes).
            if hasattr(cls, "__slots__"):
                # cls.__slots__ can be a string or an iterable of strings
                defined_slot_names: Union[str, Iterable[str]] = cls.__slots__  # type: ignore[attr-defined]
                actual_slot_names: Iterable[str]

                if isinstance(defined_slot_names, str):
                    actual_slot_names = [defined_slot_names]
                else:
                    actual_slot_names = defined_slot_names

                for slot_name in actual_slot_names:
                    # Special slots like __dict__ and __weakref__ are part of Python's object model
                    # and not typically considered data attributes for serialization.
                    # __dict__ contents are already handled above. __weakref__ is for weak references.
                    if slot_name in ("__dict__", "__weakref__"):
                        continue
                    try:
                        # Fetch the value of the slot from the instance
                        attributes_map[slot_name] = getattr(self, slot_name)
                    except AttributeError:
                        # This can happen if a slot is defined but not yet assigned a value
                        # on this particular instance, or if it's a complex descriptor.
                        # In such cases, we'll skip it for serialization.
                        continue  # Use continue to be explicit about skipping

            # 3. Gather attributes defined purely by __annotations__ that exist on the instance
            # This handles cases where an attribute might be defined with a type hint
            # but not explicitly in __init__ or __slots__, but is set later on the instance.
            if hasattr(cls, "__annotations__"):
                for key in cls.__annotations__:
                    # If the attribute is already in __dict__ or __slots__, we've already got it.
                    # We only need to check annotations for attributes *not* yet in the map.
                    if key not in attributes_map:
                        # Try to get the value from the instance.
                        # If it exists, add it to the map. If not, skip it.
                        try:
                            attributes_map[key] = getattr(self, key)
                        except AttributeError:
                            # Attribute defined in annotations but not set on this instance.
                            # Skip it for serialization.
                            continue

            for key, value in attributes_map.items():
                if not key.startswith(
                    "_"
                ):  # Exclude "private" or "protected" attributes
                    serialized_data[key] = _process_value(value)

            return serialized_data

        def from_dict(cls_target: type[_T], data: dict[str, Any]) -> _T:
            """
            Creates an instance of the class from a dictionary.
            Recursively deserializes nested objects based on type hints.
            """
            try:
                all_type_hints = get_type_hints(cls_target)
            except Exception:  # get_type_hints can fail in some edge cases
                all_type_hints = {}

            init_kwargs: dict[str, Any] = {}
            extra_data: dict[str, Any] = {}  # For data not used in __init__

            init_params: Union[
                MappingProxyType[str, inspect.Parameter], dict[str, inspect.Parameter]
            ] = {}
            # Inspect __init__ signature to find parameters
            try:
                init_sig = inspect.signature(cls_target.__init__)
                init_params = init_sig.parameters
            except (
                ValueError,
                TypeError,
            ):  # Some built-ins or C extensions might not be inspectable
                pass

            # Prepare arguments for __init__ by deserializing them
            for key, value in data.items():
                if key in init_params and init_params[key].name != "self":
                    param = init_params[key]
                    # Determine the type hint for the __init__ parameter
                    param_type_hint = param.annotation
                    if param_type_hint is inspect.Parameter.empty:
                        # If __init__ param has no type hint, try class-level hint
                        param_type_hint = all_type_hints.get(key, Any)

                    init_kwargs[key] = _deserialize_value(param_type_hint, value)
                else:
                    extra_data[key] = value

            # Instantiate the object using prepared __init__ arguments
            # This assumes __init__ can handle the provided kwargs.
            # If required __init__ args are missing from data and have no defaults,
            # this will (correctly) raise a TypeError.
            instance = cls_target(**init_kwargs)

            # Set any remaining attributes from `extra_data` using setattr
            for key, value in extra_data.items():
                is_slot = False
                if hasattr(cls_target, "__slots__"):
                    defined_slots = cls_target.__slots__  # type: ignore[attr-defined]
                    if isinstance(defined_slots, str):
                        defined_slots = [defined_slots]
                    if key in defined_slots:
                        is_slot = True

                # Set attribute if it's a known slot or a regular attribute
                if is_slot or hasattr(instance, key):
                    attr_type_hint = all_type_hints.get(key, Any)
                    deserialized_value = _deserialize_value(attr_type_hint, value)
                    try:
                        setattr(instance, key, deserialized_value)
                    except (
                        AttributeError
                    ):  # e.g., property without setter, or __slots__ issue
                        # Optionally log: f"Warning: Could not set attribute '{key}' on '{cls_target.__name__}'"
                        pass
                elif not ignore_unknown_fields:
                    # If the attribute is not a serializable attribute, try to set it anyway
                    try:
                        setattr(instance, key, value)
                    except AttributeError:
                        pass
            return instance

        def __eq__(self: _T, other: Any) -> bool:
            """
            Compares this instance with another object for equality.
            Two instances are considered equal if they are of the same type
            and their `to_dict()` representations are identical.
            """
            if not isinstance(other, self.__class__):
                return NotImplemented  # Or False, NotImplemented is more idiomatic for __eq__

            # Both self and other should have to_dict if decorated by serializable
            # and self.__class__ is the same as other.__class__
            self_dict = self.to_dict()  # type: ignore[attr-defined]
            other_dict = other.to_dict()  # type: ignore[attr-defined]
            return self_dict == other_dict  # type: ignore[no-any-return]

        def __str__(self: _T) -> str:
            """
            Returns a string representation of the instance.
            This is useful for debugging and logging.
            """
            return f"{self.__class__.__name__}({self.to_dict()})"

        # Add the to_dict method to the class.
        setattr(cls, "to_dict", to_dict)
        setattr(cls, "from_dict", classmethod(from_dict))
        setattr(cls, "__eq__", __eq__)
        setattr(cls, "__str__", __str__)
        setattr(cls, "__repr__", __str__)
        return cls

    return decorator


def deserialize(class_type: type[_T], data: dict[str, Any]) -> _T:
    """
    Deserialize a dictionary into an instance of the specified class type.
    This function is a convenience wrapper around the from_dict method of the class.
    """
    if not hasattr(class_type, "from_dict"):
        raise TypeError(f"{class_type.__name__} does not have a from_dict method.")
    return class_type.from_dict(data)  # type: ignore


def serialize(obj: Any) -> dict[str, Any]:
    """
    Serialize an object into a dictionary.
    This function is a convenience wrapper around the to_dict method of the object.
    """
    if not hasattr(obj, "to_dict"):
        raise TypeError(f"{obj.__class__.__name__} does not have a to_dict method.")
    return obj.to_dict()  # type: ignore
