from typing import Optional
from jstreams.ioc import (
    autowired,
    autowired_optional,
    return_wired,
    return_wired_optional,
    service,
)
from mockService1 import MockService1
from mockService2 import MockService2


@service()
class MockService3:
    @autowired(MockService1)
    def getMockService1(self) -> MockService1:
        return return_wired(MockService1)

    @autowired_optional(MockService2)
    def getMockService2(self) -> Optional[MockService2]:
        return return_wired_optional(MockService2)
