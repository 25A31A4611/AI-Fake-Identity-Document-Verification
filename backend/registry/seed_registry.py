from backend.registry.database import (
    initialize_database
)

from backend.registry.document_registry import (
    register_document
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# SAMPLE AUTHORIZED REGISTRY RECORDS
# ============================================================
#
# These are synthetic records for prototype testing.
# They are NOT real government records.
#
# Replace/add records later using your authorized dataset
# or your own test database.
# ============================================================


records = [

    {
        "document_type": "passport",

        "document_number": "P1234567",

        "full_name": "RAHUL KUMAR",

        "date_of_birth": "15/08/1998",

        "gender": "MALE",

        "nationality": "INDIAN",

        "issue_date": "10/01/2024",

        "expiry_date": "09/01/2034",

        "address": "Hyderabad, India",

        "status": "ACTIVE"
    },

    {
        "document_type": "aadhaar",

        "document_number": "123456789012",

        "full_name": "PRIYA SHARMA",

        "date_of_birth": "21/04/2001",

        "gender": "FEMALE",

        "nationality": "INDIAN",

        "issue_date": None,

        "expiry_date": None,

        "address": "Hyderabad, India",

        "status": "ACTIVE"
    },

    {
        "document_type": "passport",

        "document_number": "P7654321",

        "full_name": "ARJUN REDDY",

        "date_of_birth": "12/11/1995",

        "gender": "MALE",

        "nationality": "INDIAN",

        "issue_date": "20/05/2020",

        "expiry_date": "19/05/2030",

        "address": "Vijayawada, India",

        "status": "ACTIVE"
    },

    {
        "document_type": "passport",

        "document_number": "P9999999",

        "full_name": "BLOCKED USER",

        "date_of_birth": "01/01/1990",

        "gender": "MALE",

        "nationality": "INDIAN",

        "issue_date": "01/01/2020",

        "expiry_date": "31/12/2030",

        "address": "India",

        "status": "BLOCKED"
    }

]


# ============================================================
# INSERT RECORDS
# ============================================================

for record in records:

    result = register_document(

        document_type=
            record["document_type"],

        document_number=
            record["document_number"],

        full_name=
            record["full_name"],

        date_of_birth=
            record["date_of_birth"],

        gender=
            record["gender"],

        nationality=
            record["nationality"],

        issue_date=
            record["issue_date"],

        expiry_date=
            record["expiry_date"],

        address=
            record["address"],

        status=
            record["status"],

        source="PROTOTYPE_TEST_REGISTRY"
    )

    print(
        result["message"]
    )


print(
    "\nRegistry seed completed."
)