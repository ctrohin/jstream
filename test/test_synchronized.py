import unittest
import threading
import time
from typing import List, Any, Callable

# Assuming the synchronized decorator is in 'jstreams.annotations'
# Adjust the import path if necessary
from jstreams.annotations import synchronized, DEFAULT_INSTANCE_LOCK_ATTR

# --- Test State ---
execution_log: List[str] = []
log_lock = threading.Lock()


# --- Test Class with Decorated Methods ---
class InstanceTester:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self._reentrant_flag = False
        self._counter = 0
        # Locks are created lazily by the decorator

    @synchronized()  # Uses default lock attribute
    def method_default_lock(self, thread_name: str, delay: float = 0.05) -> None:
        """Method protected by the default instance lock."""
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] default_start")
        time.sleep(delay)
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] default_end")

    @synchronized("_lock_A")  # Uses named lock attribute "_lock_A"
    def method_named_lock_A(self, thread_name: str, delay: float = 0.05) -> None:
        """Method protected by instance lock A."""
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] lock_A_start")
        time.sleep(delay)
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] lock_A_end")

    @synchronized("_lock_A")  # Uses named lock attribute "_lock_A"
    def another_method_named_lock_A(
        self, thread_name: str, delay: float = 0.05
    ) -> None:
        """Another method protected by instance lock A."""
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] another_lock_A_start"
            )
        time.sleep(delay)
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] another_lock_A_end"
            )

    @synchronized("_lock_B")  # Uses named lock attribute "_lock_B"
    def method_named_lock_B(self, thread_name: str, delay: float = 0.05) -> None:
        """Method protected by instance lock B."""
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] lock_B_start")
        time.sleep(delay)
        with log_lock:
            execution_log.append(f"{thread_name}: [{self.instance_id}] lock_B_end")

    # --- Reentrancy Methods ---
    @synchronized()  # Default lock
    def reentrant_outer_default(self, thread_name: str) -> None:
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_outer_default_start"
            )
        self.reentrant_inner_default(thread_name)  # Call method with same default lock
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_outer_default_end"
            )

    @synchronized()  # Default lock
    def reentrant_inner_default(self, thread_name: str) -> None:
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_inner_default"
            )
        self._reentrant_flag = True

    @synchronized("_lock_A")  # Named lock A
    def reentrant_outer_named(self, thread_name: str) -> None:
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_outer_named_start"
            )
        self.reentrant_inner_named(thread_name)  # Call method with same named lock
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_outer_named_end"
            )

    @synchronized("_lock_A")  # Named lock A
    def reentrant_inner_named(self, thread_name: str) -> None:
        with log_lock:
            execution_log.append(
                f"{thread_name}: [{self.instance_id}] reentrant_inner_named"
            )
        self._reentrant_flag = True

    # --- Basic Functionality Methods ---
    @synchronized()
    def return_value_method(self, value: Any) -> Any:
        return value

    @synchronized()
    def exception_method(self, message: str) -> None:
        raise ValueError(message)


# --- Standalone function for error testing ---
@synchronized()
def standalone_function(arg: int) -> None:
    # This should fail when called because 'self' is missing
    pass


# --- Test Suite ---
class TestInstanceSynchronized(unittest.TestCase):
    def setUp(self) -> None:
        """Reset shared state before each test."""
        global execution_log
        execution_log = []
        # No global registry to clear for synchronized

    def run_threads(
        self, targets_with_args: List[tuple[Callable[..., Any], tuple]]
    ) -> None:
        """Helper to create, start, and join threads for specific targets/args."""
        threads: List[threading.Thread] = []
        for i, (target, args) in enumerate(targets_with_args):
            # Pass thread name as first arg for logging within the method
            full_args = (f"Thread-{i}",) + args
            thread = threading.Thread(target=target, args=full_args, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def assert_concurrent(
        self,
        start_time: float,
        end_time: float,
        min_expected_duration: float,
        message: str,
    ) -> None:
        """Asserts that execution time indicates concurrency."""
        # Allow some overhead, but should be significantly less than serial execution
        self.assertLess(end_time - start_time, min_expected_duration * 1.9, message)

    def assert_serialized(
        self,
        start_time: float,
        end_time: float,
        min_expected_duration: float,
        message: str,
    ) -> None:
        """Asserts that execution time indicates serialization."""
        # Should be close to or greater than the sum of delays
        self.assertGreaterEqual(
            end_time - start_time, min_expected_duration * 0.95, message
        )  # Allow slight timing variations

    # --- Core Functionality Tests ---

    def test_serialization_same_instance_default_lock(self) -> None:
        """Verify calls to same method on same instance are serialized (default lock)."""
        instance = InstanceTester("inst-1")
        delay = 0.05
        start_time = time.time()
        self.run_threads(
            [
                (instance.method_default_lock, (delay,)),
                (instance.method_default_lock, (delay,)),
            ]
        )
        end_time = time.time()
        self.assert_serialized(
            start_time,
            end_time,
            delay * 2,
            "Calls on same instance (default lock) should be serialized",
        )
        # Optional: Check log order for strict sequence

    def test_concurrency_different_instances_default_lock(self) -> None:
        """Verify calls to same method on different instances run concurrently (default lock)."""
        instance1 = InstanceTester("inst-1")
        instance2 = InstanceTester("inst-2")
        delay = 0.1
        start_time = time.time()
        self.run_threads(
            [
                (instance1.method_default_lock, (delay,)),
                (instance2.method_default_lock, (delay,)),
            ]
        )
        end_time = time.time()
        self.assert_concurrent(
            start_time,
            end_time,
            delay,
            "Calls on different instances (default lock) should be concurrent",
        )
        # Optional: Check log for interleaving

    def test_serialization_same_instance_named_lock(self) -> None:
        """Verify calls to different methods using same named lock on same instance are serialized."""
        instance = InstanceTester("inst-1")
        delay = 0.05
        start_time = time.time()
        self.run_threads(
            [
                (instance.method_named_lock_A, (delay,)),
                (instance.another_method_named_lock_A, (delay,)),
            ]
        )
        end_time = time.time()
        self.assert_serialized(
            start_time,
            end_time,
            delay * 2,
            "Calls on same instance (named lock A) should be serialized",
        )

    def test_concurrency_different_instances_named_lock(self) -> None:
        """Verify calls to same method on different instances run concurrently (named lock)."""
        instance1 = InstanceTester("inst-1")
        instance2 = InstanceTester("inst-2")
        delay = 0.1
        start_time = time.time()
        self.run_threads(
            [
                (instance1.method_named_lock_A, (delay,)),
                (instance2.method_named_lock_A, (delay,)),
            ]
        )
        end_time = time.time()
        self.assert_concurrent(
            start_time,
            end_time,
            delay,
            "Calls on different instances (named lock A) should be concurrent",
        )

    def test_concurrency_different_locks_same_instance(self) -> None:
        """Verify calls to methods using different locks on same instance run concurrently."""
        instance = InstanceTester("inst-1")
        delay = 0.1
        start_time = time.time()
        self.run_threads(
            [
                (instance.method_default_lock, (delay,)),  # Default lock
                (instance.method_named_lock_A, (delay,)),  # Lock A
                (instance.method_named_lock_B, (delay,)),  # Lock B
            ]
        )
        end_time = time.time()
        # If concurrent, time should be closer to max delay, not sum
        self.assert_concurrent(
            start_time,
            end_time,
            delay,
            "Calls with different locks on same instance should be concurrent",
        )

    # --- Reentrancy Tests ---

    def test_reentrancy_default_lock(self) -> None:
        """Verify reentrancy for the default instance lock."""
        instance = InstanceTester("inst-1")
        instance.reentrant_outer_default("MainThread")
        self.assertTrue(
            instance._reentrant_flag, "Inner default method should have been called"
        )
        # Check log order
        self.assertIn("reentrant_outer_default_start", execution_log[0])
        self.assertIn("reentrant_inner_default", execution_log[1])
        self.assertIn("reentrant_outer_default_end", execution_log[2])

    def test_reentrancy_named_lock(self) -> None:
        """Verify reentrancy for a named instance lock."""
        instance = InstanceTester("inst-1")
        instance.reentrant_outer_named("MainThread")
        self.assertTrue(
            instance._reentrant_flag, "Inner named method should have been called"
        )
        # Check log order
        self.assertIn("reentrant_outer_named_start", execution_log[0])
        self.assertIn("reentrant_inner_named", execution_log[1])
        self.assertIn("reentrant_outer_named_end", execution_log[2])

    # --- Basic Decorator Functionality ---

    def test_return_value(self) -> None:
        """Verify the decorator preserves the method's return value."""
        instance = InstanceTester("inst-1")
        expected = "test_return"
        self.assertEqual(instance.return_value_method(expected), expected)

    def test_exception_propagation(self) -> None:
        """Verify exceptions from the original method are propagated."""
        instance = InstanceTester("inst-1")
        error_message = "Test Exception"
        with self.assertRaisesRegex(ValueError, error_message):
            instance.exception_method(error_message)

    def test_lock_attribute_creation(self) -> None:
        """Verify lock attributes are created on the instance."""
        instance = InstanceTester("inst-1")
        # Call methods to trigger lock creation
        instance.method_default_lock("MainThread", 0)
        instance.method_named_lock_A("MainThread", 0)
        instance.method_named_lock_B("MainThread", 0)

        self.assertTrue(hasattr(instance, DEFAULT_INSTANCE_LOCK_ATTR))
        self.assertIn("RLock", str(type(getattr(instance, DEFAULT_INSTANCE_LOCK_ATTR))))

        self.assertTrue(hasattr(instance, "_lock_A"))
        self.assertIn("RLock", str(type(getattr(instance, "_lock_A"))))

        self.assertTrue(hasattr(instance, "_lock_B"))
        self.assertIn("RLock", str(type(getattr(instance, "_lock_B"))))

        # Check locks are distinct
        self.assertIsNot(
            getattr(instance, DEFAULT_INSTANCE_LOCK_ATTR), getattr(instance, "_lock_A")
        )
        self.assertIsNot(getattr(instance, "_lock_A"), getattr(instance, "_lock_B"))

    # --- Error Cases ---

    def test_raises_on_non_method(self) -> None:
        """Verify TypeError is raised if applied to a non-method function."""
        with self.assertRaisesRegex(
            TypeError,
            "Could not set lock attribute '_default_instance_sync_lock' on instance of int. Does the class use __slots__ without including '_default_instance_sync_lock'?",
        ):
            standalone_function(
                123
            )  # Calling the decorated function triggers the check


if __name__ == "__main__":
    unittest.main()
