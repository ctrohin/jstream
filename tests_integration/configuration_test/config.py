from jstreams.ioc import provide, configuration, provideVariable


@configuration(["profile1", "profile2"])
class Config:
    def __init__(self) -> None:
        pass

    @provide(str)
    def test1(self) -> str:
        return "test1"

    @provideVariable(str, "test1")
    def test2(self) -> str:
        return "test1"

    def _test1(self) -> str:
        return "_test1"

    def __test2(self) -> str:
        return "_test2"


@configuration()
class Config2:
    def __init__(self) -> None:
        pass

    @provide(int)
    def test1(self) -> int:
        return 3

    @provideVariable(str, "test2")
    def test2(self) -> str:
        return "test2"

    def _test1(self) -> str:
        return "_test1"

    def __test2(self) -> str:
        return "_test2"
