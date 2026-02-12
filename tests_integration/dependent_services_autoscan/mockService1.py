from jstreams.ioc import service
from interfaces import IMockService1


@service(class_name=IMockService1)
class MockService1(IMockService1):
    pass
