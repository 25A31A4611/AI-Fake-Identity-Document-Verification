# ==================================================
# DEMO REFERENCE DATABASE
# ==================================================

DEMO_DATABASE = {

    "548732219877": {
        "name": "GUNNAM DHARISHRI",
        "date_of_birth": "25-08-2007",
        "gender": "FEMALE"
    },

    "DEMO-123456": {
        "name": "DEMO USER",
        "date_of_birth": "01-01-2000",
        "gender": "F"
    },

    "DEMO-654321": {
        "name": "SAMPLE USER",
        "date_of_birth": "15-08-1999",
        "gender": "M"
    }

}


def normalize_name(name):

    if not name:
        return ""

    name = str(name).upper().strip()

    # Remove punctuation
    name = name.replace(".", " ")
    name = name.replace(",", " ")

    # Remove extra spaces
    name = " ".join(name.split())

    return name


def check_reference_database(fields):
    """
    Compare extracted National ID information
    with the synthetic demo reference database.

    Prototype only.
    No real government database is used.
    """

    # ==================================================
    # GET ID NUMBER
    # ==================================================

    id_number = fields.get(
        "id_number",
        "Not detected"
    )

    if id_number == "Not detected":

        return {
            "status": "REVIEW",
            "message": "ID number was not detected.",
            "match": False
        }

    # ==================================================
    # NORMALIZE ID NUMBER
    # ==================================================

    normalized_id = (
        str(id_number)
        .replace(" ", "")
        .replace("-", "")
        .upper()
    )

    # ==================================================
    # FIND SYNTHETIC RECORD
    # ==================================================

    record = None

    for database_id, database_record in DEMO_DATABASE.items():

        normalized_database_id = (
            database_id
            .replace(" ", "")
            .replace("-", "")
            .upper()
        )

        if normalized_id == normalized_database_id:

            record = database_record
            break

    # ==================================================
    # RECORD NOT FOUND
    # ==================================================

    if record is None:

        return {
            "status": "REVIEW",
            "message": (
                "No matching synthetic demo "
                "record found."
            ),
            "match": False
        }

    # ==================================================
    # FIELD COMPARISON
    # ==================================================

    extracted_name = normalize_name(
        fields.get("name", "")
    )

    database_name = normalize_name(
        record.get("name", "")
    )

    extracted_dob = (
        fields.get(
            "date_of_birth",
            ""
        )
        .strip()
    )

    database_dob = (
        record.get(
            "date_of_birth",
            ""
        )
        .strip()
    )

    extracted_gender = (
        fields.get(
            "gender",
            ""
        )
        .strip()
        .upper()
    )

    database_gender = (
        record.get(
            "gender",
            ""
        )
        .strip()
        .upper()
    )

    # ==================================================
    # MATCH CHECKS
    # ==================================================

    name_match = (
        extracted_name == database_name
    )

    dob_match = (
        extracted_dob == database_dob
    )

    gender_match = (
        extracted_gender == database_gender
    )

    # ==================================================
    # FINAL MATCH
    # ==================================================

    if (
        name_match
        and dob_match
        and gender_match
    ):

        return {
            "status": "PASS",
            "message": (
                "Synthetic reference record matched "
                "for name, date of birth and gender."
            ),
            "match": True
        }

    # ==================================================
    # PARTIAL MATCH
    # ==================================================

    mismatches = []

    if not name_match:
        mismatches.append("Name")

    if not dob_match:
        mismatches.append("Date of Birth")

    if not gender_match:
        mismatches.append("Gender")

    return {
        "status": "REVIEW",
        "message": (
            "Reference record found, but "
            + ", ".join(mismatches)
            + " does not match."
        ),
        "match": False
    }