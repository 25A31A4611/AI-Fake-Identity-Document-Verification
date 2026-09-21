from datetime import datetime


def validate_visa(fields):
    """
    Prototype validation module for visa documents.

    This checks extracted visa information and basic
    date/format conditions.

    It does NOT verify against any real government
    database or immigration system.
    """

    results = []

    # ==================================================
    # NAME
    # ==================================================

    name = fields.get("name", "Not detected")

    if name == "Not detected" or not name:
        results.append({
            "check": "Name",
            "status": "WARNING",
            "message": "Visa holder name was not detected."
        })
    else:
        results.append({
            "check": "Name",
            "status": "PASS",
            "message": "Visa holder name was detected."
        })

    # ==================================================
    # VISA NUMBER
    # ==================================================

    visa_number = fields.get(
        "visa_number",
        "Not detected"
    )

    if visa_number == "Not detected" or not visa_number:
        results.append({
            "check": "Visa Number",
            "status": "WARNING",
            "message": "Visa/passport reference number was not detected."
        })
    else:
        results.append({
            "check": "Visa Number",
            "status": "PASS",
            "message": "Visa/passport reference number was detected."
        })

    # ==================================================
    # VISA TYPE
    # ==================================================

    visa_type = fields.get(
        "visa_type",
        "Not detected"
    )

    if visa_type == "Not detected" or not visa_type:
        results.append({
            "check": "Visa Type",
            "status": "WARNING",
            "message": "Visa type was not detected."
        })
    else:
        results.append({
            "check": "Visa Type",
            "status": "PASS",
            "message": "Visa type was detected."
        })

    # ==================================================
    # DATE OF BIRTH
    # ==================================================

    dob = fields.get(
        "date_of_birth",
        "Not detected"
    )

    if dob == "Not detected" or not dob:
        results.append({
            "check": "Date of Birth",
            "status": "WARNING",
            "message": "Date of birth was not detected."
        })
    else:
        results.append({
            "check": "Date of Birth",
            "status": "PASS",
            "message": "Date of birth was detected."
        })

    # ==================================================
    # NATIONALITY
    # ==================================================

    nationality = fields.get(
        "nationality",
        "Not detected"
    )

    if nationality == "Not detected" or not nationality:
        results.append({
            "check": "Nationality",
            "status": "WARNING",
            "message": "Nationality was not detected."
        })
    else:
        results.append({
            "check": "Nationality",
            "status": "PASS",
            "message": "Nationality was detected."
        })

    # ==================================================
    # ISSUE DATE
    # ==================================================

    issue_date = fields.get(
        "date_of_issue",
        "Not detected"
    )

    if issue_date == "Not detected" or not issue_date:
        results.append({
            "check": "Issue Date",
            "status": "WARNING",
            "message": "Visa issue date was not detected."
        })
    else:
        results.append({
            "check": "Issue Date",
            "status": "PASS",
            "message": "Visa issue date was detected."
        })

    # ==================================================
    # EXPIRY DATE
    # ==================================================

    expiry = fields.get(
        "date_of_expiry",
        "Not detected"
    )

    if expiry == "Not detected" or not expiry:

        results.append({
            "check": "Expiry Date",
            "status": "WARNING",
            "message": "Visa expiration date was not detected."
        })

    else:

        try:

            expiry_date = datetime.strptime(
                expiry.upper(),
                "%d%b%Y"
            )

            today = datetime.today()

            if expiry_date < today:

                results.append({
                    "check": "Visa Expiry",
                    "status": "FAIL",
                    "message": "Visa appears to be expired."
                })

            else:

                results.append({
                    "check": "Visa Expiry",
                    "status": "PASS",
                    "message": "Visa is currently within its expiry date."
                })

        except ValueError:

            results.append({
                "check": "Visa Expiry",
                "status": "WARNING",
                "message": "Visa expiration date format could not be verified."
            })

    # ==================================================
    # OVERALL VALIDATION
    # ==================================================

    has_fail = any(
        result["status"] == "FAIL"
        for result in results
    )

    has_warning = any(
        result["status"] == "WARNING"
        for result in results
    )

    if has_fail:

        overall_status = "FAIL"

        overall_message = (
            "Visa validation detected a condition "
            "that requires officer review."
        )

    elif has_warning:

        overall_status = "WARNING"

        overall_message = (
            "Some visa information could not be "
            "completely validated."
        )

    else:

        overall_status = "PASS"

        overall_message = (
            "All detected visa information passed "
            "basic prototype validation."
        )

    results.append({
        "check": "Overall Visa Validation",
        "status": overall_status,
        "message": overall_message
    })

    return results