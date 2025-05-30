from time import sleep
from typing import Any
from unittest.mock import patch, MagicMock, call

from baseTest import BaseTestCase
from jstreams.scheduler import (
    Duration,
    schedule_duration,
    schedule_periodic,
    scheduler,
)
from jstreams.utils import Value


class TestScheduler(BaseTestCase):
    def test_scheduler(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)
        global run_times
        run_times = 0

        class RunTest:
            @staticmethod
            @schedule_periodic(2)
            def run_every_2_seconds() -> None:
                global run_times
                run_times += 1

        sleep(5)
        scheduler().stop()
        self.assertGreaterEqual(
            run_times, 2, "The job should have run at least 2 times"
        )

    def test_scheduler_callback(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)
        global run_times
        run_times = 0

        def run_callback(param: Any) -> None:
            global run_times
            run_times += 1

        class RunTest:
            @staticmethod
            @schedule_periodic(2, on_success=run_callback)
            def run_every_2_seconds() -> None:
                pass

        sleep(5)
        scheduler().stop()
        self.assertGreaterEqual(
            run_times, 2, "The job should have run at least 2 times"
        )

    def test_scheduler_callback_value(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)

        val = Value(0)

        class RunTest:
            @staticmethod
            @schedule_periodic(period=1, one_time=True, on_success=val.set)
            def run_every_2_seconds() -> int:
                return 10

        sleep(5)
        scheduler().stop()
        self.assertEqual(
            val.get(), 10, "The callback should have been called with the return value"
        )

    def test_scheduler_callback_error(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)

        val = Value(0)
        err = Value(None)

        class RunTest:
            @staticmethod
            @schedule_periodic(
                period=1, one_time=True, on_success=val.set, on_error=err.set
            )
            def run_every_2_seconds() -> int:
                raise Exception("Test exception")

        sleep(5)
        scheduler().stop()
        self.assertEqual(
            val.get(),
            0,
            "The callback should not have been called with the return value",
        )
        self.assertIsInstance(err.get(), Exception)
        self.assertEqual(
            str(err.get()),
            "Test exception",
            "The callback should have been called with the exception",
        )


class TestDuration(BaseTestCase):
    def test_initialization_and_normalization(self):
        d = Duration(days=1, hours=25, minutes=70)
        self.assertEqual(d._days, 2)  # 1 + 1 (from 25 hours)
        self.assertEqual(d._hours, 2)  # 25 % 24 = 1 + 1 (from 70 minutes)
        self.assertEqual(d._minutes, 10)  # 70 % 60

        d_neg_placeholder = Duration(
            days=0, hours=0, minutes=0
        )  # Values are positive after normalize
        self.assertEqual(d_neg_placeholder._days, 0)

    def test_to_seconds(self):
        self.assertEqual(Duration(minutes=1).to_seconds(), 60)
        self.assertEqual(Duration(hours=1).to_seconds(), 3600)
        self.assertEqual(Duration(days=1).to_seconds(), 86400)
        self.assertEqual(
            Duration(days=1, hours=1, minutes=1).to_seconds(), 86400 + 3600 + 60
        )

    def test_add_duration(self):
        d1 = Duration(hours=1, minutes=30)
        d2 = Duration(hours=2, minutes=40)  # 2h 40m
        d_sum = d1 + d2  # 1h30m + 2h40m = 3h70m = 4h10m
        self.assertEqual(d_sum._days, 0)
        self.assertEqual(d_sum._hours, 4)
        self.assertEqual(d_sum._minutes, 10)

    def test_add_invalid_type(self):
        d1 = Duration(hours=1)
        self.assertRaises(TypeError, lambda: d1 + 5)

    def test_subtract_duration(self):
        d1 = Duration(hours=3, minutes=30)  # 3.5 hours
        d2 = Duration(hours=1, minutes=10)  # 1h 10m
        d_diff = d1 - d2  # 3h30m - 1h10m = 2h20m
        self.assertEqual(d_diff._days, 0)
        self.assertEqual(d_diff._hours, 2)
        self.assertEqual(d_diff._minutes, 20)

        # Test absolute difference
        d_diff_abs = d2 - d1
        self.assertEqual(d_diff_abs._days, 0)
        self.assertEqual(d_diff_abs._hours, 2)
        self.assertEqual(d_diff_abs._minutes, 20)

        d3 = Duration(minutes=50)
        d4 = Duration(hours=1, minutes=10)  # 70 minutes
        d_diff2 = d3 - d4  # 50m - 70m = abs(-20m) = 20m
        self.assertEqual(d_diff2._minutes, 20)
        self.assertEqual(d_diff2._hours, 0)

    def test_subtract_invalid_type(self):
        d1 = Duration(hours=1)
        with self.assertRaisesRegex(
            TypeError, "Unsupported operand type for -: 'Duration' and 'str'"
        ):
            _ = d1 - "test"

    @patch("importlib.import_module")
    def test_scan_modules_success(self, mock_import_module):
        s = scheduler()
        s.scan_modules(["module1", "module2"])
        mock_import_module.assert_has_calls([call("module1"), call("module2")])

    def test_schedule_periodic(self):
        s = scheduler()
        s.enforce_minimum_period(False)
        mock_f = MagicMock(__name__="mock_f")
        mock_on_success = MagicMock()
        mock_on_error = MagicMock()

        s.schedule_periodic(
            mock_f, 1, on_success=mock_on_success, on_error=mock_on_error
        )
        self.assertEqual(len(s._Scheduler__jobs), 1)
        job = s._Scheduler__jobs[0]
        self.assertEqual(job.name, "mock_f")
        self.assertEqual(job.period, 1)
        self.assertFalse(job.run_once)
        self.assertEqual(job.on_success, mock_on_success)
        self.assertEqual(job.on_error, mock_on_error)
        s.stop()

    def test_schedule_periodic_one_time(self):
        s = scheduler()
        mock_f = MagicMock(__name__="mock_f_once")
        s.schedule_periodic(mock_f, 1, one_time=True)
        self.assertEqual(len(s._Scheduler__jobs), 1)
        job = s._Scheduler__jobs[0]
        s.stop()
        self.assertTrue(job.run_once)

    def test_schedule_periodic_enforcement_error(self):
        s = scheduler()
        s.enforce_minimum_period(True)  # Default, but explicit
        mock_f = MagicMock(__name__="mock_f_short")
        with self.assertRaisesRegex(
            ValueError, "Period must be greater than 10 seconds"
        ):
            s.schedule_periodic(mock_f, 5)  # Period is 5s, one_time is False

        # Should not raise if one_time is True
        s.schedule_periodic(mock_f, 5, one_time=True)
        self.assertEqual(len(s._Scheduler__jobs), 1)

        # Should not raise if enforcement is off
        s.enforce_minimum_period(False)
        s.schedule_periodic(mock_f, 5)
        self.assertEqual(len(s._Scheduler__jobs), 2)

    def test_schedule_duration(self):
        s = scheduler()
        mock_f = MagicMock(__name__="duration_f")
        mock_on_success = MagicMock()
        mock_on_error = MagicMock()
        duration = Duration(minutes=15)  # 900 seconds

        with patch.object(
            s, "schedule_periodic", wraps=s.schedule_periodic
        ) as mock_schedule_periodic:
            s.schedule_duration(
                mock_f, duration, on_success=mock_on_success, on_error=mock_on_error
            )
            mock_schedule_periodic.assert_called_once_with(
                mock_f,
                duration.to_seconds(),
                on_success=mock_on_success,
                on_error=mock_on_error,
            )
        self.assertEqual(len(s._Scheduler__jobs), 1)
        job = s._Scheduler__jobs[0]
        self.assertEqual(job.period, 900)


class TestSchedulerHelperFunctions(BaseTestCase):
    def test_scheduler_function(self):
        s1 = scheduler()
        s2 = scheduler()
        self.assertIs(s1, s2)

    def test_decorator_schedule_periodic(self):
        mock_on_s = MagicMock()
        mock_on_e = MagicMock()

        @schedule_periodic(120, one_time=True, on_success=mock_on_s, on_error=mock_on_e)
        def decorated_func_periodic():
            return "periodic_result"

        s = scheduler()
        self.assertEqual(len(s._Scheduler__jobs), 1)
        job = s._Scheduler__jobs[0]
        self.assertEqual(job.name, "decorated_func_periodic")
        self.assertEqual(job.period, 120)
        self.assertTrue(job.run_once)
        self.assertEqual(job.on_success, mock_on_s)
        self.assertEqual(job.on_error, mock_on_e)
        self.assertIs(job.func, decorated_func_periodic)

    def test_decorator_schedule_duration(self):
        d = Duration(hours=1)  # 3600 seconds
        mock_on_s = MagicMock()
        mock_on_e = MagicMock()

        @schedule_duration(d, on_success=mock_on_s, on_error=mock_on_e)
        def decorated_func_duration():
            return "duration_result"

        s = scheduler()
        self.assertEqual(len(s._Scheduler__jobs), 1)
        job = s._Scheduler__jobs[0]
        self.assertEqual(job.name, "decorated_func_duration")
        self.assertEqual(job.period, 3600)
        self.assertEqual(job.on_success, mock_on_s)
        self.assertEqual(job.on_error, mock_on_e)

    def test_duration_zero(self):
        d = Duration()
        self.assertEqual(d.to_seconds(), 0)
        self.assertEqual(d._days, 0)
        self.assertEqual(d._hours, 0)
        self.assertEqual(d._minutes, 0)
