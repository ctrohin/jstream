from jstreams.scheduler import schedule_periodic

global two_seconds_counter
two_seconds_counter = 0

global two_seconds_class_counter
two_seconds_class_counter = 0


@schedule_periodic(2)
def run_at_two_seconds() -> None:
    global two_seconds_counter
    two_seconds_counter += 1


class SchedulerStaticClass:
    @staticmethod
    @schedule_periodic(2)
    def run_at_two_seconds() -> None:
        global two_seconds_class_counter
        two_seconds_class_counter += 1
