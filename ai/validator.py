from datetime import datetime


def validate_passport(fields):
    results = []

    # 1. Check required fields
    required_fields = [
        "name",
        "passport_number",
        "nationality",
        "date_of_birth",
        "gender",
        "date_of_expiry"
    ]

    for field in required_fields:
        value = fields.get(field, "Not detected")

        if value == "Not detected" or not value:
            results.append({
                "check": field.replace("_", " ").title(),
                "status": "WARNING",
                "message": "Required information not detected."
            })
        else:
            results.append({
                "check": field.replace("_", " ").title(),
                "status": "PASS",
                "message": "Information detected."
            })

    # 2. Passport number format
    passport_number = fields.get("passport_number", "")

    if passport_number != "Not detected":
        if len(passport_number) == 8:
            results.append({
                "check": "Passport Number Format",
                "status": "PASS",
                "message": "Passport number format appears valid."
            })
        else:
            results.append({
                "check": "Passport Number Format",
                "status": "WARNING",
                "message": "Passport number format requires review."
            })

    # 3. Expiry date check
    expiry = fields.get("date_of_expiry", "Not detected")

    if expiry != "Not detected":
        try:
            expiry_date = datetime.strptime(
                expiry.replace("/", "-"),
                "%d-%m-%Y"
            )

            today = datetime.today()

            if expiry_date < today:
                results.append({
                    "check": "Passport Expiry",
                    "status": "FAIL",
                    "message": "Passport appears to be expired."
                })
            else:
                results.append({
                    "check": "Passport Expiry",
                    "status": "PASS",
                    "message": "Passport is not expired."
                })

        except ValueError:
            results.append({
                "check": "Passport Expiry",
                "status": "WARNING",
                "message": "Expiry date format could not be verified."
            })

    return results