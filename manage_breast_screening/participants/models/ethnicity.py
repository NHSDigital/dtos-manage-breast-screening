class Ethnicity:
    """
    This class contains structured ethnicity data along with methods for retrieval and querying of
    the dataset.

    List of ethnic groups from
    https://design-system.service.gov.uk/patterns/equality-information/
    This list is specific to England.

    The ids are stored in the database and should not be changed without an accompanying data
    migration.
    """

    PREFER_NOT_TO_SAY = "prefer_not_to_say"

    # fmt: off
    DATA = {
        "White": [
            { "id": "english_welsh_scottish_ni_british", "display_name": "English, Welsh, Scottish, Northern Irish or British", },
            { "id": "irish", "display_name": "Irish" },
            { "id": "gypsy_or_irish_traveller", "display_name": "Gypsy or Irish Traveller" },
            { "id": "any_other_white_background", "display_name": "Any other White background" },
        ],
        "Mixed or multiple ethnic groups": [
            { "id": "white_and_black_caribbean", "display_name": "White and Black Caribbean" },
            { "id": "white_and_black_african", "display_name": "White and Black African" },
            { "id": "white_and_asian", "display_name": "White and Asian" },
            { "id": "any_other_mixed_or_multiple_ethnic_background", "display_name": "Any other mixed or multiple ethnic background" },
        ],
        "Asian or Asian British": [
            { "id": "indian", "display_name": "Indian" },
            { "id": "pakistani", "display_name": "Pakistani" },
            { "id": "bangladeshi", "display_name": "Bangladeshi" },
            { "id": "chinese", "display_name": "Chinese" },
            { "id": "any_other_asian_background", "display_name": "Any other Asian background" },
        ],
        "Black, African, Caribbean or Black British": [
            { "id": "african", "display_name": "African" },
            { "id": "caribbean", "display_name": "Caribbean" },
            { "id": "any_other_black_african_or_caribbean_background", "display_name": "Any other Black, African or Caribbean background" },
        ],
        "Other ethnic group": [
            { "id": "arab", "display_name": "Arab" },
            { "id": "any_other_ethnic_background", "display_name": "Any other ethnic group" },
            { "id": "prefer_not_to_say", "display_name": "Prefer not to say" },
        ],
    }
    # fmt: on

    @staticmethod
    def non_specific_ethnic_backgrounds():
        return [
            "any_other_white_background",
            "any_other_mixed_or_multiple_ethnic_background",
            "any_other_asian_background",
            "any_other_black_african_or_caribbean_background",
            "any_other_ethnic_background",
        ]

    @classmethod
    def ethnic_background_ids_with_display_names(cls):
        """
        Returns a list of tuples containing the id and display name for each ethnic background.
        """
        choices = []
        for ethnic_backgrounds in cls.DATA.values():
            for background in ethnic_backgrounds:
                choices.append((background["id"], background["display_name"]))
        return tuple(choices)

    @classmethod
    def ethnic_category(cls, ethnic_background_id: str):
        """
        Returns the top-level ethnic category for the given ethnic background id.
        """
        for category, ethnic_backgrounds in cls.DATA.items():
            for background in ethnic_backgrounds:
                if ethnic_background_id == background["id"]:
                    return category
        return None

    @classmethod
    def ethnic_background_display_name(cls, ethnic_background_id: str):
        """
        Returns the display name for the given ethnic background id.
        """
        for _, ethnic_backgrounds in cls.DATA.items():
            for background in ethnic_backgrounds:
                if ethnic_background_id == background["id"]:
                    return background["display_name"]
        return None
