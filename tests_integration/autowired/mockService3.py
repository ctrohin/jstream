from typing import Optional
from jstreams.ioc import (
    autowired,
    autowiredOptional,
    returnWired,
    returnWiredOptional,
    service,
)
from mockService1 import MockService1
from mockService2 import MockService2


@service()
class MockService3:
    @autowired(MockService1)
    def getMockService1(self) -> MockService1:
        return returnWired(MockService1)

    @autowiredOptional(MockService2)
    def getMockService2(self) -> Optional[MockService2]:
        return returnWiredOptional(MockService2)
