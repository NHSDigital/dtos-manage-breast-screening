# FIXME: Update this info
BSO_CONTACT_DATA = {
    "MBD": {
        "email": "swb-tr.cswbreastscreening@nhs.net",
        "phone": "0121 507 4967",
    }
}


class BsoContactData:
    def __init__(self, clinic):
        self.clinic = clinic
        self.email = BSO_CONTACT_DATA.get(clinic.bso_code, {}).get("email", "")
        self.phone = BSO_CONTACT_DATA.get(clinic.bso_code, {}).get("phone", "")
