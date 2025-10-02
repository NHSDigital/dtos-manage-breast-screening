import os


class FailuresQuery:
    COLUMNS = [
        "NHS number",
        "Appointment date",
        "Clinic code",
        "Episode type",
        "Failure date",
        "Failure reason",
    ]

    @staticmethod
    def sql() -> str:
        sql_file_path = f"{os.path.dirname(os.path.realpath(__file__))}/failures.sql"
        return str(open(sql_file_path).read())

    @classmethod
    def columns(cls) -> list:
        return cls.COLUMNS
