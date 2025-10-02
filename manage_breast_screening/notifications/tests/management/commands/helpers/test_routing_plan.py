import pytest

from manage_breast_screening.notifications.management.commands.helpers.routing_plan import (
    RoutingPlan,
)


class TestRoutingPlan:
    @pytest.mark.parametrize("django_env", ["dev", "prod"])
    def test_routing_plans_for_known_environments(self, django_env, monkeypatch):
        monkeypatch.setenv("DJANGO_ENV", django_env)

        plans = RoutingPlan.all()

        for idx, data in enumerate(RoutingPlan.PLANS[django_env]):
            assert plans[idx].id == data[0]
            assert plans[idx].episode_types == data[1]

    @pytest.mark.parametrize("django_env", [None, "nft", "nope"])
    def test_routing_plans_default_to_dev(self, django_env, monkeypatch):
        monkeypatch.setenv("DJANGO_ENV", django_env)

        plans = RoutingPlan.all()

        assert plans[0].id == RoutingPlan.PLANS["dev"][0][0]
        assert plans[1].id == RoutingPlan.PLANS["dev"][1][0]

    def test_routing_plan_episode_types(self):
        plans = RoutingPlan.all()

        assert plans[0].episode_types == ["F", "G", "S"]
        assert plans[1].episode_types == ["R"]

    @pytest.mark.parametrize("episode_type", ["F", "G", "R", "S"])
    def test_routing_plan_for_episode_type(self, episode_type):
        plan = RoutingPlan.for_episode_type(episode_type)

        assert episode_type in plan.episode_types
