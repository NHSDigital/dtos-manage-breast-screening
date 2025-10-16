import os


class Helper:
    @staticmethod
    def sql(filename: str) -> str:
        filepath = os.path.dirname(os.path.realpath(__file__)) + "/" + filename + ".sql"

        return open(filepath).read()
