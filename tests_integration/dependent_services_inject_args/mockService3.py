from jstreams.ioc import StrVariable, inject_args, service
from iMockService1 import IMockService
from mockService2 import MockService2


@service()
class MockService3:
    @inject_args(
        {
            "mockService1": IMockService,
            "mockService2": MockService2,
            "var1": StrVariable("var1"),
        }
    )
    def __init__(
        self, mockService1: IMockService, mockService2: MockService2, var1: str
    ) -> None:
        self.mockService1 = mockService1
        self.mockService2 = mockService2
        self.var1 = var1

    def getMockService1Class(self) -> type:
        return type(self.mockService1)

    def getMockService2Class(self) -> type:
        return type(self.mockService2)
