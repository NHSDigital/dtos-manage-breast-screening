CLINIC_LOCATION_DATA = [
    {
        "code": "MDSAL",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS9+8AJ",
    },
    {
        "code": "MDSAT",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B6+6QR",
    },
    {
        "code": "MDSBL",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS3+3JP",
    },
    {
        "code": "MDSBR",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS8+6DZ",
    },
    {
        "code": "MDSCV",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B24+9FP",
    },
    {
        "code": "MDSCH",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B18+7QH",
    },
    {
        "code": "MDSCW",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B64+7HA",
    },
    {
        "code": "MDSDA",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS10+8SY",
    },
    {
        "code": "MDSDD",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B23+5DD",
    },
    {
        "code": "MDSHH",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B36+8DT",
    },
    {
        "code": "MDSMG",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B75+5BT",
    },
    {
        "code": "MDSOL",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B69+4DE",
    },
    {
        "code": "MDSQU",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B43+7HA",
    },
    {
        "code": "MDSSY",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B8+3SG",
    },
    {
        "code": "MDSYG",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B10+0HH",
    },
    {
        "code": "MDSVH",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B66+3PZ",
    },
    {
        "code": "MDSSG",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B23+6DJ",
    },
    {
        "code": "MDSNP",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/DY4+8PX",
    },
    {
        "code": "MDSWA",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS2+9BZ",
    },
    {
        "code": "MDSSH",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/B71+4HJ",
    },
    {
        "code": "MDSWE",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WS10+7BD",
    },
    {
        "code": "MDSWJ",
        "bso_code": "MBD",
        "location_url": "https://www.google.com/maps/search/WV13+1QG",
    },
]


class ClinicLocationData:
    def __init__(self, clinic):
        self.clinic = clinic
        self.code = clinic.code
        self.bso_code = clinic.bso_code
        self.data = self.location_data()
        # Not used, but still part of the Notify template, so fails validation
        # if not present.
        self.description = ""
        self.url = self.data.get("location_url", "")

    def location_data(self) -> dict:
        for data in CLINIC_LOCATION_DATA:
            if self.code == data.get("code") and self.bso_code == data.get("bso_code"):
                return data
        return {}
