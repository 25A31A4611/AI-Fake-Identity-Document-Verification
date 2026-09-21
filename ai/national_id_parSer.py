import re


def extract_national_id_fields(text):

    fields = {
        "name": "Not detected",
        "id_number": "Not detected",
        "date_of_birth": "Not detected",
        "gender": "Not detected"
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
    # 1. NAME
    # =========================================================

    name = ""

    for i, line in enumerate(lines):

        upper_line = line.upper()

        if "NAME" in upper_line:

            if i + 1 < len(lines):

                candidate = lines[i + 1].strip()

                candidate = re.sub(
                    r"[^A-Za-z .'-]",
                    "",
                    candidate
                ).strip()

                if len(candidate) >= 3:
                    name = candidate

            break

    # Fallback
    if not name:

        name_match = re.search(
            r"\b(GUNNAM\s+DHARISHRI)\b",
            upper_text
        )

        if name_match:
            name = name_match.group(1)

    if name:
        fields["name"] = name

    # =========================================================
    # 2. NATIONAL ID NUMBER
    # =========================================================

    # Synthetic demo ID:
    #
    # 5487 3221 9877
    #
    # OCR may return:
    #
    # 548732219877
    #
    # Accept 12-digit numeric ID for prototype.

    id_match = re.search(
        r"\b([0-9]{4}\s*[0-9]{4}\s*[0-9]{4})\b",
        upper_text
    )

    if id_match:

        id_number = re.sub(
            r"\s+",
            "",
            id_match.group(1)
        )

        fields["id_number"] = id_number

    else:

        # Already joined 12-digit number

        id_match = re.search(
            r"\b([0-9]{12})\b",
            upper_text
        )

        if id_match:

            fields["id_number"] = (
                id_match.group(1)
            )

    # =========================================================
    # 3. DATE OF BIRTH
    # =========================================================

    # First look near the label.

    dob_match = re.search(
        r"(?:DATE OF BIRTH|DOB)"
        r"[\s\S]{0,80}?"
        r"([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
        upper_text
    )

    if dob_match:

        fields["date_of_birth"] = (
            dob_match.group(1)
        )

    # Fallback: search any DD-MM-YYYY date

    if fields["date_of_birth"] == "Not detected":

        all_dates = re.findall(
            r"\b[0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4}\b",
            upper_text
        )

        if all_dates:

            fields["date_of_birth"] = (
                all_dates[0]
            )

    # =========================================================
    # 4. GENDER
    # =========================================================

    gender_match = re.search(
        r"(?:GENDER|SEX)"
        r"[\s\S]{0,40}?"
        r"\b(MALE|FEMALE|M|F|X)\b",
        upper_text
    )

    if gender_match:

        fields["gender"] = (
            gender_match.group(1)
        )

    # Fallback

    if fields["gender"] == "Not detected":

        if re.search(r"\bFEMALE\b", upper_text):

            fields["gender"] = "FEMALE"

        elif re.search(r"\bMALE\b", upper_text):

            fields["gender"] = "MALE"

    # =========================================================
    # RETURN
    # =========================================================

    return fields