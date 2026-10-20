import re


def normalize_text(value):
    """
    Normalizes names and other text so that
    OCR formatting differences do not immediately
    create a false mismatch.
    """

    if value is None:
        return ""

    value = str(value).upper().strip()

    # Remove punctuation
    value = re.sub(r"[^A-Z0-9 ]", " ", value)

    # Remove extra spaces
    value = re.sub(r"\s+", " ", value).strip()

    return value


def normalize_name(value):
    """
    Normalizes names.

    Example:
    GUNNAM DHARISHRI
    DHARISHRI GUNNAM

    are treated as containing the same name parts.
    """

    value = normalize_text(value)

    if not value or value == "NOT DETECTED":
        return ""

    parts = value.split()

    # Remove duplicate parts
    parts = list(dict.fromkeys(parts))

    # Sort name parts so OCR ordering differences
    # don't immediately create a mismatch.
    parts.sort()

    return " ".join(parts)


def normalize_date(value):
    """
    Converts common date formats into a comparable form.
    """

    if value is None:
        return ""

    value = str(value).upper().strip()

    value = re.sub(r"[^A-Z0-9]", "", value)

    # Convert month names to month numbers
    months = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }

    for month, number in months.items():

        if month in value:

            value = value.replace(month, number)

    return value


def normalize_nationality(value):
    """
    Handles common nationality representations.

    Example:

    IND
    INDIA
    INDIAN

    are treated as the same nationality
    for this prototype comparison.
    """

    value = normalize_text(value)

    nationality_map = {
        "IND": "IND",
        "INDIA": "IND",
        "INDIAN": "IND",

        "USA": "USA",
        "UNITED STATES": "USA",
        "AMERICAN": "USA",

        "GBR": "GBR",
        "UK": "GBR",
        "UNITED KINGDOM": "GBR",
        "BRITISH": "GBR",

        "CAN": "CAN",
        "CANADA": "CAN",

        "AUS": "AUS",
        "AUSTRALIA": "AUS"
    }

    return nationality_map.get(value, value)


def normalize_passport_number(value):
    """
    Removes spaces and symbols from passport numbers.
    """

    if value is None:
        return ""

    value = str(value).upper().strip()

    value = re.sub(r"[^A-Z0-9]", "", value)

    return value


def compare_documents(passport_fields, visa_fields):

    results = []

    # ==================================================
    # 1. NAME COMPARISON
    # ==================================================

    passport_name = normalize_name(
        passport_fields.get("name", "")
    )

    visa_name = normalize_name(
        visa_fields.get("name", "")
    )

    if not passport_name or passport_name == "NOTDETECTED":

        results.append({
            "check": "Name Consistency",
            "status": "WARNING",
            "message": "Passport name was not available for comparison."
        })

    elif not visa_name or visa_name == "NOTDETECTED":

        results.append({
            "check": "Name Consistency",
            "status": "WARNING",
            "message": "Visa name was not available for comparison."
        })

    elif passport_name == visa_name:

        results.append({
            "check": "Name Consistency",
            "status": "PASS",
            "message": "Passport and visa names are consistent after OCR normalization."
        })

    else:

        results.append({
            "check": "Name Consistency",
            "status": "REVIEW",
            "message": "Name mismatch detected between documents."
        })


    # ==================================================
    # 2. DATE OF BIRTH COMPARISON
    # ==================================================

    passport_dob = normalize_date(
        passport_fields.get("date_of_birth", "")
    )

    visa_dob = normalize_date(
        visa_fields.get("date_of_birth", "")
    )

    if not passport_dob or passport_dob == "NOTDETECTED":

        results.append({
            "check": "Date of Birth Consistency",
            "status": "WARNING",
            "message": "Passport date of birth was not available."
        })

    elif not visa_dob or visa_dob == "NOTDETECTED":

        results.append({
            "check": "Date of Birth Consistency",
            "status": "WARNING",
            "message": "Visa date of birth was not available."
        })

    elif passport_dob == visa_dob:

        results.append({
            "check": "Date of Birth Consistency",
            "status": "PASS",
            "message": "Date of birth matches across passport and visa."
        })

    else:

        results.append({
            "check": "Date of Birth Consistency",
            "status": "REVIEW",
            "message": "Date of birth mismatch detected between documents."
        })


    # ==================================================
    # 3. PASSPORT NUMBER COMPARISON
    # ==================================================

    passport_number = normalize_passport_number(
        passport_fields.get("passport_number", "")
    )

    visa_reference = normalize_passport_number(
        visa_fields.get("visa_number", "")
    )

    if not passport_number or passport_number == "NOTDETECTED":

        results.append({
            "check": "Passport Number Consistency",
            "status": "WARNING",
            "message": "Passport number was not available from the passport document."
        })

    elif not visa_reference or visa_reference == "NOTDETECTED":

        results.append({
            "check": "Passport Number Consistency",
            "status": "WARNING",
            "message": "Passport reference number was not available from the visa."
        })

    elif passport_number == visa_reference:

        results.append({
            "check": "Passport Number Consistency",
            "status": "PASS",
            "message": "Passport number matches the visa reference number."
        })

    else:

        results.append({
            "check": "Passport Number Consistency",
            "status": "REVIEW",
            "message": "Passport number does not match the visa reference number."
        })


    # ==================================================
    # 4. NATIONALITY COMPARISON
    # ==================================================

    passport_nationality = normalize_nationality(
        passport_fields.get("nationality", "")
    )

    visa_nationality = normalize_nationality(
        visa_fields.get("nationality", "")
    )

    if (
        not passport_nationality
        or passport_nationality == "NOTDETECTED"
    ):

        results.append({
            "check": "Nationality Consistency",
            "status": "WARNING",
            "message": "Passport nationality was not available."
        })

    elif (
        not visa_nationality
        or visa_nationality == "NOTDETECTED"
    ):

        results.append({
            "check": "Nationality Consistency",
            "status": "WARNING",
            "message": "Visa nationality was not available."
        })

    elif passport_nationality == visa_nationality:

        results.append({
            "check": "Nationality Consistency",
            "status": "PASS",
            "message": "Nationality is consistent across the documents."
        })

    else:

        results.append({
            "check": "Nationality Consistency",
            "status": "REVIEW",
            "message": "Nationality mismatch detected between documents."
        })


    # ==================================================
    # 5. OVERALL CROSS-DOCUMENT RESULT
    # ==================================================

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
            "Cross-document inconsistency detected. "
            "Officer review recommended."
        )

    elif has_warning:

        overall_status = "WARNING"

        overall_message = (
            "Some information was unavailable "
            "for complete cross-document comparison."
        )

    else:

        overall_status = "PASS"

        overall_message = (
            "Passport and visa information are "
            "consistent across the compared fields."
        )


    results.append({
        "check": "Overall Cross-Document Analysis",
        "status": overall_status,
        "message": overall_message
    })


    return results
# =========================================================
# NATIONAL ID ↔ PASSPORT COMPARISON
# =========================================================

def compare_national_id_passport(national_id_fields, passport_fields):

    results = []

    # -----------------------------------------------------
    # 1. NAME COMPARISON
    # -----------------------------------------------------

    national_id_name = normalize_name(
        national_id_fields.get("name", "")
    )

    passport_name = normalize_name(
        passport_fields.get("name", "")
    )

    if not national_id_name:
        results.append({
            "check": "National ID ↔ Passport Name",
            "status": "WARNING",
            "message": "National ID name was not available."
        })

    elif not passport_name:
        results.append({
            "check": "National ID ↔ Passport Name",
            "status": "WARNING",
            "message": "Passport name was not available."
        })

    elif national_id_name == passport_name:
        results.append({
            "check": "National ID ↔ Passport Name",
            "status": "PASS",
            "message": "Name matches between National ID and Passport."
        })

    else:
        results.append({
            "check": "National ID ↔ Passport Name",
            "status": "REVIEW",
            "message": "Name mismatch detected between National ID and Passport."
        })


    # -----------------------------------------------------
    # 2. DATE OF BIRTH COMPARISON
    # -----------------------------------------------------

    national_id_dob = normalize_date(
        national_id_fields.get("date_of_birth", "")
    )

    passport_dob = normalize_date(
        passport_fields.get("date_of_birth", "")
    )

    if not national_id_dob:
        results.append({
            "check": "National ID ↔ Passport Date of Birth",
            "status": "WARNING",
            "message": "National ID date of birth was not available."
        })

    elif not passport_dob:
        results.append({
            "check": "National ID ↔ Passport Date of Birth",
            "status": "WARNING",
            "message": "Passport date of birth was not available."
        })

    elif national_id_dob == passport_dob:
        results.append({
            "check": "National ID ↔ Passport Date of Birth",
            "status": "PASS",
            "message": "Date of birth matches between National ID and Passport."
        })

    else:
        results.append({
            "check": "National ID ↔ Passport Date of Birth",
            "status": "REVIEW",
            "message": "Date of birth mismatch detected between National ID and Passport."
        })


    # -----------------------------------------------------
    # 3. GENDER COMPARISON
    # -----------------------------------------------------

    national_id_gender = normalize_text(
        national_id_fields.get("gender", "")
    )

    passport_gender = normalize_text(
        passport_fields.get("gender", "")
    )

    gender_map = {
        "MALE": "M",
        "M": "M",
        "FEMALE": "F",
        "F": "F",
        "X": "X"
    }

    national_id_gender = gender_map.get(
        national_id_gender,
        national_id_gender
    )

    passport_gender = gender_map.get(
        passport_gender,
        passport_gender
    )

    if not national_id_gender:
        results.append({
            "check": "National ID ↔ Passport Gender",
            "status": "WARNING",
            "message": "National ID gender was not available."
        })

    elif not passport_gender:
        results.append({
            "check": "National ID ↔ Passport Gender",
            "status": "WARNING",
            "message": "Passport gender was not available."
        })

    elif national_id_gender == passport_gender:
        results.append({
            "check": "National ID ↔ Passport Gender",
            "status": "PASS",
            "message": "Gender matches between National ID and Passport."
        })

    else:
        results.append({
            "check": "National ID ↔ Passport Gender",
            "status": "REVIEW",
            "message": "Gender mismatch detected between National ID and Passport."
        })


    # -----------------------------------------------------
    # 4. OVERALL RESULT
    # -----------------------------------------------------

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
            "National ID and Passport contain inconsistent identity information. "
            "Officer review recommended."
        )

    elif has_warning:

        overall_status = "WARNING"

        overall_message = (
            "Some National ID ↔ Passport fields were unavailable "
            "for complete comparison."
        )

    else:

        overall_status = "PASS"

        overall_message = (
            "National ID and Passport identity information "
            "is consistent across the compared fields."
        )

    results.append({
        "check": "Overall National ID ↔ Passport Analysis",
        "status": overall_status,
        "message": overall_message
    })

    return results