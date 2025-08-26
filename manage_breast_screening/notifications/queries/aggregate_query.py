import os


class AggregateQuery:
    @staticmethod
    def sql() -> str:
        sql_file_path = f"{os.path.dirname(os.path.realpath(__file__))}/aggregate.sql"
        return str(open(sql_file_path).read())
