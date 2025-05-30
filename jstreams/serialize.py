import sys
from datetime import date, datetime
from enum import Enum
import re
from typing import (
    Any,
    Callable,
    Optional,
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
from uuid import UUID

# TypeVar to represent the class being decorated.
_T = TypeVar("_T")
# Covariant TypeVar for SerializableObject protocol
_T_co = TypeVar("_T_co", covariant=True)

# Pre-compiled regex for _camel_to_snake for performance
_CAMEL_TO_SNAKE_PAT1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_TO_SNAKE_PAT2 = re.compile(r"__([A-Z])")
_CAMEL_TO_SNAKE_PAT3 = re.compile(r"([a-z0-9])([A-Z])")

# Caches for _deserialize_value to speed up repeated type checks
_ENUM_TYPE_CACHE: dict[type, bool] = {}
_HAS_CALLABLE_FROM_DICT_CACHE: dict[type, bool] = {}


def _snake_to_camel(snake_str: str) -> str:
    """Converts a snake_case string to camelCase."""
    if not snake_str:
        return snake_str

    # Optimized handling of leading underscores
    first_char_index = 0
    s_len = len(snake_str)
    while first_char_index < s_len and snake_str[first_char_index] == "_":
        first_char_index += 1

    leading_underscores = snake_str[:first_char_index]
    name_part = snake_str[first_char_index:]

    if not name_part:  # True if original string was all underscores or empty
        return snake_str
    # If snake_str was empty, it's returned at the top.
    # If it was all underscores (e.g., "___"), leading_underscores="___", name_part="".
    # It will correctly return "___".

    components = name_part.split("_")
    camel_case_part = components[0] + "".join(x.title() for x in components[1:])
    return leading_underscores + camel_case_part


def _camel_to_snake(camel_str: str) -> str:
    """Converts a camelCase string to snake_case."""
    if not camel_str:
        return camel_str
    name = _CAMEL_TO_SNAKE_PAT1.sub(r"\1_\2", camel_str)
    name = _CAMEL_TO_SNAKE_PAT2.sub(r"_\1", name)
    name = _CAMEL_TO_SNAKE_PAT3.sub(r"\1_\2", name)
    return name.lower()


# Define a Protocol for objects that have to_dict and from_dict methods.
# Define a Protocol for objects that have a to_dict method.
# This helps in type checking the duck-typed call to value.to_dict().
@runtime_checkable
class SerializableObject(Protocol[_T_co]):
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls: type[_T_co], data: dict[str, Any]) -> _T_co: ...


def _process_value(value: Any) -> Any:
    """Helper function to recursively process values for serialization."""
    # If the object conforms to SerializableObject, isinstance check is sufficient due to @runtime_checkable

    if isinstance(value, SerializableObject):
        # If the object conforms to SerializableObject and has a callable to_dict
        return value.to_dict()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value  # Serialize Enums to their value
    if isinstance(value, list):
        return [_process_value(item) for item in value]
    if isinstance(value, tuple):
        # Preserve tuple type by creating a new tuple with processed items
        return tuple(_process_value(item) for item in value)
    if isinstance(value, dict):
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
    actual_type_to_check = origin or target_type

    # 1. Handle specific known types first
    if actual_type_to_check is datetime and isinstance(data_value, str):
        try:
            return datetime.fromisoformat(data_value)
        except ValueError:
            pass  # Fall through if not a valid ISO format string
    if actual_type_to_check is date and isinstance(data_value, str):
        try:
            return date.fromisoformat(data_value)
        except ValueError:
            pass
    if actual_type_to_check is UUID and isinstance(data_value, str):
        try:
            return UUID(data_value)
        except ValueError:
            pass
    if inspect.isclass(actual_type_to_check) and issubclass(actual_type_to_check, Enum):
        # Optimized Enum check using cache
        is_enum_class = _ENUM_TYPE_CACHE.get(actual_type_to_check)
        if is_enum_class is None:
            is_enum_class = inspect.isclass(actual_type_to_check) and issubclass(
                actual_type_to_check, Enum
            )
            _ENUM_TYPE_CACHE[actual_type_to_check] = is_enum_class

        if is_enum_class:
            try:
                # Attempt to create enum member from value
                return actual_type_to_check(data_value)
            except ValueError:
                # If data_value is not a valid value for the enum,
                # it might be the enum member name (less common for JSON).
                pass
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

        # If no type in Union matches or successfully deserializes,
        # and data_value was not None (or None was not allowed), return raw data_value.
        # This might be the correct behavior if data_value is already of a compatible simple type
        # that wasn't explicitly in the Union's args but is assignable.
        if data_value is not None or not any(arg is type(None) for arg in args):
            return data_value
        return None  # Should have been caught by 'if data_value is None' earlier if None was allowed

    if origin in (list, tuple) and args:  # Handles list[X], tuple[X, Y, ...]
        item_type = args[0]  # Assuming list[X] or tuple[X, ...]
        if isinstance(data_value, list):  # Expecting a list from JSON-like data
            processed_list = [
                _deserialize_value(item_type, item) for item in data_value
            ]
            return processed_list if origin is list else origin(processed_list)
        # Data doesn't match expected list type, return as is or raise error.
        return data_value  # Or raise TypeError(f"Expected list for {target_type}, got {type(data_value)}")

    if origin is dict and args and len(args) == 2:  # Handles dict[KeyType, ValueType]
        # key_type = args[0] # Assuming key_type is simple (e.g. str) for JSON-like dicts
        value_type = args[1]
        if isinstance(data_value, dict):
            return {k: _deserialize_value(value_type, v) for k, v in data_value.items()}
        # Data doesn't match expected dict type
        return data_value  # Or raise TypeError

    # Check for a class that has from_dict (could be target_type itself if not a generic)
    # This handles direct SerializableObject types.
    # Optimized check for from_dict capability using cache
    has_callable_from_dict = _HAS_CALLABLE_FROM_DICT_CACHE.get(actual_type_to_check)
    if has_callable_from_dict is None:
        if inspect.isclass(
            actual_type_to_check
        ):  # hasattr/getattr are safer on classes
            from_dict_method = getattr(actual_type_to_check, "from_dict", None)
            has_callable_from_dict = callable(from_dict_method)
        else:
            has_callable_from_dict = (
                False  # Not a class, so can't have classmethod from_dict
            )
        _HAS_CALLABLE_FROM_DICT_CACHE[actual_type_to_check] = has_callable_from_dict

    if has_callable_from_dict and isinstance(data_value, dict):
        # actual_type_to_check is known to have a callable from_dict
        return actual_type_to_check.from_dict(data_value)

    # If data_value is already an instance of the target type (after considering origin)
    if actual_type_to_check is not Any and isinstance(data_value, actual_type_to_check):
        return data_value

    # Attempt basic type coercion if target_type is a basic type and data_value is not already that type
    if actual_type_to_check in (int, float, str, bool) and not isinstance(
        data_value, actual_type_to_check
    ):
        try:
            return actual_type_to_check(data_value)
        except (ValueError, TypeError):
            # Coercion failed, fall through to return original data_value
            pass
    return data_value


def json_standard_serializable(
    ignore_unknown_fields: bool = True,
    aliases: Optional[dict[str, str]] = None,
    omit_none: bool = False,
    custom_serializers: Optional[dict[str, Callable[[Any], Any]]] = None,
    custom_deserializers: Optional[dict[str, Callable[[Any], Any]]] = None,
    post_deserialize_hook_name: Optional[str] = "__post_deserialize__",
) -> Callable[[type[_T]], type[_T]]:
    """
    Alias for json_serializable with translate_snake_to_camel set to True.
    This decorator is used to create a JSON serializable class.

    Args:
        ignore_unknown_fields (bool, optional): _description_. Defaults to True.
        aliases (Optional[dict[str, str]], optional): _description_. Defaults to None.
        omit_none (bool, optional): _description_. Defaults to False.
        custom_serializers (Optional[dict[str, Callable[[Any], Any]]], optional): _description_. Defaults to None.
        custom_deserializers (Optional[dict[str, Callable[[Any], Any]]], optional): _description_. Defaults to None.
        post_deserialize_hook_name (Optional[str], optional): _description_. Defaults to "__post_deserialize__".

    Returns:
        Callable[[type[_T]], type[_T]]: _description_
    """
    return json_serializable(
        ignore_unknown_fields=ignore_unknown_fields,
        aliases=aliases,
        omit_none=omit_none,
        custom_serializers=custom_serializers,
        custom_deserializers=custom_deserializers,
        post_deserialize_hook_name=post_deserialize_hook_name,
        translate_snake_to_camel=True,
    )


def json_serializable(
    ignore_unknown_fields: bool = True,
    aliases: Optional[dict[str, str]] = None,
    omit_none: bool = False,
    custom_serializers: Optional[dict[str, Callable[[Any], Any]]] = None,
    custom_deserializers: Optional[dict[str, Callable[[Any], Any]]] = None,
    post_deserialize_hook_name: Optional[str] = "__post_deserialize__",
    translate_snake_to_camel: bool = False,
) -> Callable[[type[_T]], type[_T]]:
    """
    A class decorator that adds a to_dict() method to the decorated class.
    This method serializes an instance into a dictionary, including attributes
    from both __dict__ (standard instance attributes) and __slots__ (if used).
    The decorator also provides a from_dict() class method for deserialization.
    This method takes a dictionary and populates the instance's attributes
    based on the provided data. It uses type hints to determine the expected
    types of the attributes and attempts to deserialize the data accordingly.

    Serialization is recursive:
    - Objects that have a 'to_dict' method (e.g., other @serializable instances)
      are serialized by calling their to_dict() method.
    - Lists and tuples are iterated, and their items are processed recursively.
    - Dictionaries are iterated, and their values are processed recursively.
    - Supports field aliasing for serialization and deserialization.
    - Can omit fields with None values during serialization.
    - Supports custom serializer functions for specific fields.
    - Supports custom deserializer functions for specific fields.
    - Can call a post-deserialization hook method on the instance.
    - Enhanced to handle common types like datetime, date, Enum, UUID.

    By convention, attributes are excluded from serialization if their names:
    - Start with a single underscore (e.g., _protected_attribute).
    - Start with double underscores (e.g., __private_attribute, which undergoes
      name mangling to _ClassName__private_attribute and is thus also excluded).
    This helps in respecting encapsulation and not serializing internal state.
    It also supports:
    - Aliasing of attributes during deserialization.
    - Handling of unknown fields (fields not defined in the class).
    - Custom deserializer functions for specific fields.
    - Post-deserialization hook method that can be called after deserialization.
    The decorator can be applied to any class, including those that use
    dataclasses, namedtuples, or other custom structures.

    Args:
        ignore_unknown_fields (bool): If True, unknown fields in the input data
            will be ignored during deserialization.
        aliases (Optional[dict[str, str]]): A dictionary mapping attribute names
            to their aliases. This allows for renaming attributes during
            serialization/deserialization.  Defaults to None.
        omit_none (bool): If True, attributes with None values will be omitted
            from the serialized output. Defaults to False.
        custom_serializers (Optional[dict[str, Callable[[Any], Any]]]): A dictionary
            mapping attribute names to custom serializer functions. These functions
            will be called to serialize the corresponding attribute. Defaults to None.
        custom_deserializers (Optional[dict[str, Callable[[Any], Any]]]): A dictionary
            mapping attribute names to custom deserializer functions. These functions
            will be called to deserialize the corresponding attribute. Defaults to None.
        post_deserialize_hook_name (Optional[str]): The name of a method to be called
            after deserialization. This method should be defined in the class and
            will be called with no arguments. Defaults to "__post_deserialize__".
        translate_snake_to_camel (bool): If True, attribute names will be converted
            from snake_case to camelCase during serialization. Defaults to False.
    """

    def decorator(cls: type[_T]) -> type[_T]:
        # --- Caching introspection results at decoration time ---
        # Use a unique prefix for cached attributes to avoid potential collisions.
        cached_type_hints_attr = f"_jstreams_cached_type_hints_{cls.__name__}"
        cached_init_params_attr = f"_jstreams_cached_init_params_{cls.__name__}"
        cached_reverse_aliases_attr = f"_jstreams_cached_reverse_aliases_{cls.__name__}"
        cached_slots_attr = f"_jstreams_cached_slots_{cls.__name__}"

        # Cache type hints
        if not hasattr(cls, cached_type_hints_attr):
            try:
                hints = get_type_hints(cls)
                setattr(cls, cached_type_hints_attr, hints)
            except Exception:  # get_type_hints can fail in some edge cases
                setattr(cls, cached_type_hints_attr, {})

        # Cache __init__ parameters
        if not hasattr(cls, cached_init_params_attr):
            try:
                init_sig = inspect.signature(cls.__init__)
                setattr(cls, cached_init_params_attr, init_sig.parameters)
            except (ValueError, TypeError):  # Not inspectable
                setattr(cls, cached_init_params_attr, {})

        # Cache reverse aliases
        if not hasattr(cls, cached_reverse_aliases_attr):
            setattr(
                cls,
                cached_reverse_aliases_attr,
                {v: k for k, v in (aliases or {}).items()},
            )

        # Cache __slots__ as a set for efficient lookup
        if not hasattr(cls, cached_slots_attr):
            if hasattr(cls, "__slots__"):
                defined_slots = cls.__slots__  # type: ignore[attr-defined]
                if isinstance(defined_slots, str):
                    setattr(cls, cached_slots_attr, {defined_slots})
                else:  # Assuming iterable
                    setattr(cls, cached_slots_attr, set(defined_slots))
            else:
                setattr(cls, cached_slots_attr, set())  # Empty set if no slots

        # --- End Caching ---

        def to_dict(self: _T) -> dict[str, Any]:
            return _to_dict_convert_name(self, convert_names=True)

        def _to_dict_convert_name(self: _T, convert_names: bool) -> dict[str, Any]:
            serialized_data: dict[str, Any] = {}
            aliases_map_local = aliases or {}
            custom_serializers_map_local = custom_serializers or {}

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

            for attr_name, raw_value in attributes_map.items():
                if not attr_name.startswith(
                    "_"
                ):  # Exclude "private" or "protected" attributes
                    processed_value: Any
                    if attr_name in custom_serializers_map_local:
                        processed_value = custom_serializers_map_local[attr_name](
                            raw_value
                        )
                    else:
                        processed_value = _process_value(raw_value)

                    if omit_none and processed_value is None:
                        continue

                    output_key = aliases_map_local.get(attr_name, attr_name)
                    if translate_snake_to_camel and convert_names:
                        output_key = _snake_to_camel(output_key)
                    serialized_data[output_key] = processed_value

            return serialized_data

        def from_dict(cls_target: type[_T], data: dict[str, Any]) -> _T:
            """
            Creates an instance of the class from a dictionary.
            Recursively deserializes nested objects based on type hints.
            """
            # Retrieve cached introspection results
            all_type_hints = getattr(cls_target, cached_type_hints_attr)
            init_params = getattr(cls_target, cached_init_params_attr)
            reverse_aliases_map = getattr(cls_target, cached_reverse_aliases_attr)
            cls_slots = getattr(
                cls_target, cached_slots_attr
            )  # Retrieve cached slots set

            custom_deserializers_map_local = custom_deserializers or {}

            init_kwargs: dict[str, Any] = {}
            extra_data: dict[str, Any] = {}  # For data not used in __init__

            # Prepare arguments for __init__ by deserializing them
            for key_from_data, value_from_data in data.items():
                sanitized_key = key_from_data
                if translate_snake_to_camel:
                    sanitized_key = _camel_to_snake(key_from_data)
                attr_name = reverse_aliases_map.get(sanitized_key, sanitized_key)

                if attr_name in init_params and init_params[attr_name].name != "self":
                    param = init_params[attr_name]
                    # Determine the type hint for the __init__ parameter
                    param_type_hint = param.annotation
                    if param_type_hint is inspect.Parameter.empty:
                        # If __init__ param has no type hint, try class-level hint
                        param_type_hint = all_type_hints.get(attr_name, Any)

                    if attr_name in custom_deserializers_map_local:
                        init_kwargs[attr_name] = custom_deserializers_map_local[
                            attr_name
                        ](value_from_data)

                    else:
                        init_kwargs[attr_name] = _deserialize_value(
                            param_type_hint, value_from_data
                        )
                else:
                    # Store with original (potentially aliased) key if it's not an init param,
                    # or de-aliased name if it was an init param but not used (e.g. **kwargs)
                    # For simplicity, always use de-aliased name for extra_data keys.
                    extra_data[attr_name] = value_from_data

            # Instantiate the object using prepared __init__ arguments
            # This assumes __init__ can handle the provided kwargs.
            # If required __init__ args are missing from data and have no defaults,
            # this will (correctly) raise a TypeError.
            instance = cls_target(**init_kwargs)

            # Set any remaining attributes from `extra_data` using setattr
            for attr_name_from_extra, original_value_from_data in extra_data.items():
                is_known_attribute = False  # Known via slots or type hints
                if attr_name_from_extra in cls_slots:  # Use cached slots
                    is_known_attribute = True

                if not is_known_attribute and attr_name_from_extra in all_type_hints:
                    is_known_attribute = True

                if is_known_attribute:
                    attr_type_hint = all_type_hints.get(attr_name_from_extra, Any)
                    final_value: Any
                    if attr_name_from_extra in custom_deserializers_map_local:
                        final_value = custom_deserializers_map_local[
                            attr_name_from_extra
                        ](original_value_from_data)
                    else:
                        final_value = _deserialize_value(
                            attr_type_hint, original_value_from_data
                        )
                    try:
                        setattr(instance, attr_name_from_extra, final_value)
                    except (
                        AttributeError
                    ):  # e.g., property without setter, or __slots__ issue
                        # Optionally log: f"Warning: Could not set attribute '{key}' on '{cls_target.__name__}'"
                        pass
                elif (
                    not ignore_unknown_fields
                ):  # Attribute is not known, but we are not ignoring unknown fields
                    # Attempt to set it. Deserialize with Any, which processes collections/SerializableObjects
                    # but otherwise uses the value as-is.
                    value_to_set = _deserialize_value(Any, original_value_from_data)
                    try:
                        setattr(instance, attr_name_from_extra, value_to_set)
                    except AttributeError:
                        pass

            # Call post-deserialization hook if it exists
            if post_deserialize_hook_name and hasattr(
                instance, post_deserialize_hook_name
            ):
                hook_method = getattr(instance, post_deserialize_hook_name)
                if callable(hook_method):
                    try:
                        hook_method()
                    except Exception:
                        # Optionally log or handle exception from hook
                        # print(f"Warning: Error in post_deserialize_hook '{post_deserialize_hook_name}': {e}")
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
            self_dict = self._to_dict_convert_name(False)  # type: ignore[attr-defined]
            other_dict = other._to_dict_convert_name(False)  # type: ignore[attr-defined]
            return self_dict == other_dict  # type: ignore[no-any-return]

        def __str__(self: _T) -> str:
            """
            Returns a string representation of the instance.
            This is useful for debugging and logging.
            """
            return f"{self.__class__.__name__}({self._to_dict_convert_name(False)})"  # type: ignore[attr-defined]

        # Add the to_dict method to the class.
        setattr(cls, "to_dict", to_dict)
        setattr(cls, "_to_dict_convert_name", _to_dict_convert_name)
        setattr(cls, "from_dict", classmethod(from_dict))
        setattr(cls, "__eq__", __eq__)
        setattr(cls, "__str__", __str__)
        setattr(cls, "__repr__", __str__)
        return cls

    return decorator


def json_deserialize(class_type: type[_T], data: dict[str, Any]) -> _T:
    """
    Deserialize a dictionary into an instance of the specified class type.
    This function is a convenience wrapper around the from_dict method of the class.
    """
    if not hasattr(class_type, "from_dict"):
        raise TypeError(f"{class_type.__name__} does not have a from_dict method.")
    return class_type.from_dict(data)  # type: ignore


def json_deserialize_list(class_type: type[_T], data: list[dict[str, Any]]) -> list[_T]:
    """
    Deserialize a list of dictionaries into a list of instances of the specified class type.
    """
    if not hasattr(class_type, "from_dict"):
        raise TypeError(f"{class_type.__name__} does not have a from_dict method.")
    for item in data:
        if not isinstance(item, dict):
            raise TypeError(f"Expected a dictionary, got {type(item)}")

    return [class_type.from_dict(item) for item in data]  # type: ignore


def json_serialize(obj: Any) -> dict[str, Any]:
    """
    Serialize an object into a dictionary.
    This function is a convenience wrapper around the to_dict method of the object.
    """
    if not hasattr(obj, "to_dict"):
        raise TypeError(f"{obj.__class__.__name__} does not have a to_dict method.")
    return obj.to_dict()  # type: ignore


def json_serialize_list(obj: list[Any]) -> list[dict[str, Any]]:
    """
    Serialize an list of objects into a list of dictionaries.
    This function is a convenience wrapper around the to_dict method of the object.
    """
    for item in obj:
        if not hasattr(item, "to_dict"):
            raise TypeError(
                f"{item.__class__.__name__} does not have a to_dict method."
            )
    return [item.to_dict() for item in obj]


if sys.version_info >= (3, 10):
    from typing import ParamSpec

    P = ParamSpec("P")
else:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")
# TypeVar for the original return type of a callable
R = TypeVar("R")


def json_serialize_return() -> Callable[  # Type of the decorator factory
    [Callable[P, R]],  # It accepts a callable func(P) -> R
    Callable[P, dict[str, Any]],  # It returns a new callable func(P) -> dict
]:
    """
    Decorator factory to serialize the return value of a function using json_serialize.
    The decorated function will have its return value processed by json_serialize.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, dict[str, Any]]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
            result = func(*args, **kwargs)
            return json_serialize(result)

        return wrapper

    return decorator


def json_serialize_return_list() -> Callable[  # Type of the decorator factory
    [Callable[P, list[R]]],  # It accepts a callable func(P) -> list[R]
    Callable[
        P, list[dict[str, Any]]
    ],  # It returns a new callable func(P) -> list[dict]
]:
    """
    Decorator factory to serialize the return value of a function using json_serialize.
    The decorated function will have its return value processed by json_serialize.
    """

    def decorator(func: Callable[P, list[R]]) -> Callable[P, list[dict[str, Any]]]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[dict[str, Any]]:
            result = func(*args, **kwargs)
            return [json_serialize(item) for item in result]

        return wrapper

    return decorator
