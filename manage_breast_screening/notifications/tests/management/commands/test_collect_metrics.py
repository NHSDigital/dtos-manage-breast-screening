from manage_breast_screening.notifications.management.commands.collect_metrics import (
    Command,
)


class TestCollectMetrics:
    def test_handle(self):
        Command().handle()
