from typing import Any


class ClassOps:
    __slots__ = ("__class_type",)

    def __init__(self, class_type: type) -> None:
        self.__class_type = class_type

    def instance_of(self, obj: Any) -> bool:
        return isinstance(obj, self.__class_type)

    def subclass_of(self, typ: type) -> bool:
        return issubclass(typ, self.__class_type)
