from jstreams.ioc import service
from iMockService1 import IMockService


@service(className=IMockService)
class MockService1(IMockService):
    pass
