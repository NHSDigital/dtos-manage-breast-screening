import os

from django.db import connection


class Helper:
    @staticmethod
    def sql(filename: str) -> str:
        filepath = os.path.dirname(os.path.realpath(__file__)) + "/" + filename + ".sql"

        return open(filepath).read()

    @staticmethod
    def fetchall(report_name, *args):
        results = []

        with connection.cursor() as cursor:
            cursor.execute(Helper.sql(report_name), *args)
            results = cursor.fetchall()

        return results
