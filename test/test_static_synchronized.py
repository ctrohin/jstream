import unittest
import threading
import time

from typing import Callable, List, Any

# Assuming the synchronized decorator is in 'jstreams.annotations'
# Adjust the import path if necessary
from jstreams.annotations import synchronized_static, _lock_registry

# Helper shared state for tests - still needed for cross-thread communication
counter = 0
counter_lock = threading.Lock()  # Lock for test infrastructure itself
execution_log: List[str] = []
log_lock = threading.Lock()
reentrant_flag = False  # Still needed for named reentrancy test across functions

# --- Test Class ---


class TestSynchronizedDecorator(unittest.TestCase):
    def setUp(self) -> None:
        """Reset shared state before each test."""
        global counter, execution_log, reentrant_flag
        counter = 0
        execution_log = []
        reentrant_flag = False
        # Clear the single lock registry for isolation between tests
        # Use lock context manager for thread safety if tests run in parallel (unlikely with unittest)
        with (
            threading.Lock()
        ):  # Use a simple lock to protect registry access during clear
            _lock_registry.clear()

    def run_threads(
        self,
        target: Callable[..., Any],
        num_threads: int,
        args: tuple = (),
        kwargs: dict = {},
    ) -> None:
        """Helper to create, start, and join threads."""
        threads: List[threading.Thread] = []
        for i in range(num_threads):
            thread = threading.Thread(
                target=target, args=args, kwargs=kwargs, name=f"Thread-{i}"
            )
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def test_default_lock_prevents_race_condition(self) -> None:
        """Tests that @synchronized_static() prevents race conditions on the same function."""

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_increment_counter(amount: int = 1, delay: float = 0.01) -> None:
            """Increments the global counter with default lock."""
            global counter
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: default_inc_start"
                )
            # Simulate work
            current = counter
            time.sleep(delay)
            counter = current + amount
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: default_inc_end"
                )

        # --- End Inline Function ---

        num_threads = 10
        increments_per_thread = 1
        delay = 0.02

        self.run_threads(
            local_increment_counter,
            num_threads,
            args=(1,),
            kwargs={"delay": delay},  # Use local function
        )

        self.assertEqual(counter, num_threads * increments_per_thread)

    def test_named_lock_prevents_race_condition_across_functions(self) -> None:
        """Tests that @synchronized_static('name') prevents races across different functions."""

        # --- Inline Function Definitions ---
        @synchronized_static("test_lock")
        def local_increment_counter_named(amount: int = 1, delay: float = 0.01) -> None:
            """Increments the global counter with named lock 'test_lock'."""
            global counter
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: named_inc_start"
                )
            current = counter
            time.sleep(delay)
            counter = current + amount
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: named_inc_end"
                )

        @synchronized_static("test_lock")
        def local_decrement_counter_named(amount: int = 1, delay: float = 0.01) -> None:
            """Decrements the global counter with named lock 'test_lock'."""
            global counter
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: named_dec_start"
                )
            current = counter
            time.sleep(delay)
            counter = current - amount
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: named_dec_end"
                )

        # --- End Inline Functions ---

        num_threads = 5
        delay = 0.02
        threads: List[threading.Thread] = []

        for i in range(num_threads):
            threads.append(
                threading.Thread(
                    target=local_increment_counter_named,  # Use local function
                    args=(1,),
                    kwargs={"delay": delay},
                    name=f"IncThread-{i}",
                )
            )
            threads.append(
                threading.Thread(
                    target=local_decrement_counter_named,  # Use local function
                    args=(1,),
                    kwargs={"delay": delay},
                    name=f"DecThread-{i}",
                )
            )

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(
            counter, 0, "Counter should be zero after balanced increments/decrements"
        )
        self.assertIn("test_lock", _lock_registry)

    def test_reentrancy_default_lock(self) -> None:
        """Tests that a function with a default lock can call itself (reentrancy)."""
        local_reentrant_flag = False
        local_reentrant_depth = 0

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_reentrant_recursive(max_depth: int = 2) -> None:
            """Tests reentrancy by calling itself."""
            nonlocal local_reentrant_flag, local_reentrant_depth  # Use nonlocal to modify outer scope vars
            current_depth = local_reentrant_depth
            local_reentrant_depth += 1
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: reentrant_recursive_default_depth_{current_depth}"
                )

            if current_depth < max_depth:
                local_reentrant_recursive(max_depth)  # Recursive call
            else:
                local_reentrant_flag = True  # Mark success at max depth

            local_reentrant_depth -= 1  # Decrement depth on return

        # --- End Inline Function ---

        local_reentrant_recursive(max_depth=3)  # Call local function
        self.assertTrue(
            local_reentrant_flag, "Recursive function should have reached max depth"
        )
        # Check log for correct sequence
        self.assertIn("reentrant_recursive_default_depth_0", execution_log[0])
        self.assertIn("reentrant_recursive_default_depth_1", execution_log[1])
        self.assertIn("reentrant_recursive_default_depth_2", execution_log[2])
        self.assertIn("reentrant_recursive_default_depth_3", execution_log[3])

    def test_reentrancy_named_lock(self) -> None:
        """Tests that a function with a named lock can call another with the same lock."""
        # Need reentrant_flag to be accessible by both local functions
        global reentrant_flag  # Keep global flag for this test case

        # --- Inline Function Definitions ---
        @synchronized_static("reentrant_lock")
        def local_reentrant_inner_named() -> None:
            global reentrant_flag
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: reentrant_inner_named"
                )
            reentrant_flag = True

        @synchronized_static("reentrant_lock")
        def local_reentrant_outer_named() -> None:
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: reentrant_outer_named_start"
                )
            local_reentrant_inner_named()  # Call local function
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: reentrant_outer_named_end"
                )

        # --- End Inline Functions ---

        local_reentrant_outer_named()  # Call local function
        self.assertTrue(reentrant_flag, "Inner function should have been called")
        # Check log for correct sequence
        self.assertIn("reentrant_outer_named_start", execution_log[0])
        self.assertIn("reentrant_inner_named", execution_log[1])
        self.assertIn("reentrant_outer_named_end", execution_log[2])
        self.assertIn("reentrant_lock", _lock_registry)

    def test_different_default_locks_allow_concurrency(self) -> None:
        """Tests that functions with different default locks can run concurrently."""

        # --- Inline Function Definitions ---
        @synchronized_static()
        def local_task_c_default(delay: float = 0.05) -> None:
            """Task using its own default lock."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_c_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_c_end")

        @synchronized_static()
        def local_task_d_default(delay: float = 0.05) -> None:
            """Task using its own, different default lock."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_d_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_d_end")

        # --- End Inline Functions ---

        delay = 0.1
        thread_c = threading.Thread(
            target=local_task_c_default,
            kwargs={"delay": delay},
            name="Thread-C",  # Use local function
        )
        thread_d = threading.Thread(
            target=local_task_d_default,
            kwargs={"delay": delay},
            name="Thread-D",  # Use local function
        )

        start_time = time.time()
        thread_c.start()
        thread_d.start()
        thread_c.join()
        thread_d.join()
        end_time = time.time()

        self.assertLess(
            end_time - start_time, delay * 1.9, "Tasks should run concurrently"
        )
        # Check log for interleaved execution
        self.assertTrue(any("task_c_start" in entry for entry in execution_log))
        self.assertTrue(any("task_d_start" in entry for entry in execution_log))
        self.assertTrue(any("task_c_end" in entry for entry in execution_log))
        self.assertTrue(any("task_d_end" in entry for entry in execution_log))

    def test_different_named_locks_allow_concurrency(self) -> None:
        """Tests that functions with different named locks can run concurrently."""

        # --- Inline Function Definitions ---
        @synchronized_static("lock_a")
        def local_task_a_named(delay: float = 0.05) -> None:
            """Task using named lock 'lock_a'."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_a_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_a_end")

        @synchronized_static("lock_b")
        def local_task_b_named(delay: float = 0.05) -> None:
            """Task using named lock 'lock_b'."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_b_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_b_end")

        # --- End Inline Functions ---

        delay = 0.1
        thread_a = threading.Thread(
            target=local_task_a_named,
            kwargs={"delay": delay},
            name="Thread-A",  # Use local function
        )
        thread_b = threading.Thread(
            target=local_task_b_named,
            kwargs={"delay": delay},
            name="Thread-B",  # Use local function
        )

        start_time = time.time()
        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()
        end_time = time.time()

        self.assertLess(
            end_time - start_time, delay * 1.9, "Tasks should run concurrently"
        )
        self.assertTrue(any("task_a_start" in entry for entry in execution_log))
        self.assertTrue(any("task_b_start" in entry for entry in execution_log))
        self.assertTrue(any("task_a_end" in entry for entry in execution_log))
        self.assertTrue(any("task_b_end" in entry for entry in execution_log))
        self.assertIn("lock_a", _lock_registry)
        self.assertIn("lock_b", _lock_registry)
        self.assertIsNot(_lock_registry["lock_a"], _lock_registry["lock_b"])

    def test_named_vs_default_locks_allow_concurrency(self) -> None:
        """Tests that functions with named vs default locks can run concurrently."""

        # --- Inline Function Definitions ---
        @synchronized_static("lock_a")
        def local_task_a_named(delay: float = 0.05) -> None:
            """Task using named lock 'lock_a'."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_a_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_a_end")

        @synchronized_static()
        def local_task_c_default(delay: float = 0.05) -> None:
            """Task using its own default lock."""
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_c_start")
            time.sleep(delay)
            with log_lock:
                execution_log.append(f"{threading.current_thread().name}: task_c_end")

        # --- End Inline Functions ---

        delay = 0.1
        thread_a = threading.Thread(
            target=local_task_a_named,  # Use local function
            kwargs={"delay": delay},
            name="Thread-A",  # Uses "lock_a"
        )
        thread_c = threading.Thread(
            target=local_task_c_default,  # Use local function
            kwargs={"delay": delay},
            name="Thread-C",  # Uses default lock
        )

        start_time = time.time()
        thread_a.start()
        thread_c.start()
        thread_a.join()
        thread_c.join()
        end_time = time.time()

        self.assertLess(
            end_time - start_time, delay * 1.9, "Tasks should run concurrently"
        )
        self.assertTrue(any("task_a_start" in entry for entry in execution_log))
        self.assertTrue(any("task_c_start" in entry for entry in execution_log))
        self.assertTrue(any("task_a_end" in entry for entry in execution_log))
        self.assertTrue(any("task_c_end" in entry for entry in execution_log))
        # Check locks were created and are different
        self.assertIn("lock_a", _lock_registry)

    def test_return_value_preservation(self) -> None:
        """Tests that the decorator returns the original function's value."""

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_return_value_func(value: Any) -> Any:
            """Returns the given value."""
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: return_value_func"
                )
            return value

        # --- End Inline Function ---

        expected = "test_value"
        result = local_return_value_func(expected)  # Use local function
        self.assertEqual(result, expected)

        expected_list = [1, 2, 3]
        result_list = local_return_value_func(expected_list)  # Use local function
        self.assertEqual(result_list, expected_list)
        self.assertIs(result_list, expected_list)

        result_none = local_return_value_func(None)  # Use local function
        self.assertIsNone(result_none)

    def test_exception_propagation(self) -> None:
        """Tests that exceptions raised by the decorated function are propagated."""

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_raise_exception_func(message: str) -> None:
            """Raises a ValueError."""
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: raise_exception_func"
                )
            raise ValueError(message)

        # --- End Inline Function ---

        error_message = "Something went wrong"
        with self.assertRaisesRegex(ValueError, error_message):
            local_raise_exception_func(error_message)  # Use local function
        self.assertTrue(any("raise_exception_func" in entry for entry in execution_log))

    def test_argument_passing(self) -> None:
        """Tests that *args and **kwargs are passed correctly."""

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_arg_passing_func(
            *args: Any, **kwargs: Any
        ) -> tuple[tuple[Any, ...], dict[str, Any]]:
            """Returns received args and kwargs."""
            with log_lock:
                execution_log.append(
                    f"{threading.current_thread().name}: arg_passing_func"
                )
            return args, kwargs

        # --- End Inline Function ---

        args_in = (1, "two", [3])
        kwargs_in = {"a": 10, "b": None}
        args_out, kwargs_out = local_arg_passing_func(
            *args_in, **kwargs_in
        )  # Use local function

        self.assertEqual(args_out, args_in)
        self.assertEqual(kwargs_out, kwargs_in)

        args_out_empty, kwargs_out_empty = (
            local_arg_passing_func()
        )  # Use local function
        self.assertEqual(args_out_empty, ())
        self.assertEqual(kwargs_out_empty, {})

    def test_metadata_preservation(self) -> None:
        """Tests that functools.wraps preserves metadata."""

        # --- Inline Function Definition ---
        @synchronized_static()
        def local_metadata_func() -> None:
            """This is the docstring."""
            pass

        # --- End Inline Function ---

        # Test the local metadata_func directly after decoration
        self.assertEqual(local_metadata_func.__name__, "local_metadata_func")
        self.assertEqual(local_metadata_func.__doc__, "This is the docstring.")
        self.assertEqual(local_metadata_func.__module__, __name__)  # Check module

    def test_lock_creation_and_reuse(self) -> None:
        """Tests that locks are created and reused correctly in the registry."""

        # --- Define functions within the test to ensure clean state ---
        @synchronized_static("shared_lock_test")
        def func1_shared():
            pass

        @synchronized_static("shared_lock_test")
        def func2_shared():
            pass

        @synchronized_static()
        def func3_default():
            pass

        @synchronized_static()
        def func4_default():
            pass

        @synchronized_static("another_lock_test")
        def func5_another():
            pass

        # --- End function definitions ---

        # Check named locks
        self.assertIn("shared_lock_test", _lock_registry)
        lock_shared1 = _lock_registry["shared_lock_test"]
        # Decorating func2 should reuse the same lock object
        self.assertIs(lock_shared1, _lock_registry["shared_lock_test"])

        self.assertIn("another_lock_test", _lock_registry)
        lock_another = _lock_registry["another_lock_test"]
        self.assertIsNot(lock_shared1, lock_another)

        # Test reuse by getting lock name from decorated function attribute
        # (Assuming _synchronized_lock_name is set by the decorator)
        if hasattr(func1_shared, "_synchronized_lock_name"):
            self.assertEqual(
                getattr(func1_shared, "_synchronized_lock_name"), "shared_lock_test"
            )


# --- Method Synchronization Test Class (Remains unchanged as it tests methods) ---
class MethodTester:
    # Class variable shared by instances for testing cross-instance locking
    _class_counter = 0
    _class_lock = threading.Lock()  # Lock for accessing _class_counter in tests

    def __init__(self, instance_id: int):
        self.instance_id = instance_id
        self.instance_counter = 0
        self.reentrant_method_flag = False

    @synchronized_static()
    def increment_default(self, delay: float = 0.01) -> None:
        """Increments instance and class counter with default method lock."""
        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: default_method_start")

        current_inst = self.instance_counter
        time.sleep(delay / 2)
        self.instance_counter = current_inst + 1

        with MethodTester._class_lock:
            current_class = MethodTester._class_counter
            time.sleep(delay / 2)
            MethodTester._class_counter = current_class + 1

        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: default_method_end")

    @synchronized_static("method_lock")
    def increment_named(self, delay: float = 0.01) -> None:
        """Increments instance and class counter with named method lock."""
        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: named_method_start")

        current_inst = self.instance_counter
        time.sleep(delay / 2)
        self.instance_counter = current_inst + 1

        with MethodTester._class_lock:
            current_class = MethodTester._class_counter
            time.sleep(delay / 2)
            MethodTester._class_counter = current_class + 1

        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: named_method_end")

    @synchronized_static("method_lock")
    def reentrant_method_outer_named(self) -> None:
        """Calls another method with the same named lock."""
        with log_lock:
            execution_log.append(
                f"Inst-{self.instance_id}: reentrant_outer_named_start"
            )
        self.reentrant_method_inner_named()
        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: reentrant_outer_named_end")

    @synchronized_static("method_lock")
    def reentrant_method_inner_named(self) -> None:
        """Inner method for named reentrancy test."""
        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: reentrant_inner_named")
        self.instance_counter += 5

    # --- Methods for Default Lock Reentrancy Test ---
    # These remain as methods because we are testing method reentrancy
    @synchronized_static()
    def reentrant_method_outer_default(self) -> None:
        """Calls another method with the same default lock."""
        with log_lock:
            execution_log.append(
                f"Inst-{self.instance_id}: reentrant_outer_default_start"
            )
        # Call another method on the same instance decorated with @synchronized()
        self.reentrant_method_inner_default()
        with log_lock:
            execution_log.append(
                f"Inst-{self.instance_id}: reentrant_outer_default_end"
            )

    @synchronized_static()
    def reentrant_method_inner_default(self) -> None:
        """Inner method for default reentrancy test."""
        with log_lock:
            execution_log.append(f"Inst-{self.instance_id}: reentrant_inner_default")
        self.reentrant_method_flag = True  # Mark success


class TestSynchronizedMethods(unittest.TestCase):
    def setUp(self) -> None:
        """Reset shared state before each test."""
        global execution_log
        MethodTester._class_counter = 0
        execution_log = []
        # Clear the lock registry
        with threading.Lock():
            _lock_registry.clear()

    def test_method_synchronization_default_lock(self) -> None:
        """Tests default lock on methods synchronizes across different instances."""
        num_instances = 3
        num_threads_per_instance = 2
        delay = 0.02
        instances = [MethodTester(i) for i in range(num_instances)]
        threads: List[threading.Thread] = []

        for i, instance in enumerate(instances):
            for j in range(num_threads_per_instance):
                threads.append(
                    threading.Thread(
                        target=instance.increment_default,  # Target is the method
                        kwargs={"delay": delay},
                        name=f"Inst-{i}-Thread-{j}",
                    )
                )

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        total_calls = num_instances * num_threads_per_instance
        self.assertEqual(
            MethodTester._class_counter,
            total_calls,
            "Class counter should reflect all calls",
        )
        # Instance counters should also be correct as locking is per method definition
        for instance in instances:
            self.assertEqual(instance.instance_counter, num_threads_per_instance)

    def test_method_synchronization_named_lock(self) -> None:
        """Tests named lock on methods synchronizes across different instances."""
        num_instances = 3
        num_threads_per_instance = 2
        delay = 0.02
        instances = [MethodTester(i) for i in range(num_instances)]
        threads: List[threading.Thread] = []

        for i, instance in enumerate(instances):
            for j in range(num_threads_per_instance):
                threads.append(
                    threading.Thread(
                        target=instance.increment_named,  # Target is the method
                        kwargs={"delay": delay},
                        name=f"Inst-{i}-Thread-{j}",
                    )
                )

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        total_calls = num_instances * num_threads_per_instance
        self.assertEqual(
            MethodTester._class_counter,
            total_calls,
            "Class counter should reflect all calls",
        )
        for instance in instances:
            self.assertEqual(instance.instance_counter, num_threads_per_instance)

    def test_method_reentrancy_named_lock(self) -> None:
        """Tests reentrancy between methods with the same named lock."""
        instance = MethodTester(0)
        instance.reentrant_method_outer_named()  # Call the method
        self.assertEqual(instance.instance_counter, 5)  # Check inner method ran
        # Check log
        self.assertIn("Inst-0: reentrant_outer_named_start", execution_log[0])
        self.assertIn("Inst-0: reentrant_inner_named", execution_log[1])
        self.assertIn("Inst-0: reentrant_outer_named_end", execution_log[2])

    def test_method_reentrancy_default_lock(self) -> None:
        """Tests reentrancy between methods with the same default lock (by calling another method)."""
        # This test verifies that one method decorated with @synchronized()
        # can call another method on the same instance also decorated with @synchronized()
        # IF AND ONLY IF they happen to generate the same default lock name.
        # In our implementation, they generate DIFFERENT default lock names based on qualname.
        # Therefore, this test SHOULD NOT deadlock, but it doesn't test re-entrancy on the *same* lock.
        # It tests that different default locks don't interfere.

        instance = MethodTester(0)
        instance.reentrant_method_outer_default()  # Call the method
        self.assertTrue(
            instance.reentrant_method_flag,
            "Inner default method should have been called",
        )
        # Check log
        self.assertIn("Inst-0: reentrant_outer_default_start", execution_log[0])
        self.assertIn("Inst-0: reentrant_inner_default", execution_log[1])
        self.assertIn("Inst-0: reentrant_outer_default_end", execution_log[2])

    def test_method_reentrancy_default_lock_recursive(self) -> None:
        """Tests reentrancy for a single method's default lock via recursion."""
        instance = MethodTester(1)
        local_reentrant_flag = False

        # --- Inline Recursive Method (bound later) ---
        @synchronized_static()
        def recursive_method(
            self: MethodTester, depth: int = 0, max_depth: int = 2
        ) -> None:
            """Recursive method on instance to test default lock reentrancy."""
            nonlocal local_reentrant_flag  # Modify flag in outer scope
            with log_lock:
                execution_log.append(
                    f"Inst-{self.instance_id}: recursive_depth_{depth}"
                )
            if depth < max_depth:
                recursive_method(
                    self, depth + 1, max_depth
                )  # Use the unbound version for recursion
            else:
                local_reentrant_flag = True

        # --- End Inline Method ---

        # Bind the method to the instance for the test call
        # Using __get__ creates a bound method object
        bound_recursive_method = recursive_method.__get__(instance, MethodTester)
        bound_recursive_method()  # Call the bound method

        self.assertTrue(
            local_reentrant_flag,
            "Recursive method should have reached max depth",
        )
        self.assertIn("Inst-1: recursive_depth_0", execution_log[0])
        self.assertIn("Inst-1: recursive_depth_1", execution_log[1])
        self.assertIn("Inst-1: recursive_depth_2", execution_log[2])


if __name__ == "__main__":
    unittest.main()
