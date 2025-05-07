from typing import Any


class ClassOps:
    __slots__ = ("__class_type",)

    def __init__(self, class_type: type) -> None:
        self.__class_type = class_type

    def instance_of(self, obj: Any) -> bool:
        """
        Checks if the given object is of this `ClassOps` instance

        Args:
            obj (Any): The given object

        Returns:
            bool: True if the object is an instance, False otherwise
        """
        return type(obj) == self.__class_type

    def instance_of_subclass(self, obj: Any) -> bool:
        """
        Checks if the given object is of this `ClassOps` instance or a subclass of it

        Args:
            obj (Any): The given object

        Returns:
            bool: True if the object is an instance or instance of a subclass, False otherwise
        """
        return self.subclass_of(type(obj))

    def subclass_of(self, typ: type) -> bool:
        """
        Checks if the given class is a subclass of this `ClassOps` type

        Args:
            typ (type): The given type

        Returns:
            bool: True if the type is a subclass, False otherwise
        """
        return issubclass(typ, self.__class_type)

    def is_same_type(self, typ: type) -> bool:
        """
        Checks if the given type is exactly the same as this `ClassOps` type.

        Args:
            typ (type): The given type

        Returns:
            bool: True if the types are identical, False otherwise
        """
        return typ is self.__class_type

    def has_attribute(self, attr_name: str) -> bool:
        """
        Checks if the class type itself has the specified attribute.

        Args:
            attr_name (str): The name of the attribute to check for.

        Returns:
            bool: True if the class has the attribute, False otherwise.
        """
        return hasattr(self.__class_type, attr_name)

    def get_name(self) -> str:
        """
        Returns the name of the class type.

        Returns:
            str: The class name.
        """
        return self.__class_type.__name__

    def not_instance_of(self, obj: Any) -> bool:
        """
        Checks if the given object is *not* an instance of this `ClassOps` type.

        Args:
            obj (Any): The given object

        Returns:
            bool: True if the object is not an instance, False otherwise
        """
        return not isinstance(obj, self.__class_type)
