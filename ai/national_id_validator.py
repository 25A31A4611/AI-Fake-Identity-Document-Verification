import re


def validate_national_id(fields):

    results = []

    # =========================================================
    # NAME
    # =========================================================

    name = fields.get("name", "").strip()

    if name and name != "Not detected":

        results.append({
            "check": "Name",
            "status": "PASS",
            "message": "Name information was detected."
        })

    else:

        results.append({
            "check": "Name",
            "status": "WARNING",
            "message": "Name information was not detected."
        })

    # =========================================================
    # ID NUMBER
    # =========================================================

    id_number = fields.get("id_number", "").strip()

    # Synthetic prototype ID:
    # 12 digit numeric format

    if re.fullmatch(r"\d{12}", id_number):

        results.append({
            "check": "ID Number Format",
            "status": "PASS",
            "message": "Synthetic National ID number format is valid."
        })

    else:

        results.append({
            "check": "ID Number Format",
            "status": "REVIEW",
            "message": "ID number format requires review."
        })

    # =========================================================
    # DATE OF BIRTH
    # =========================================================

    dob = fields.get("date_of_birth", "").strip()

    if re.fullmatch(
        r"\d{2}[-/]\d{2}[-/]\d{4}",
        dob
    ):

        results.append({
            "check": "Date of Birth Format",
            "status": "PASS",
            "message": "Date of birth format appears valid."
        })

    else:

        results.append({
            "check": "Date of Birth Format",
            "status": "WARNING",
            "message": "Date of birth format requires review."
        })

    # =========================================================
    # GENDER
    # =========================================================

    gender = fields.get("gender", "").upper().strip()

    if gender in ["MALE", "FEMALE", "M", "F", "X"]:

        results.append({
            "check": "Gender",
            "status": "PASS",
            "message": "Gender information appears valid."
        })

    else:

        results.append({
            "check": "Gender",
            "status": "WARNING",
            "message": "Gender information requires review."
        })

    # =========================================================
    # OVERALL
    # =========================================================

    has_review = any(
        result["status"] == "REVIEW"
        for result in results
    )

    has_warning = any(
        result["status"] == "WARNING"
        for result in results
    )

    if has_review:

        overall_status = "REVIEW"
        overall_message = (
            "One or more identity fields require additional review."
        )

    elif has_warning:

        overall_status = "WARNING"
        overall_message = (
            "Some identity information requires review."
        )

    else:

        overall_status = "PASS"
        overall_message = (
            "All detected identity fields passed basic prototype validation."
        )

    results.append({
        "check": "Overall Validation",
        "status": overall_status,
        "message": overall_message
    })

    return results