from datetime import datetime


# Fields that should normally remain consistent
# across identity documents.
CONSISTENCY_FIELDS = {
    "full_name": "Full Name",
    "date_of_birth": "Date of Birth",
    "gender": "Gender",
    "nationality": "Nationality",
    "document_number": "Document Number",
}


def normalize(value):
    """
    Normalize values before comparison.

    The comparison logic remains unchanged.
    This function only converts common OCR/document
    variations into a comparable representation.
    """

    if value is None:
        return ""

    value = str(value).strip().upper()

    # Remove common separators/spaces
    value = value.replace("-", "")
    value = value.replace("/", "")
    value = value.replace(".", "")
    value = value.replace(" ", "")

    return value


def normalize_gender(value):
    """
    Normalize common gender representations.

    Examples:
        M      -> MALE
        MALE   -> MALE
        F      -> FEMALE
        FEMALE -> FEMALE
    """

    value = normalize(value)

    if value in ("M", "MALE"):
        return "MALE"

    if value in ("F", "FEMALE"):
        return "FEMALE"

    return value


def normalize_nationality(value):
    """
    Normalize common nationality representations.

    Examples:
        IND    -> INDIAN
        INDIAN -> INDIAN
    """

    value = normalize(value)

    nationality_map = {
        "IND": "INDIAN",
        "INDIAN": "INDIAN",

        "GBR": "BRITISH",
        "GB": "BRITISH",
        "BRITISH": "BRITISH",

        "USA": "AMERICAN",
        "US": "AMERICAN",
        "AMERICAN": "AMERICAN",

        "CAN": "CANADIAN",
        "CANADIAN": "CANADIAN",

        "AUS": "AUSTRALIAN",
        "AUSTRALIAN": "AUSTRALIAN",

        "DEU": "GERMAN",
        "GERMAN": "GERMAN",

        "FRA": "FRENCH",
        "FRENCH": "FRENCH",

        "JPN": "JAPANESE",
        "JAPANESE": "JAPANESE",

        "CHN": "CHINESE",
        "CHINESE": "CHINESE",

        "NPL": "NEPALESE",
        "NEPALESE": "NEPALESE",

        "LKA": "SRI LANKAN",
        "SRILANKAN": "SRI LANKAN",

        "BGD": "BANGLADESHI",
        "BANGLADESHI": "BANGLADESHI",
    }

    return nationality_map.get(value, value)


def normalize_date(value):
    """
    Normalize common date formats.

    Examples:
        25-08-2007
        25/08/2007
        25.08.2007
        25AUG2007

    All are converted to:

        25082007
    """

    value = normalize(value)

    if not value:
        return ""

    # Already numeric date formats
    if len(value) == 8 and value.isdigit():
        return value

    # Common OCR month representations
    month_map = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "SEPT": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12",
    }

    # Handle DDMMMYYYY
    for month_name, month_number in month_map.items():

        if value.startswith(month_name):
            remaining = value[len(month_name):]

            if len(remaining) == 6 and remaining.isdigit():
                day = remaining[:2]
                year = remaining[2:]

                return f"{day}{month_number}{year}"

        if value.endswith(month_name):
            remaining = value[:-len(month_name)]

            if len(remaining) == 6 and remaining.isdigit():
                day = remaining[:2]
                year = remaining[2:]

                return f"{day}{month_number}{year}"

    # Handle DDMMMYYYY explicitly
    if len(value) == 9:

        day = value[:2]
        month = value[2:5]
        year = value[5:]

        if (
            day.isdigit()
            and month in month_map
            and year.isdigit()
        ):
            return f"{day}{month_map[month]}{year}"

    return value


def normalize_field(field, value):
    """
    Apply field-specific normalization while preserving
    the original comparison logic.
    """

    if field == "gender":
        return normalize_gender(value)

    if field == "nationality":
        return normalize_nationality(value)

    if field == "date_of_birth":
        return normalize_date(value)

    return normalize(value)


def compare_documents(documents):
    """
    Compare extracted information from multiple documents.

    Expected input:

    documents = [
        {
            "document_type": "passport",
            "document_number": "P1234567",
            "full_name": "Rahul Kumar",
            "date_of_birth": "15/08/1998",
            "gender": "Male",
            "nationality": "Indian"
        },
        {
            "document_type": "aadhaar",
            "document_number": "123456789012",
            "full_name": "Rahul Kumar",
            "date_of_birth": "15/08/1998",
            "gender": "Male",
            "nationality": "Indian"
        }
    ]
    """

    if not documents:
        return {
            "status": "REVIEW",
            "message": "No documents available for comparison.",
            "documents_checked": 0,
            "matched_fields": [],
            "mismatched_fields": [],
            "risk_points": 0
        }

    if len(documents) < 2:
        return {
            "status": "REVIEW",
            "message": "Cross-document comparison requires at least two documents.",
            "documents_checked": len(documents),
            "matched_fields": [],
            "mismatched_fields": [],
            "risk_points": 0
        }

    matched_fields = []
    mismatched_fields = []

    # Use the first document as the reference document.
    reference = documents[0]

    for field, field_label in CONSISTENCY_FIELDS.items():

        reference_value = normalize_field(
            field,
            reference.get(field)
        )

        # If the reference document doesn't contain this field,
        # skip it.
        if not reference_value:
            continue

        field_values = []

        for document in documents:

            value = normalize_field(
                field,
                document.get(field)
            )

            if value:
                field_values.append({
                    "document_type": document.get(
                        "document_type",
                        "unknown"
                    ),
                    "value": value
                })

        # Need at least two values to compare.
        if len(field_values) < 2:
            continue

        unique_values = set(
            item["value"]
            for item in field_values
        )

        if len(unique_values) == 1:

            matched_fields.append({
                "field": field,
                "label": field_label,
                "value": field_values[0]["value"],
                "documents": [
                    item["document_type"]
                    for item in field_values
                ]
            })

        else:

            mismatched_fields.append({
                "field": field,
                "label": field_label,
                "values": field_values
            })

    # Calculate risk contribution.
    #
    # Each inconsistent identity field adds risk.
    risk_points = len(mismatched_fields) * 15

    if mismatched_fields:
        status = "MISMATCH"
        message = (
            f"{len(mismatched_fields)} identity field(s) "
            "are inconsistent across documents."
        )

    elif matched_fields:
        status = "CONSISTENT"
        message = (
            "Identity information is consistent "
            "across the supplied documents."
        )

    else:
        status = "REVIEW"
        message = (
            "Insufficient common information was found "
            "for cross-document comparison."
        )

    return {
        "status": status,
        "message": message,
        "documents_checked": len(documents),
        "matched_fields": matched_fields,
        "mismatched_fields": mismatched_fields,
        "risk_points": min(risk_points, 60),
        "checked_at": datetime.now().isoformat()
    }