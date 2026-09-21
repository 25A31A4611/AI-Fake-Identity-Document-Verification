import re


def extract_visa_fields(text):
    """
    Extract visa information from OCR text.

    Prototype only.

    MRZ is given priority for passport number because
    normal OCR may confuse characters such as Z and 2.
    """

    fields = {
        "name": "Not detected",
        "visa_number": "Not detected",
        "visa_type": "Not detected",
        "date_of_birth": "Not detected",
        "date_of_issue": "Not detected",
        "date_of_expiry": "Not detected",
        "nationality": "Not detected"
    }

    # =========================================================
    # CLEAN OCR TEXT
    # =========================================================

    text = text.replace("\r", "\n")

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    upper_text = "\n".join(lines)

    # =========================================================
    # 1. SURNAME
    # =========================================================

    surname = ""

    for i, line in enumerate(lines):

        if line.upper() == "SURNAME":

            if i + 1 < len(lines):

                surname = lines[i + 1].strip()

                surname = re.sub(
                    r"[^A-Za-z .'-]",
                    "",
                    surname
                ).strip()

                break

    # =========================================================
    # 2. GIVEN NAME
    # =========================================================

    given_name = ""

    for i, line in enumerate(lines):

        upper_line = line.upper()

        if "GIVEN NAME" in upper_line:

            if i + 1 < len(lines):

                next_line = lines[i + 1].strip()

                next_line = next_line.rstrip(". ")

                # Find visa type such as B1/B2
                visa_match = re.search(
                    r"\b([A-Z]\d(?:/[A-Z]\d)?)\b",
                    next_line.upper()
                )

                if visa_match:

                    fields["visa_type"] = (
                        visa_match.group(1)
                    )

                    given_name = (
                        next_line[:visa_match.start()]
                        .strip()
                    )

                else:

                    given_name = next_line

                break

    # =========================================================
    # 3. FALLBACK VISA TYPE
    # =========================================================

    if fields["visa_type"] == "Not detected":

        visa_match = re.search(
            r"\b([A-Z]\d(?:/[A-Z]\d)?)\b",
            upper_text
        )

        if visa_match:

            fields["visa_type"] = (
                visa_match.group(1)
            )

    # =========================================================
    # 4. BUILD FULL NAME
    # =========================================================

    if surname and given_name:

        fields["name"] = (
            surname + " " + given_name
        )

    elif surname:

        fields["name"] = surname

    elif given_name:

        fields["name"] = given_name

    # =========================================================
    # 5. MRZ EXTRACTION
    # =========================================================
    #
    # Example:
    #
    # VNUSAGUNNAM<<DHARISHRI<<<<<<<<<<<<
    #
    # Z7654321<<<2GBR7704123F3303204B...
    #
    # MRZ is more reliable for passport number.
    # =========================================================

    mrz_name = ""
    mrz_passport_number = ""

    # ---------------------------------------------------------
    # MRZ NAME
    # ---------------------------------------------------------

    mrz_name_match = re.search(
        r"VNUSA([A-Z]+)<<([A-Z]+)",
        upper_text
    )

    if mrz_name_match:

        mrz_surname = mrz_name_match.group(1)
        mrz_given_name = mrz_name_match.group(2)

        mrz_name = (
            mrz_surname + " " + mrz_given_name
        )

    # ---------------------------------------------------------
    # MRZ PASSPORT NUMBER
    # ---------------------------------------------------------

    mrz_passport_match = re.search(
        r"\b([A-Z][0-9]{7})[<0-9]",
        upper_text
    )

    if mrz_passport_match:

        mrz_passport_number = (
            mrz_passport_match.group(1)
        )

    # =========================================================
    # 6. PASSPORT NUMBER
    # =========================================================
    #
    # IMPORTANT:
    #
    # First use MRZ.
    #
    # This prevents OCR:
    #
    # 27654321
    #
    # from replacing:
    #
    # Z7654321
    # =========================================================

    if mrz_passport_number:

        fields["visa_number"] = (
            mrz_passport_number
        )

    else:

        passport_match = re.search(
            r"Passport Number.*?\n\s*([A-Z0-9]{6,10})",
            upper_text,
            re.IGNORECASE
        )

        if passport_match:

            fields["visa_number"] = (
                passport_match.group(1).strip()
            )

    # =========================================================
    # 7. NAME CLEANUP USING MRZ
    # =========================================================
    #
    # If MRZ gives a clean name, prefer it.
    #
    # This avoids OCR results such as:
    #
    # GUNNAM ye DHARTSHRI B
    #
    # when the MRZ provides:
    #
    # GUNNAM DHARISHRI
    # =========================================================

    if mrz_name:

        fields["name"] = mrz_name

    # =========================================================
    # 8. DATE OF BIRTH
    # =========================================================

    dob_match = re.search(
        r"\b([0-9]{2}[A-Z]{3}[0-9]{4})\b",
        upper_text,
        re.IGNORECASE
    )

    if dob_match:

        fields["date_of_birth"] = (
            dob_match.group(1).upper()
        )

    # =========================================================
    # 9. NATIONALITY
    # =========================================================

    nationality_match = re.search(
        r"Nationality.*?\n.*?\b([A-Z]{3})\b",
        upper_text,
        re.IGNORECASE
    )

    if nationality_match:

        candidate = (
            nationality_match.group(1).upper()
        )

        if candidate in [
            "IND",
            "USA",
            "GBR",
            "CAN",
            "AUS",
            "FRA",
            "DEU",
            "JPN",
            "CHN"
        ]:

            fields["nationality"] = candidate

    # Fallback
    if fields["nationality"] == "Not detected":

        if re.search(r"\bIND\b", upper_text):

            fields["nationality"] = "IND"

    # =========================================================
    # 10. ISSUE DATE + EXPIRY DATE
    # =========================================================

    issue_section = re.search(
        r"Issue Date.*?Expiration Date.*?\n(.*?)\n",
        upper_text,
        re.IGNORECASE
    )

    if issue_section:

        dates = re.findall(
            r"\b[0-9]{2}[A-Z]{3}[0-9]{4}\b",
            issue_section.group(1),
            re.IGNORECASE
        )

        if len(dates) >= 1:

            fields["date_of_issue"] = (
                dates[0].upper()
            )

        if len(dates) >= 2:

            fields["date_of_expiry"] = (
                dates[1].upper()
            )

    # =========================================================
    # 11. FALLBACK DATE EXTRACTION
    # =========================================================

    if (
        fields["date_of_issue"] == "Not detected"
        or
        fields["date_of_expiry"] == "Not detected"
    ):

        all_dates = re.findall(
            r"\b[0-9]{2}[A-Z]{3}[0-9]{4}\b",
            upper_text,
            re.IGNORECASE
        )

        if len(all_dates) >= 3:

            if fields["date_of_birth"] == "Not detected":

                fields["date_of_birth"] = (
                    all_dates[0].upper()
                )

            if fields["date_of_issue"] == "Not detected":

                fields["date_of_issue"] = (
                    all_dates[1].upper()
                )

            if fields["date_of_expiry"] == "Not detected":

                fields["date_of_expiry"] = (
                    all_dates[2].upper()
                )

    # =========================================================
    # 12. FINAL RETURN
    # =========================================================

    return fields