import sys
from typing import Optional

sys.path.append(".")

from jstreams import (
    Variable,
    configuration,
    inject_args,
    injector,
    provide_variable,
    component,
    provide,
)

import abc

# The idea of this example is to declare a class of validators, all derived from the same interface.
# Then, we can use those validators to validate objects.


class ValidationInterface(abc.ABC):
    @abc.abstractmethod
    def is_valid(self, obj: Optional[str]) -> bool:
        pass


# This validator will check if the string is lowercase
@component(class_name=ValidationInterface, qualifier="only_lower_case")
class OnlyLowerCaseValidator(ValidationInterface):
    def is_valid(self, obj: Optional[str]) -> bool:
        return obj is not None and obj.lower() == obj


# This validator will validate if the string has a certain length
@component(class_name=ValidationInterface, qualifier="length_validator")
class MaxLengthValidator(ValidationInterface):
    # Here we use the injection mechanism to inject the max_len variable to this validator
    @inject_args({"max_len": Variable(int, "max_len")})
    def __init__(self, max_len: int) -> None:
        super().__init__()
        self.max_len = max_len

    def is_valid(self, obj: Optional[str]) -> bool:
        return obj is not None and len(obj) < self.max_len


# We can also define a non decorated class, that we can provide to the
# injection mechanism using the configuration class below
class NoSpaceValidator(ValidationInterface):
    def is_valid(self, obj: Optional[str]) -> bool:
        return obj is not None and " " not in obj


# Then we can provide a set of dependencies using a configuration class
@configuration()
class InjectorConfig:
    # Here we define the max_len variable that will be injected in the `MaxLengthValidator` class
    @provide_variable(int, "max_len")
    def get_max_len(self) -> int:
        return 10

    @provide(ValidationInterface, "no_space_validator")
    def get_no_space_validator(self) -> ValidationInterface:
        return NoSpaceValidator()


# In this validation method, we retrieve all classes that implement our `ValidationInterface` in order
# to validate the given value
def validate(obj: str) -> bool:
    return (
        injector()
        .all_of_type_stream(ValidationInterface)
        .all_match(lambda v: v.is_valid(obj))
    )


# This string should match both validator
is_valid = validate("test")
print("Matches", is_valid)
assert is_valid

# This string will not match the lower case validator
is_valid = validate("Test")
print("Matches", is_valid)
assert not is_valid

# This string will not match the no space validator
is_valid = validate("t est")
print("Matches", is_valid)
assert not is_valid

# This string will not match the length validator
is_valid = validate("test_a_string_that_is_way_too_long")
print("Matches", is_valid)
assert not is_valid
