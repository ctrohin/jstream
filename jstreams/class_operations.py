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
        return isinstance(obj, self.__class_type)

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
