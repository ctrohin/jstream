from jstreams import synchronized


class TestClass:
    @synchronized()
    def print_something(self, a: int, b: str) -> None:
        print(str(a) + " " + b)

    @synchronized()
    def print_something_else(self) -> None:
        print("something else")

    @synchronized()
    def both(self) -> None:
        self.print_something_else()
        self.print_something(1, "a")


t = TestClass()
t.print_something(10, "test")
t.print_something_else()
t.both()
