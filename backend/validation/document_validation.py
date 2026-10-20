import re


# ============================================================
# NORMALIZE TYPE
# ============================================================

def normalize_document_type(value):

    value = str(value or "").strip().lower()

    aliases = {
        "passport": "passport",

        "aadhaar": "aadhaar",
        "aadhar": "aadhaar",
        "aadhar card": "aadhaar",
        "aadhaar card": "aadhaar",

        "national id": "national id",
        "national identity card": "national id",
        "national identity": "national id",
        "identity card": "national id",

        "visa": "visa",

        "travel permit": "travel permit",
        "travel authorization": "travel permit",
        "travel authorisation": "travel permit",
    }

    return aliases.get(value, value)


# ============================================================
# TEXT HELPER
# ============================================================

def get_raw_text(extracted_data):

    return str(
        extracted_data.get("raw_text")
        or extracted_data.get("text")
        or extracted_data.get("ocr_text")
        or ""
    ).lower()


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

def detect_document_type(extracted_data):

    raw_text = get_raw_text(
        extracted_data
    )

    document_number = str(
        extracted_data.get(
            "document_number"
        ) or ""
    ).upper()

    # Normalize OCR spacing
    normalized_text = re.sub(
        r"\s+",
        " ",
        raw_text
    )

    # ========================================================
    # PASSPORT
    # ========================================================

    passport_score = 0

    # Strong passport indicators
    if re.search(
        r"\bpassport\b",
        normalized_text
    ):
        passport_score += 8

    if "republic of india" in normalized_text:
        passport_score += 3

    if "date of expiry" in normalized_text:
        passport_score += 2

    if "place of birth" in normalized_text:
        passport_score += 2

    if "place of issue" in normalized_text:
        passport_score += 2

    # MRZ indicators
    if "<<" in raw_text:
        passport_score += 5

    if re.search(
        r"\bp<[a-z]{3}",
        raw_text
    ):
        passport_score += 6

    if "mrz" in normalized_text:
        passport_score += 4

    # Passport number
    if re.fullmatch(
        r"[A-Z]\d{7}",
        document_number
    ):
        passport_score += 5

    # OCR may read Z as 2
    if re.fullmatch(
        r"2\d{7}",
        document_number
    ):
        passport_score += 3

    # Search passport number directly in OCR
    if re.search(
        r"\b[A-Z]\d{7}\b",
        raw_text.upper()
    ):
        passport_score += 4


    # ========================================================
    # AADHAAR
    # ========================================================

    aadhaar_score = 0

    if re.search(
        r"\baadhaar\b",
        normalized_text
    ):
        aadhaar_score += 8

    if re.search(
        r"\buidai\b",
        normalized_text
    ):
        aadhaar_score += 8

    if "unique identification" in normalized_text:
        aadhaar_score += 5

    # 12-digit Aadhaar pattern
    if re.search(
        r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        raw_text
    ):
        aadhaar_score += 5


    # ========================================================
    # VISA
    # ========================================================

    visa_score = 0

    if re.search(
        r"\bvisa\b",
        normalized_text
    ):
        visa_score += 8

    if "valid until" in normalized_text:
        visa_score += 3

    if "validity" in normalized_text:
        visa_score += 2


    # ========================================================
    # TRAVEL PERMIT
    # ========================================================

    permit_score = 0

    if "travel permit" in normalized_text:
        permit_score += 8

    if "travel authorization" in normalized_text:
        permit_score += 8

    if "travel authorisation" in normalized_text:
        permit_score += 8


    # ========================================================
    # NATIONAL ID
    # ========================================================

    national_id_score = 0

    if "national id" in normalized_text:
        national_id_score += 7

    if "national identity" in normalized_text:
        national_id_score += 7

    if "identity card" in normalized_text:
        national_id_score += 5


    # ========================================================
    # SELECT HIGHEST SCORE
    # ========================================================

    scores = {
        "passport": passport_score,
        "aadhaar": aadhaar_score,
        "visa": visa_score,
        "travel permit": permit_score,
        "national id": national_id_score,
    }

    detected_type = max(
        scores,
        key=scores.get
    )

    highest_score = scores[
        detected_type
    ]

    # --------------------------------------------------------
    # Weak evidence = unknown
    # --------------------------------------------------------

    if highest_score < 3:
        return "unknown"

    return detected_type


# ============================================================
# COMMON VALIDATION HELPERS
# ============================================================

def valid_name(value):

    if not value:
        return False

    value = str(value).strip()

    return len(value) >= 3


def valid_date(value):

    if not value:
        return False

    value = str(value).strip()

    return bool(
        re.fullmatch(
            r"\d{2}[-/.]\d{2}[-/.]\d{4}",
            value
        )
        or
        re.fullmatch(
            r"\d{4}[-/.]\d{2}[-/.]\d{2}",
            value
        )
    )


def valid_gender(value):

    if not value:
        return False

    value = str(value).strip().upper()

    return value in [
        "MALE",
        "FEMALE",
        "M",
        "F",
    ]


def valid_nationality(value):

    if not value:
        return False

    value = str(value).strip()

    return len(value) >= 3


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_document(
    extracted_data,
    document_type,
    document_path=None
):

    checks = []
    reasons = []

    # ========================================================
    # NORMALIZE SELECTED TYPE
    # ========================================================

    selected_type = normalize_document_type(
        document_type
    )

    # ========================================================
    # DETECT ACTUAL TYPE
    # ========================================================

    detected_type = detect_document_type(
        extracted_data
    )

    # ========================================================
    # 1. DOCUMENT TYPE CHECK
    # ========================================================

    type_match = (
        detected_type == selected_type
    )

    checks.append({
        "label": "Document type matches selected type",
        "status": type_match
    })

    if not type_match:

        if detected_type != "unknown":

            reasons.append(
                f"Selected document type is "
                f"'{document_type}', but the uploaded "
                f"document appears to be "
                f"'{detected_type}'."
            )

        else:

            reasons.append(
                f"The uploaded document could not be "
                f"verified as a '{document_type}'."
            )


    # ========================================================
    # PASSPORT VALIDATION
    # ========================================================

    if selected_type == "passport":

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Passport holder name could not be detected."
            )


        # ----------------------------------------------------
        # PASSPORT NUMBER
        # ----------------------------------------------------

        document_number = str(
            extracted_data.get(
                "document_number"
            ) or ""
        ).upper().strip()

        passport_number_valid = bool(
            re.fullmatch(
                r"[A-Z]\d{7}",
                document_number
            )
        )

        checks.append({
            "label": "Passport number detected",
            "status": passport_number_valid
        })

        if not passport_number_valid:

            reasons.append(
                "Valid passport number could not be detected."
            )


        # ----------------------------------------------------
        # DATE OF BIRTH
        # ----------------------------------------------------

        dob = extracted_data.get(
            "date_of_birth"
        )

        dob_valid = valid_date(
            dob
        )

        checks.append({
            "label": "Date of birth format",
            "status": dob_valid
        })

        if not dob_valid:

            reasons.append(
                "Date of birth is missing or invalid."
            )


        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        gender = extracted_data.get(
            "gender"
        )

        gender_valid = valid_gender(
            gender
        )

        checks.append({
            "label": "Gender detected",
            "status": gender_valid
        })

        if not gender_valid:

            reasons.append(
                "Gender could not be detected."
            )


        # ----------------------------------------------------
        # NATIONALITY
        # ----------------------------------------------------

        nationality = extracted_data.get(
            "nationality"
        )

        nationality_valid = valid_nationality(
            nationality
        )

        checks.append({
            "label": "Nationality detected",
            "status": nationality_valid
        })

        if not nationality_valid:

            reasons.append(
                "Nationality could not be detected."
            )


        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        expiry = extracted_data.get(
            "expiry_date"
        )

        expiry_valid = valid_date(
            expiry
        )

        checks.append({
            "label": "Expiry date detected",
            "status": expiry_valid
        })

        if not expiry_valid:

            reasons.append(
                "Passport expiry date could not be detected."
            )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # ADDRESS IS NOT REQUIRED FOR PASSPORT
        # ----------------------------------------------------


    # ========================================================
    # AADHAAR VALIDATION
    # ========================================================

    elif selected_type == "aadhaar":

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Name could not be detected."
            )


        # ----------------------------------------------------
        # AADHAAR NUMBER
        # ----------------------------------------------------

        document_number = str(
            extracted_data.get(
                "document_number"
            ) or ""
        )

        normalized_aadhaar = re.sub(
            r"\s+",
            "",
            document_number
        )

        aadhaar_valid = bool(
            re.fullmatch(
                r"\d{12}",
                normalized_aadhaar
            )
        )

        checks.append({
            "label": "Aadhaar number detected",
            "status": aadhaar_valid
        })

        if not aadhaar_valid:

            reasons.append(
                "Valid Aadhaar number could not be detected."
            )


        # ----------------------------------------------------
        # DATE OF BIRTH
        # ----------------------------------------------------

        dob = extracted_data.get(
            "date_of_birth"
        )

        dob_valid = valid_date(
            dob
        )

        checks.append({
            "label": "Date of birth format",
            "status": dob_valid
        })

        if not dob_valid:

            reasons.append(
                "Date of birth is missing or invalid."
            )


        # ----------------------------------------------------
        # ADDRESS
        # ----------------------------------------------------

        address = extracted_data.get(
            "address"
        )

        address_valid = bool(
            address
            and len(
                str(address).strip()
            ) >= 10
        )

        checks.append({
            "label": "Address detected",
            "status": address_valid
        })

        if not address_valid:

            reasons.append(
                "Address could not be detected."
            )


    # ========================================================
    # VISA VALIDATION
    # ========================================================

    elif selected_type == "visa":

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Visa holder name could not be detected."
            )


        # ----------------------------------------------------
        # DOCUMENT NUMBER
        # ----------------------------------------------------

        document_number = str(
            extracted_data.get(
                "document_number"
            ) or ""
        ).strip()

        visa_number_valid = (
            len(document_number) >= 5
        )

        checks.append({
            "label": "Visa number detected",
            "status": visa_number_valid
        })

        if not visa_number_valid:

            reasons.append(
                "Visa number could not be detected."
            )


        # ----------------------------------------------------
        # EXPIRY / VALIDITY
        # ----------------------------------------------------

        expiry = extracted_data.get(
            "expiry_date"
        )

        expiry_valid = valid_date(
            expiry
        )

        checks.append({
            "label": "Visa validity date detected",
            "status": expiry_valid
        })

        if not expiry_valid:

            reasons.append(
                "Visa validity date could not be detected."
            )


    # ========================================================
    # TRAVEL PERMIT VALIDATION
    # ========================================================

    elif selected_type == "travel permit":

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Travel permit holder name could not be detected."
            )


        # ----------------------------------------------------
        # PERMIT NUMBER
        # ----------------------------------------------------

        document_number = str(
            extracted_data.get(
                "document_number"
            ) or ""
        ).strip()

        permit_number_valid = (
            len(document_number) >= 5
        )

        checks.append({
            "label": "Permit number detected",
            "status": permit_number_valid
        })

        if not permit_number_valid:

            reasons.append(
                "Travel permit number could not be detected."
            )


        # ----------------------------------------------------
        # EXPIRY
        # ----------------------------------------------------

        expiry = extracted_data.get(
            "expiry_date"
        )

        expiry_valid = valid_date(
            expiry
        )

        checks.append({
            "label": "Permit expiry date detected",
            "status": expiry_valid
        })

        if not expiry_valid:

            reasons.append(
                "Travel permit expiry date could not be detected."
            )


    # ========================================================
    # NATIONAL ID VALIDATION
    # ========================================================

    elif selected_type == "national id":

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Name could not be detected."
            )


        # ----------------------------------------------------
        # ID NUMBER
        # ----------------------------------------------------

        document_number = str(
            extracted_data.get(
                "document_number"
            ) or ""
        ).strip()

        id_number_valid = (
            len(document_number) >= 5
        )

        checks.append({
            "label": "Identity number detected",
            "status": id_number_valid
        })

        if not id_number_valid:

            reasons.append(
                "Identity number could not be detected."
            )


        # ----------------------------------------------------
        # DOB
        # ----------------------------------------------------

        dob = extracted_data.get(
            "date_of_birth"
        )

        dob_valid = valid_date(
            dob
        )

        checks.append({
            "label": "Date of birth format",
            "status": dob_valid
        })

        if not dob_valid:

            reasons.append(
                "Date of birth is missing or invalid."
            )


        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        gender = extracted_data.get(
            "gender"
        )

        gender_valid = valid_gender(
            gender
        )

        checks.append({
            "label": "Gender detected",
            "status": gender_valid
        })

        if not gender_valid:

            reasons.append(
                "Gender could not be detected."
            )


    # ========================================================
    # UNKNOWN / OTHER DOCUMENT
    # ========================================================

    else:

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = extracted_data.get(
            "name"
        )

        name_valid = valid_name(
            name
        )

        checks.append({
            "label": "Name detected",
            "status": name_valid
        })

        if not name_valid:

            reasons.append(
                "Name could not be detected."
            )


        # ----------------------------------------------------
        # DOB
        # ----------------------------------------------------

        dob = extracted_data.get(
            "date_of_birth"
        )

        dob_valid = valid_date(
            dob
        )

        checks.append({
            "label": "Date of birth format",
            "status": dob_valid
        })

        if not dob_valid:

            reasons.append(
                "Date of birth is missing or invalid."
            )


        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        gender = extracted_data.get(
            "gender"
        )

        gender_valid = valid_gender(
            gender
        )

        checks.append({
            "label": "Gender detected",
            "status": gender_valid
        })

        if not gender_valid:

            reasons.append(
                "Gender could not be detected."
            )


    # ========================================================
    # CALCULATE VALIDATION SCORE
    # ========================================================

    total_checks = len(
        checks
    )

    passed_checks = sum(
        1
        for check in checks
        if check.get("status") is True
    )

    if total_checks > 0:

        validation_score = round(
            (
                passed_checks
                / total_checks
            ) * 100
        )

    else:

        validation_score = 0


    # ========================================================
    # DOCUMENT TYPE MISMATCH
    # ========================================================

    if not type_match:

        # Wrong document type is a serious failure.
        #
        # Even if OCR found generic fields, the uploaded
        # document must not be considered valid for the
        # selected document category.

        validation_score = min(
            validation_score,
            30
        )

        status = "INVALID"


    # ========================================================
    # DOCUMENT TYPE MATCHED
    # ========================================================

    else:

        if validation_score >= 80:

            status = "VALID"

        elif validation_score >= 50:

            status = "REVIEW"

        else:

            status = "INVALID"


    # ========================================================
    # EXTRA SAFETY:
    # UNKNOWN TYPE CANNOT BE VALID
    # ========================================================

    if detected_type == "unknown":

        if type_match:

            validation_score = min(
                validation_score,
                49
            )

            status = "REVIEW"


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "status": status,

        "score": validation_score,

        "checks": checks,

        "reasons": reasons,

        "selected_type": selected_type,

        "detected_type": detected_type,

        "type_match": type_match
    }