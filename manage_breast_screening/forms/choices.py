from django.db.models import TextChoices


class YesNo(TextChoices):
    YES = ("YES", "Yes")
    NO = ("NO", "No")
