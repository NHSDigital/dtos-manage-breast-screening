import os


class AggregateQuery:
    COLUMNS = [
        "Appointment date",
        "BSO code",
        "Clinic code",
        "Clinic name",
        "Episode type",
        "Notifications sent",
        "NHS app messages read",
        "SMS messages delivered",
        "Letters sent",
        "Notifications failed",
    ]

    @staticmethod
    def sql() -> str:
        sql_file_path = f"{os.path.dirname(os.path.realpath(__file__))}/aggregate.sql"
        return str(open(sql_file_path).read())

    @classmethod
    def columns(cls) -> list:
        return cls.COLUMNS
