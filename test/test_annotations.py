import threading
import time
from typing import Optional
from baseTest import BaseTestCase
from jstreams.annotations import (
    all_args,
    getter,
    locked,
    required_args,
    setter,
    builder,
)


# --- Test Subject Class for @locked ---
class UnsafeCounter:
    """A simple counter class, intentionally not thread-safe."""

    def __init__(self, initial_value: int = 0) -> None:
        # print(f"Initializing UnsafeCounter with {initial_value}") # Keep commented out unless debugging
        self.value = initial_value
        self._internal_state = "initialized"  # Example protected member

    def increment(self, amount: int = 1) -> None:
        """Increments the counter (simulates work)."""
        # print(f"{threading.current_thread().name}: Reading value {self.value}") # Keep commented out
        current_value = self.value  # Read
        time.sleep(0.01)  # Simulate work/potential race condition
        self.value = current_value + amount  # Write
        # print(f"{threading.current_thread().name}: Incremented to {self.value}") # Keep commented out

    def get_value(self) -> int:
        """Returns the current value."""
        # print(f"{threading.current_thread().name}: Getting value {self.value}") # Keep commented out
        return self.value

    def complex_operation(self, amount1: int, amount2: int) -> int:
        """Calls increment multiple times to test reentrancy."""
        self.increment(amount1)
        time.sleep(0.005)
        self.increment(amount2)
        return self.get_value()

    def get_internal_state(self) -> str:
        """Accesses a 'protected' member."""
        return self._internal_state

    def __str__(self) -> str:
        return f"UnsafeCounter(value={self.value})"

    def __repr__(self) -> str:
        return f"UnsafeCounter({self.value})"


class InitErrorCounter:
    def __init__(self) -> None:
        raise ValueError("Failed to initialize")


class TestAnnotations(BaseTestCase):
    def test_getter(self) -> None:
        @getter()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @getter()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance = Test()
        test_instance.var1 = "value1"
        test_instance.var2 = 123
        test_instance.var3 = "value3"

        self.assertEqual(test_instance.get_var1(), "value1")
        self.assertEqual(test_instance.get_var2(), 123)
        self.assertEqual(test_instance.get_var3(), "value3")

        other_test_instance = OtherTest()
        other_test_instance.other_var = "test"
        other_test_instance.other_var2 = 2.3

        self.assertEqual(other_test_instance.get_other_var(), "test")
        self.assertEqual(other_test_instance.get_other_var2(), 2.3)

        self.assertRaises(AttributeError, lambda: test_instance.get_unknown())
        self.assertRaises(AttributeError, lambda: test_instance.get__var_private())

    def test_setter(self) -> None:
        @setter()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @setter()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance = Test()
        test_instance.set_var1("value1")
        test_instance.set_var2(123)
        test_instance.set_var3("value3")

        self.assertEqual(test_instance.var1, "value1")
        self.assertEqual(test_instance.var2, 123)
        self.assertEqual(test_instance.var3, "value3")

        other_test_instance = OtherTest()
        other_test_instance.set_other_var("test")
        other_test_instance.set_other_var2(2.3)

        self.assertEqual(other_test_instance.other_var, "test")
        self.assertEqual(other_test_instance.other_var2, 2.3)
        self.assertRaises(AttributeError, lambda: test_instance.set_unknown(1))
        self.assertRaises(AttributeError, lambda: test_instance.set__var_private(1))

    def test_builder(self) -> None:
        @builder()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @builder()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance: Test = (
            Test.builder()
            .with_var1("value1")
            .with_var2(123)
            .with_var3("value3")
            .build()
        )

        self.assertEqual(test_instance.var1, "value1")
        self.assertEqual(test_instance.var2, 123)
        self.assertEqual(test_instance.var3, "value3")

        other_test_instance: OtherTest = (
            OtherTest.builder().with_other_var("test").with_other_var2(2.3).build()
        )

        self.assertEqual(other_test_instance.other_var, "test")
        self.assertEqual(other_test_instance.other_var2, 2.3)
        self.assertRaises(
            AttributeError, lambda: Test.builder().with_unknown(1).build()
        )
        self.assertRaises(
            AttributeError, lambda: Test.builder().with__var_private(1).build()
        )

    def test_locked_single_thread(self) -> None:
        """Tests basic functionality of @locked in a single thread."""
        LockedCounter = locked()(UnsafeCounter)  # Apply decorator manually for testing
        counter = LockedCounter(10)

        self.assertEqual(counter.get_value(), 10)
        counter.increment(5)
        self.assertEqual(counter.get_value(), 15)
        counter.value = 50  # Test direct attribute setting
        self.assertEqual(counter.get_value(), 50)
        self.assertEqual(
            counter.get_internal_state(), "initialized"
        )  # Test reading protected-like attr

        # Test special methods
        self.assertTrue("ThreadSafeWrapper" in repr(counter))
        self.assertTrue("UnsafeCounter(value=50)" in str(counter))

    def test_locked_multi_thread_race_condition(self) -> None:
        """Tests if @locked prevents race conditions with multiple threads."""
        LockedCounter = locked()(UnsafeCounter)
        counter = LockedCounter(0)  # Shared instance

        num_threads = 10
        increments_per_thread = 20
        threads = []

        def worker() -> None:
            for _ in range(increments_per_thread):
                counter.increment()  # Access shared instance

        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"Worker-{i + 1}")
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        expected_value = num_threads * increments_per_thread
        actual_value = counter.get_value()
        self.assertEqual(
            actual_value,
            expected_value,
            "Counter value should be correct after concurrent increments",
        )

    def test_locked_multi_thread_reentrancy(self) -> None:
        """Tests if RLock allows reentrant calls within the same thread."""
        LockedCounter = locked()(UnsafeCounter)
        counter = LockedCounter(0)  # Shared instance

        num_threads = 5
        ops_per_thread = 10
        threads = []

        def worker() -> None:
            for _ in range(ops_per_thread):
                # This method calls increment internally, testing reentrancy
                counter.complex_operation(2, 3)  # Total increment of 5 per call

        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"ReentrantWorker-{i + 1}")
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        expected_value = num_threads * ops_per_thread * 5  # 5 = 2 + 3
        actual_value = counter.get_value()
        self.assertEqual(
            actual_value,
            expected_value,
            "Counter value should be correct after concurrent complex operations",
        )

    def test_locked_attribute_errors(self) -> None:
        """Tests attribute access errors on the locked wrapper."""
        LockedCounter = locked()(UnsafeCounter)
        counter = LockedCounter(0)

        # Test getting non-existent attribute
        with self.assertRaisesRegex(
            AttributeError,
            "'UnsafeCounter' object \(wrapped\) has no attribute 'non_existent'",
        ):
            getattr(counter, "non_existent")

    def test_locked_init_exception(self) -> None:
        """Tests that exceptions during original __init__ are propagated."""
        LockedInitErrorCounter = locked()(InitErrorCounter)

        with self.assertRaisesRegex(ValueError, "Failed to initialize"):
            LockedInitErrorCounter()  # Instantiation should raise the error from original __init__

    def test_locked_metadata(self) -> None:
        """Tests if the wrapper preserves some metadata."""

        @locked()
        class MyOriginalClass:
            """This is the original docstring."""

            pass

        self.assertEqual(MyOriginalClass.__name__, "ThreadSafeMyOriginalClass")
        self.assertIn(
            "Thread-safe wrapper around MyOriginalClass", MyOriginalClass.__doc__
        )
        self.assertIn("This is the original docstring.", MyOriginalClass.__doc__)

    def test_required_args(self) -> None:
        @required_args()
        class Test:
            a: int
            b: str
            c: Optional[int]
            d: Optional[str]

        t = Test.required(10, "test")
        self.assertEqual(t.a, 10)
        self.assertEqual(t.b, "test")
        self.assertIsNone(t.c)
        self.assertIsNone(t.d)

        self.assertRaises(TypeError, lambda: Test.required(10))
        self.assertRaises(TypeError, lambda: Test.required(10, "test", 2, "test2"))

    def test_all_args(self) -> None:
        @all_args()
        class Test:
            a: int
            b: str
            c: Optional[int] = None
            d: Optional[str] = None

        t = Test.all(10, "test", 2, "test2")
        self.assertEqual(t.a, 10)
        self.assertEqual(t.b, "test")
        self.assertEqual(t.c, 2)
        self.assertEqual(t.d, "test2")

        self.assertRaises(TypeError, lambda: Test.all())
        self.assertRaises(TypeError, lambda: Test.all(10))
        self.assertRaises(TypeError, lambda: Test.all(10, "str"))
        self.assertRaises(TypeError, lambda: Test.all(10, "str", 4))
        self.assertRaises(TypeError, lambda: Test.all(10, "test", 2, "test2", 2))
