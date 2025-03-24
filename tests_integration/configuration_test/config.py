from jstreams.ioc import bean, configuration


@configuration(["profile1", "profile2"])
class Config:
    def __init__(self) -> None:
        pass

    @bean(str)
    def test1(self) -> str:
        return "test1"

    def test2(self) -> str:
        return "test2"

    def _test1(self) -> str:
        return "_test1"

    def __test2(self) -> str:
        return "_test2"


@configuration()
class Config2:
    def __init__(self) -> None:
        pass

    @bean(int)
    def test1(self) -> int:
        return 3

    def test2(self) -> str:
        return "test2"

    def _test1(self) -> str:
        return "_test1"

    def __test2(self) -> str:
        return "_test2"
