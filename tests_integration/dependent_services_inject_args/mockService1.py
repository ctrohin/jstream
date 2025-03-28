from jstreams.ioc import service
from iMockService1 import IMockService


@service(class_name=IMockService)
class MockService1(IMockService):
    pass
