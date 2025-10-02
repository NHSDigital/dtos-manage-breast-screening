import os

from manage_breast_screening.notifications.models import (
    AppointmentEpisodeTypeChoices as EpisodeTypes,
)


class RoutingPlan:
    # NHS Notify supports integration and production configurations
    # so we only need to support 2 different routing plan sets.
    # FIX ME: These are not the real production IDs
    PLANS = {
        "dev": (
            (
                "b838b13c-f98c-4def-93f0-515d4e4f4ee1",
                [
                    EpisodeTypes.ROUTINE_FIRST_CALL.value,
                    EpisodeTypes.GP_REFERRAL.value,
                    EpisodeTypes.SELF_REFERRAL.value,
                ],
            ),
            (
                "b838b13c-f98c-4def-93f0-515d4e4f4ee1",
                [EpisodeTypes.ROUTINE_RECALL.value],
            ),
        ),
        "prod": (
            (
                "e82809da-0e58-4915-9774-cc781332d893",
                [
                    EpisodeTypes.ROUTINE_FIRST_CALL.value,
                    EpisodeTypes.GP_REFERRAL.value,
                    EpisodeTypes.SELF_REFERRAL.value,
                ],
            ),
            (
                "c578e0a3-fed4-4faf-981b-ebdef16012f0",
                [EpisodeTypes.ROUTINE_RECALL.value],
            ),
        ),
    }

    def __init__(self, id: str, episode_types: list[str]):
        self.id = id
        self.episode_types = episode_types

    @classmethod
    def all(cls):
        data = cls.PLANS.get(os.getenv("DJANGO_ENV", "dev"), cls.PLANS["dev"])
        return [RoutingPlan(*d) for d in data]

    @classmethod
    def for_episode_type(cls, episode_type: str):
        plans = cls.all()
        for plan in plans:
            if episode_type in plan.episode_types:
                return plan
