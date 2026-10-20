import os
import re

import cv2
import pytesseract
from pytesseract import Output


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# TEXT CLEANING HELPERS
# ============================================================

def clean_text(value):
    """
    Basic OCR text cleanup.
    Keeps the original behavior compatible with the existing app.
    """
    if value is None:
        return None

    value = str(value).replace("\x0c", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)

    return value.strip()


def clean_address(value):
    """
    Clean address without aggressively changing OCR output.
    """
    if not value:
        return None

    value = str(value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" :,-")

    return value if value else None


def extract_dates(text):
    """
    Extract common date formats from OCR text.
    Existing formats are preserved.
    """

    if not text:
        return []

    patterns = [
        r"\b\d{2}[-/]\d{2}[-/]\d{4}\b",
        r"\b\d{2}\.\d{2}\.\d{4}\b",
        r"\b\d{4}[-/]\d{2}[-/]\d{2}\b",

        # Added support for visa-style dates:
        # 25AUG2007
        # 20MAR2033
        r"\b\d{2}[A-Z]{3}\d{4}\b",

        # 25 AUG 2007
        r"\b\d{2}\s+[A-Z]{3}\s+\d{4}\b",
    ]

    dates = []

    for pattern in patterns:
        dates.extend(
            re.findall(
                pattern,
                text,
                re.IGNORECASE
            )
        )

    result = []
    seen = set()

    for date in dates:

        date = date.strip()

        key = date.upper()

        if key not in seen:
            result.append(date)
            seen.add(key)

    return result


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_ocr_text(text):
    """
    Normalize OCR text for searching while preserving the
    original raw OCR text separately.
    """

    if not text:
        return ""

    text = str(text).upper()

    text = text.replace("—", "-")
    text = text.replace("–", "-")

    return text


def normalize_passport_number(value):
    """
    Normalize a passport number.

    Indian passport numbers generally follow:
        1 letter + 7 digits

    OCR sometimes reads Z as 2.
    """

    if not value:
        return None

    value = str(value).upper()
    value = re.sub(r"[^A-Z0-9]", "", value)

    if re.fullmatch(r"[A-Z]\d{7}", value):
        return value

    if re.fullmatch(r"2\d{7}", value):
        return "Z" + value[1:]

    return None


# ============================================================
# VISA DATE NORMALIZATION
# ============================================================

MONTH_MAP = {
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
    "DEC": "12",
}


def normalize_visa_date(value):
    """
    Convert visa dates into a consistent DDMMYYYY format.

    Examples:

        25AUG2007  -> 25082007
        20MAR2033  -> 20032033
        25-08-2007 -> 25082007
        25/08/2007 -> 25082007

    This is important because the passport side may return
    25082007 while the visa OCR naturally returns 25AUG2007.
    """

    if not value:
        return None

    value = str(value).upper().strip()

    # --------------------------------------------------------
    # DDMMMYYYY
    # --------------------------------------------------------

    match = re.fullmatch(
        r"(\d{2})([A-Z]{3})(\d{4})",
        value
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        month_number = MONTH_MAP.get(month)

        if month_number:
            return f"{day}{month_number}{year}"

    # --------------------------------------------------------
    # DD MMM YYYY
    # --------------------------------------------------------

    match = re.fullmatch(
        r"(\d{2})\s+([A-Z]{3})\s+(\d{4})",
        value
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        month_number = MONTH_MAP.get(month)

        if month_number:
            return f"{day}{month_number}{year}"

    # --------------------------------------------------------
    # DD-MM-YYYY / DD/MM/YYYY / DD.MM.YYYY
    # --------------------------------------------------------

    match = re.fullmatch(
        r"(\d{2})[-/.](\d{2})[-/.](\d{4})",
        value
    )

    if match:

        return (
            match.group(1)
            + match.group(2)
            + match.group(3)
        )

    # --------------------------------------------------------
    # YYYY-MM-DD
    # --------------------------------------------------------

    match = re.fullmatch(
        r"(\d{4})[-/.](\d{2})[-/.](\d{2})",
        value
    )

    if match:

        return (
            match.group(3)
            + match.group(2)
            + match.group(1)
        )

    # --------------------------------------------------------
    # Already DDMMYYYY
    # --------------------------------------------------------

    if re.fullmatch(r"\d{8}", value):
        return value

    return value


# ============================================================
# PASSPORT NUMBER EXTRACTION
# ============================================================

def extract_passport_number(text):

    if not text:
        return None

    original_text = str(text)
    upper_text = original_text.upper()

    label_patterns = [

        r"PASSPORT\s*(?:NO|NO\.|NUMBER|NUM|#)?\s*[:\-]?\s*([A-Z2]\d{7})",

        r"PASSPORT\s*(?:NO|NUMBER)?\s*[:\-]?\s*\n?\s*([A-Z2]\d{7})",

        r"DOCUMENT\s*(?:NO|NUMBER)?\s*[:\-]?\s*([A-Z2]\d{7})",
    ]

    for pattern in label_patterns:

        match = re.search(
            pattern,
            upper_text,
            re.IGNORECASE
        )

        if match:

            number = normalize_passport_number(
                match.group(1)
            )

            if number:
                return number

    lines = upper_text.splitlines()

    for line in lines:

        cleaned_line = re.sub(
            r"[^A-Z0-9<>]",
            "",
            line
        )

        match = re.search(
            r"\b([A-Z]\d{7})\b",
            cleaned_line
        )

        if match:

            number = normalize_passport_number(
                match.group(1)
            )

            if number:
                return number

        match = re.search(
            r"\b(2\d{7})\b",
            cleaned_line
        )

        if match:

            number = normalize_passport_number(
                match.group(1)
            )

            if number:
                return number

    match = re.search(
        r"\b([A-Z]\d{7})\b",
        upper_text
    )

    if match:

        number = normalize_passport_number(
            match.group(1)
        )

        if number:
            return number

    match = re.search(
        r"\b(2\d{7})\b",
        upper_text
    )

    if match:

        number = normalize_passport_number(
            match.group(1)
        )

        if number:
            return number

    for line in lines:

        cleaned_line = re.sub(
            r"[^A-Z0-9<]",
            "",
            line
        )

        match = re.search(
            r"([A-Z2]\d{7})\d",
            cleaned_line
        )

        if match:

            number = normalize_passport_number(
                match.group(1)
            )

            if number:
                return number

        match = re.search(
            r"<([A-Z2]\d{7})\d",
            cleaned_line
        )

        if match:

            number = normalize_passport_number(
                match.group(1)
            )

            if number:
                return number

    return None


# ============================================================
# AADHAAR NUMBER EXTRACTION
# ============================================================

def extract_aadhaar_number(text):

    if not text:
        return None

    match = re.search(
        r"\b(\d{4})\s+(\d{4})\s+(\d{4})\b",
        str(text)
    )

    if match:

        return (
            f"{match.group(1)} "
            f"{match.group(2)} "
            f"{match.group(3)}"
        )

    match = re.search(
        r"\b(\d{12})\b",
        str(text)
    )

    if match:

        number = match.group(1)

        return (
            number[:4]
            + " "
            + number[4:8]
            + " "
            + number[8:]
        )

    return None


# ============================================================
# NATIONALITY EXTRACTION
# ============================================================

KNOWN_NATIONALITIES = [

    "INDIAN",
    "INDIA",
    "AMERICAN",
    "BRITISH",
    "CANADIAN",
    "AUSTRALIAN",
    "GERMAN",
    "FRENCH",
    "ITALIAN",
    "SPANISH",
    "JAPANESE",
    "CHINESE",
    "KOREAN",
    "NEPALESE",
    "BHUTANESE",
    "BANGLADESHI",
    "SRI LANKAN",
    "PAKISTANI",
    "AFGHAN",
    "AFGHANISTAN",
]


def extract_nationality(text):

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    nationality_match = re.search(
        r"NATIONALITY\s*[:\-]?\s*([A-Z ]{3,25})",
        upper_text,
        re.IGNORECASE
    )

    if nationality_match:

        value = nationality_match.group(1).strip()

        value = re.sub(
            r"\b(NAME|SEX|GENDER|DATE|DOB|BIRTH|PASSPORT|INDIA)\b",
            "",
            value
        ).strip()

        for nationality in KNOWN_NATIONALITIES:

            if nationality in value:

                if nationality == "INDIA":
                    return "INDIAN"

                return nationality

    lines = [
        re.sub(
            r"\s+",
            " ",
            line.strip()
        )
        for line in upper_text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if "NATIONALITY" in line:

            for nationality in KNOWN_NATIONALITIES:

                if nationality in line:

                    if nationality == "INDIA":
                        return "INDIAN"

                    return nationality

            for next_index in range(
                index + 1,
                min(index + 4, len(lines))
            ):

                candidate = lines[next_index]

                for nationality in KNOWN_NATIONALITIES:

                    if nationality in candidate:

                        if nationality == "INDIA":
                            return "INDIAN"

                        return nationality

    for nationality in KNOWN_NATIONALITIES:

        if re.search(
            rf"\b{re.escape(nationality)}\b",
            upper_text
        ):

            if nationality == "INDIA":
                return "INDIAN"

            return nationality

    return None


# ============================================================
# GENDER EXTRACTION
# ============================================================

def extract_gender(text):

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    match = re.search(
        r"(?:SEX|GENDER)\s*[:\-]?\s*(FEMALE|MALE)\b",
        upper_text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    match = re.search(
        r"(?:SEX|GENDER)[^\n]{0,100}?\b(FEMALE|MALE)\b",
        upper_text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    lines = upper_text.splitlines()

    for i, line in enumerate(lines):

        line = line.strip()

        if not line:
            continue

        if re.search(r"\bFEMALE\b", line):
            return "FEMALE"

        if re.search(r"\bMALE\b", line):
            return "MALE"

        if re.fullmatch(
            r"FEMALE\s*/?\s*F?",
            line
        ):
            return "FEMALE"

        if re.fullmatch(
            r"MALE\s*/?\s*M?",
            line
        ):
            return "MALE"

    for line in lines:

        line = line.strip()

        if line in {
            "F",
            "FEMALE",
            "FEMALE/F"
        }:
            return "FEMALE"

        if line in {
            "M",
            "MALE",
            "MALE/M"
        }:
            return "MALE"

    return None


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_labeled_date(text, labels):

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    label_expression = "|".join(
        re.escape(label)
        for label in labels
    )

    date_pattern = (
        r"(\d{2}[-/.]\d{2}[-/.]\d{4}"
        r"|\d{4}[-/.]\d{2}[-/.]\d{2})"
    )

    pattern = (
        rf"(?:{label_expression})"
        rf"\s*[:\-]?\s*"
        rf"(?:\n\s*)?"
        rf"{date_pattern}"
    )

    match = re.search(
        pattern,
        upper_text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


def extract_date_of_birth(text):

    labels = [
        "DATE OF BIRTH",
        "DATE OF BIRTH.",
        "DOB",
        "BIRTH",
    ]

    return extract_labeled_date(
        text,
        labels
    )


def extract_expiry_date(text):

    labels = [
        "DATE OF EXPIRY",
        "DATE OF EXPIRY.",
        "EXPIRY",
        "EXPIRATION",
        "VALID UNTIL",
        "VALID TILL",
    ]

    return extract_labeled_date(
        text,
        labels
    )


# ============================================================
# NAME EXTRACTION
# ============================================================

NAME_STOP_WORDS = {

    "PASSPORT",
    "REPUBLIC",
    "INDIA",
    "INDIAN",
    "NATIONALITY",
    "DATE",
    "BIRTH",
    "EXPIRY",
    "EXPIRATION",
    "SEX",
    "GENDER",
    "MALE",
    "FEMALE",
    "SURNAME",
    "GIVEN",
    "NAMES",
    "NAME",
    "PLACE",
    "ISSUE",
    "ISSUING",
    "AUTHORITY",
    "CONTROL",
    "NUMBER",
    "VISA",
    "TYPE",
    "CLASS",
    "ENTRIES",
    "ANNOTATION",
    "CLEARANCE",
    "RECEIVED",
    "DEPARTMENT",
    "AUTHORIZATION",
}


def clean_name_candidate(value):

    if not value:
        return None

    value = str(value).upper()

    value = re.sub(
        r"[^A-Z .'-]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    if not value:
        return None

    words = value.split()

    filtered_words = [
        word
        for word in words
        if word not in NAME_STOP_WORDS
    ]

    if not filtered_words:
        return None

    value = " ".join(filtered_words)

    if len(value) > 60:
        value = value[:60].strip()

    return value if value else None


def extract_passport_name(text):

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    mrz_lines = [
        line.strip()
        for line in upper_text.splitlines()
        if line.strip()
    ]

    for line in mrz_lines:

        if "<<" in line:

            candidate = line.split("<<")[0]

            candidate = re.sub(
                r"^[^A-Z]+",
                "",
                candidate
            )

            candidate = clean_name_candidate(
                candidate
            )

            if candidate:

                words = candidate.split()

                if len(words) >= 2:
                    return candidate

    surname = None
    given_names = None

    lines = [
        re.sub(
            r"\s+",
            " ",
            line.strip()
        )
        for line in upper_text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if re.search(
            r"\bSURNAME\b",
            line
        ):

            after = re.sub(
                r".*?\bSURNAME\b\s*[:\-]?\s*",
                "",
                line
            ).strip()

            candidate = clean_name_candidate(
                after
            )

            if candidate:
                surname = candidate
                break

            for next_index in range(
                index + 1,
                min(index + 3, len(lines))
            ):

                candidate = clean_name_candidate(
                    lines[next_index]
                )

                if candidate:
                    surname = candidate
                    break

            if surname:
                break

    for index, line in enumerate(lines):

        if re.search(
            r"\bGIVEN\s+NAMES?\b",
            line
        ):

            after = re.sub(
                r".*?\bGIVEN\s+NAMES?\b\s*[:\-]?\s*",
                "",
                line
            ).strip()

            candidate = clean_name_candidate(
                after
            )

            if candidate:
                given_names = candidate
                break

            for next_index in range(
                index + 1,
                min(index + 3, len(lines))
            ):

                candidate = clean_name_candidate(
                    lines[next_index]
                )

                if candidate:
                    given_names = candidate
                    break

            if given_names:
                break

    if surname and given_names:
        return f"{surname} {given_names}".strip()

    if given_names:
        return given_names

    if surname:
        return surname

    candidates = []

    for line in lines:

        cleaned = clean_name_candidate(line)

        if not cleaned:
            continue

        words = cleaned.split()

        if len(cleaned) < 5:
            continue

        if len(words) < 2:
            continue

        if any(
            word in NAME_STOP_WORDS
            for word in words
        ):
            continue

        candidates.append(cleaned)

    if candidates:
        return candidates[0]

    return None


# ============================================================
# GENERIC NAME EXTRACTION
# ============================================================

def extract_generic_name(text):

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    patterns = [

        r"(?:NAME|FULL NAME)\s*[:\-]?\s*([A-Z][A-Z .'-]{2,60})",

        r"(?:NAME OF HOLDER)\s*[:\-]?\s*([A-Z][A-Z .'-]{2,60})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            upper_text,
            re.IGNORECASE
        )

        if match:

            candidate = clean_name_candidate(
                match.group(1)
            )

            if candidate:
                return candidate

    return None


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

def detect_document_type(text):

    if not text:
        return "unknown"

    upper_text = normalize_ocr_text(text)

    scores = {

        "passport": 0,
        "aadhaar": 0,
        "visa": 0,
        "travel permit": 0,
        "national id": 0,
    }

    # --------------------------------------------------------
    # Passport
    # --------------------------------------------------------

    if re.search(
        r"\bPASSPORT\b",
        upper_text
    ):
        scores["passport"] += 8

    if "REPUBLIC OF INDIA" in upper_text:
        scores["passport"] += 3

    if re.search(
        r"\bP<[A-Z]{3}",
        upper_text
    ):
        scores["passport"] += 6

    if "MRZ" in upper_text:
        scores["passport"] += 4

    if re.search(
        r"\b[A-Z]\d{7}\b",
        upper_text
    ):
        scores["passport"] += 4

    if re.search(
        r"\b2\d{7}\b",
        upper_text
    ):
        scores["passport"] += 2

    if "NATIONALITY" in upper_text:
        scores["passport"] += 1

    if "DATE OF EXPIRY" in upper_text:
        scores["passport"] += 2

    # --------------------------------------------------------
    # Aadhaar
    # --------------------------------------------------------

    if "AADHAAR" in upper_text:
        scores["aadhaar"] += 8

    if "UIDAI" in upper_text:
        scores["aadhaar"] += 8

    if "UNIQUE IDENTIFICATION" in upper_text:
        scores["aadhaar"] += 5

    if re.search(
        r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        upper_text
    ):
        scores["aadhaar"] += 4

    # --------------------------------------------------------
    # Visa
    # --------------------------------------------------------

    if re.search(
        r"\bVISA\b",
        upper_text
    ):
        scores["visa"] += 8

    if "VALID UNTIL" in upper_text:
        scores["visa"] += 2

    if "ENTRY" in upper_text:
        scores["visa"] += 1

    # --------------------------------------------------------
    # Travel Permit
    # --------------------------------------------------------

    if "TRAVEL PERMIT" in upper_text:
        scores["travel permit"] += 8

    if "TRAVEL AUTHORIZATION" in upper_text:
        scores["travel permit"] += 8

    if "TRAVEL AUTHORISATION" in upper_text:
        scores["travel permit"] += 8

    # --------------------------------------------------------
    # National ID
    # --------------------------------------------------------

    if "NATIONAL ID" in upper_text:
        scores["national id"] += 7

    if "NATIONAL IDENTITY" in upper_text:
        scores["national id"] += 7

    if "IDENTITY CARD" in upper_text:
        scores["national id"] += 5

    detected_type = max(
        scores,
        key=scores.get
    )

    highest_score = scores[detected_type]

    if highest_score < 3:
        return "unknown"

    return detected_type


# ============================================================
# PASSPORT MRZ OCR
# ============================================================

def extract_passport_mrz_text(image, gray):

    try:

        height, width = gray.shape[:2]

        start_y = int(height * 0.68)

        mrz_crop = gray[
            start_y:height,
            0:width
        ]

        if mrz_crop.size == 0:
            return ""

        mrz_crop = cv2.resize(
            mrz_crop,
            None,
            fx=2.5,
            fy=2.5,
            interpolation=cv2.INTER_CUBIC
        )

        mrz_crop = cv2.GaussianBlur(
            mrz_crop,
            (3, 3),
            0
        )

        mrz_crop = cv2.threshold(
            mrz_crop,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        mrz_text = pytesseract.image_to_string(
            mrz_crop,
            config="--psm 6"
        )

        return clean_text(mrz_text)

    except Exception:
        return ""


# ============================================================
# VISA LAYOUT OCR
# ============================================================

def extract_visa_layout_ocr(image):

    """
    Additional OCR pass specifically for visas.

    PSM 11 is much better for documents where labels and
    values are separated spatially.

    This does NOT replace the existing OCR.
    """

    try:

        if image is None:
            return ""

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        # ----------------------------------------------------
        # Pass 1 - original grayscale
        # ----------------------------------------------------

        text_1 = pytesseract.image_to_string(
            gray,
            config="--psm 11"
        )

        # ----------------------------------------------------
        # Pass 2 - enlarged grayscale
        # ----------------------------------------------------

        height, width = gray.shape[:2]

        scale = 2.0

        enlarged = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

        text_2 = pytesseract.image_to_string(
            enlarged,
            config="--psm 11"
        )

        # ----------------------------------------------------
        # Combine
        # ----------------------------------------------------

        combined = "\n".join(
            part
            for part in [
                text_1,
                text_2
            ]
            if part
        )

        return clean_text(combined)

    except Exception:

        return ""


# ============================================================
# VISA WORD-LEVEL OCR
# ============================================================

def get_visa_ocr_words(image):

    """
    Get word-level OCR with coordinates.

    This is used only for visa extraction.

    It allows us to understand:

        Surname
        GUNNAM

        Given Name
        DHARISHRI

        Birth Date
        25AUG2007

        Expiration Date
        20MAR2033

    instead of relying only on OCR text order.
    """

    try:

        if image is None:
            return []

        data = pytesseract.image_to_data(
            image,
            config="--psm 11",
            output_type=Output.DICT
        )

        words = []

        total = len(data["text"])

        for i in range(total):

            text = data["text"][i]

            if not text:
                continue

            text = text.strip()

            if not text:
                continue

            try:
                confidence = float(
                    data["conf"][i]
                )
            except Exception:
                confidence = 0

            if confidence < 10:
                continue

            words.append({
                "text": text,
                "upper": text.upper(),
                "left": int(data["left"][i]),
                "top": int(data["top"][i]),
                "width": int(data["width"][i]),
                "height": int(data["height"][i]),
                "right": (
                    int(data["left"][i])
                    + int(data["width"][i])
                ),
                "bottom": (
                    int(data["top"][i])
                    + int(data["height"][i])
                ),
                "center_x": (
                    int(data["left"][i])
                    + int(data["width"][i]) / 2
                ),
                "center_y": (
                    int(data["top"][i])
                    + int(data["height"][i]) / 2
                ),
            })

        return words

    except Exception:

        return []


# ============================================================
# VISA WORD HELPERS
# ============================================================

def visa_find_label(words, label_parts):

    """
    Find a label such as:

        Surname
        Given Name
        Birth Date
        Expiration Date

    """

    if not words:
        return None

    label_parts = [
        part.upper()
        for part in label_parts
    ]

    # --------------------------------------------------------
    # One-word label
    # --------------------------------------------------------

    if len(label_parts) == 1:

        target = label_parts[0]

        for word in words:

            if word["upper"] == target:

                return {
                    "left": word["left"],
                    "right": word["right"],
                    "top": word["top"],
                    "bottom": word["bottom"],
                    "center_x": word["center_x"],
                    "center_y": word["center_y"],
                }

    # --------------------------------------------------------
    # Multi-word label
    # --------------------------------------------------------

    for first in words:

        if first["upper"] != label_parts[0]:
            continue

        current = [first]

        last = first

        matched = True

        for part in label_parts[1:]:

            candidates = [
                word
                for word in words
                if word["upper"] == part
                and abs(
                    word["center_y"]
                    - first["center_y"]
                ) < 35
                and word["left"] >= last["right"] - 10
            ]

            if not candidates:

                matched = False
                break

            next_word = min(
                candidates,
                key=lambda w:
                abs(
                    w["center_y"]
                    - first["center_y"]
                )
                + max(
                    0,
                    w["left"] - last["right"]
                )
            )

            current.append(next_word)
            last = next_word

        if matched:

            return {
                "left": min(
                    word["left"]
                    for word in current
                ),
                "right": max(
                    word["right"]
                    for word in current
                ),
                "top": min(
                    word["top"]
                    for word in current
                ),
                "bottom": max(
                    word["bottom"]
                    for word in current
                ),
                "center_x": (
                    min(
                        word["left"]
                        for word in current
                    )
                    +
                    max(
                        word["right"]
                        for word in current
                    )
                ) / 2,
                "center_y": (
                    min(
                        word["top"]
                        for word in current
                    )
                    +
                    max(
                        word["bottom"]
                        for word in current
                    )
                ) / 2,
            }

    return None


def visa_words_below_label(
    words,
    label_box,
    max_vertical_distance=90,
    horizontal_distance=220
):

    """
    Find words immediately below a label.

    We intentionally use spatial distance rather than OCR
    sequence. This is the important part that prevents:

        Birth Date -> Expiration Date

    from being mixed up.
    """

    if not label_box:
        return []

    label_x = label_box["center_x"]
    label_bottom = label_box["bottom"]

    candidates = []

    for word in words:

        if word["top"] <= label_bottom:
            continue

        vertical_distance = (
            word["top"] - label_bottom
        )

        if vertical_distance > max_vertical_distance:
            continue

        horizontal_distance_value = abs(
            word["center_x"] - label_x
        )

        if (
            horizontal_distance_value
            > horizontal_distance
        ):
            continue

        candidates.append(
            (
                vertical_distance,
                horizontal_distance_value,
                word
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1]
        )
    )

    return [
        item[2]
        for item in candidates
    ]


def visa_date_from_words(words):

    """
    Return the first valid date-like word.
    """

    for word in words:

        text = word["upper"]

        # 25AUG2007
        if re.fullmatch(
            r"\d{2}[A-Z]{3}\d{4}",
            text
        ):
            return normalize_visa_date(text)

        # 25-08-2007
        if re.fullmatch(
            r"\d{2}[-/.]\d{2}[-/.]\d{4}",
            text
        ):
            return normalize_visa_date(text)

        # OCR may separate it as 25 AUG 2007.
        if re.fullmatch(
            r"\d{2}",
            text
        ):
            index = words.index(word)

            if index + 2 < len(words):

                month = words[index + 1]["upper"]
                year = words[index + 2]["upper"]

                combined = (
                    text
                    + month
                    + year
                )

                if re.fullmatch(
                    r"\d{2}[A-Z]{3}\d{4}",
                    combined
                ):
                    return normalize_visa_date(
                        combined
                    )

    return None


def visa_text_from_words(words):

    """
    Return a short clean value from words below a label.

    Used for names, nationality, gender, passport number, etc.
    """

    if not words:
        return None

    # Keep only the first few spatially closest words.
    selected = words[:5]

    values = []

    for word in selected:

        value = word["upper"]

        if value in {
            "SURNAME",
            "GIVEN",
            "NAME",
            "BIRTH",
            "DATE",
            "EXPIRATION",
            "SEX",
            "NATIONALITY",
            "ENTRIES",
            "ISSUE",
            "ANNOTATION",
        }:
            continue

        values.append(value)

    if not values:
        return None

    return " ".join(values).strip()


# ============================================================
# VISA MRZ NAME FALLBACK
# ============================================================

def extract_visa_mrz_name(text):

    """
    Extract visa name from the machine-readable line.

    Example:

        VNUSAGUNNAM<<DHARISHRI<<<<<<<<

    becomes:

        GUNNAM DHARISHRI

    This is a fallback only. Label-based extraction has priority.
    """

    if not text:
        return None

    upper_text = normalize_ocr_text(text)

    lines = upper_text.splitlines()

    for line in lines:

        line = re.sub(
            r"\s+",
            "",
            line
        )

        if "<<" not in line:
            continue

        # ----------------------------------------------------
        # Try common US visa MRZ structure.
        # ----------------------------------------------------

        match = re.search(
            r"V[A-Z]?USA([A-Z]+)<<([A-Z]+)",
            line
        )

        if match:

            surname = match.group(1)
            given = match.group(2)

            return clean_name_candidate(
                f"{surname} {given}"
            )

        # ----------------------------------------------------
        # Generic MRZ fallback.
        # ----------------------------------------------------

        match = re.search(
            r"([A-Z]{3,})<<([A-Z]{3,})",
            line
        )

        if match:

            left = match.group(1)
            right = match.group(2)

            # Remove common visa prefixes.
            for prefix in [
                "VNUSA",
                "VUSA",
                "VNU",
                "VISA",
            ]:

                if left.startswith(prefix):
                    left = left[len(prefix):]
                    break

            if len(left) >= 2:

                return clean_name_candidate(
                    f"{left} {right}"
                )

    return None


# ============================================================
# ROBUST VISA EXTRACTION FROM IMAGE
# ============================================================

def extract_visa_fields_from_image(image):

    """
    Main layout-aware visa extraction.

    This function is intentionally isolated from the existing
    passport/Aadhaar/travel-permit/national-ID logic.
    """

    result = {
        "name": None,
        "document_number": None,
        "nationality": None,
        "date_of_birth": None,
        "gender": None,
        "expiry_date": None,
    }

    if image is None:
        return result

    words = get_visa_ocr_words(image)

    if not words:
        return result

    # ========================================================
    # SURNAME
    # ========================================================

    surname_label = visa_find_label(
        words,
        ["SURNAME"]
    )

    surname = None

    if surname_label:

        candidates = visa_words_below_label(
            words,
            surname_label,
            max_vertical_distance=80,
            horizontal_distance=180
        )

        for word in candidates:

            candidate = clean_name_candidate(
                word["upper"]
            )

            if candidate:

                # Reject obvious non-name values.
                if (
                    candidate
                    not in NAME_STOP_WORDS
                    and not re.fullmatch(
                        r"\d+",
                        candidate
                    )
                ):
                    surname = candidate
                    break

    # ========================================================
    # GIVEN NAME
    # ========================================================

    given_label = visa_find_label(
        words,
        ["GIVEN", "NAME"]
    )

    given_name = None

    if given_label:

        candidates = visa_words_below_label(
            words,
            given_label,
            max_vertical_distance=90,
            horizontal_distance=180
        )

        for word in candidates:

            candidate = clean_name_candidate(
                word["upper"]
            )

            if candidate:

                if (
                    candidate
                    not in NAME_STOP_WORDS
                    and not re.fullmatch(
                        r"\d+",
                        candidate
                    )
                ):
                    given_name = candidate
                    break

    if surname and given_name:

        result["name"] = (
            f"{surname} {given_name}"
        )

    elif surname:

        result["name"] = surname

    elif given_name:

        result["name"] = given_name

    # ========================================================
    # PASSPORT NUMBER
    # ========================================================

    passport_label = visa_find_label(
        words,
        ["PASSPORT", "NUMBER"]
    )

    if passport_label:

        candidates = visa_words_below_label(
            words,
            passport_label,
            max_vertical_distance=80,
            horizontal_distance=180
        )

        for word in candidates:

            candidate = normalize_passport_number(
                word["upper"]
            )

            if candidate:

                result["document_number"] = candidate
                break

    # ========================================================
    # SEX
    # ========================================================

    sex_label = visa_find_label(
        words,
        ["SEX"]
    )

    if sex_label:

        candidates = visa_words_below_label(
            words,
            sex_label,
            max_vertical_distance=80,
            horizontal_distance=100
        )

        for word in candidates:

            value = word["upper"]

            if value == "F":
                result["gender"] = "FEMALE"
                break

            if value == "M":
                result["gender"] = "MALE"
                break

            if value == "FEMALE":
                result["gender"] = "FEMALE"
                break

            if value == "MALE":
                result["gender"] = "MALE"
                break

    # ========================================================
    # BIRTH DATE
    # ========================================================

    birth_label = visa_find_label(
        words,
        ["BIRTH", "DATE"]
    )

    if birth_label:

        candidates = visa_words_below_label(
            words,
            birth_label,
            max_vertical_distance=80,
            horizontal_distance=180
        )

        birth_date = visa_date_from_words(
            candidates
        )

        if birth_date:

            result["date_of_birth"] = birth_date

    # ========================================================
    # NATIONALITY
    # ========================================================

    nationality_label = visa_find_label(
        words,
        ["NATIONALITY"]
    )

    if nationality_label:

        candidates = visa_words_below_label(
            words,
            nationality_label,
            max_vertical_distance=80,
            horizontal_distance=130
        )

        for word in candidates:

            value = word["upper"]

            if value == "IND":
                result["nationality"] = "INDIAN"
                break

            if value in KNOWN_NATIONALITIES:

                if value == "INDIA":
                    result["nationality"] = "INDIAN"
                else:
                    result["nationality"] = value

                break

    # ========================================================
    # EXPIRATION DATE
    # ========================================================

    expiration_label = visa_find_label(
        words,
        ["EXPIRATION", "DATE"]
    )

    if expiration_label:

        candidates = visa_words_below_label(
            words,
            expiration_label,
            max_vertical_distance=90,
            horizontal_distance=180
        )

        expiry_date = visa_date_from_words(
            candidates
        )

        if expiry_date:

            result["expiry_date"] = expiry_date

    return result


# ============================================================
# MAIN DOCUMENT FIELD EXTRACTION
# ============================================================

def extract_document_fields(image_path):

    result = {

        "name": None,
        "document_number": None,
        "nationality": None,
        "date_of_birth": None,
        "gender": None,
        "expiry_date": None,
        "address": None,
        "raw_text": "",
        "document_type": "unknown",
    }

    # ========================================================
    # CHECK IMAGE
    # ========================================================

    if (
        not image_path
        or not os.path.exists(image_path)
    ):

        result["raw_text"] = ""

        return result

    # ========================================================
    # READ IMAGE
    # ========================================================

    image = cv2.imread(
        image_path
    )

    if image is None:

        result["raw_text"] = ""

        return result

    # ========================================================
    # GRAYSCALE
    # ========================================================

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # ========================================================
    # UPSCALE
    # ========================================================

    height, width = gray.shape[:2]

    if width < 1600:

        scale = 1600 / width

        gray_for_ocr = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

    else:

        gray_for_ocr = gray.copy()

    # ========================================================
    # DENOISE
    # ========================================================

    blurred = cv2.GaussianBlur(
        gray_for_ocr,
        (3, 3),
        0
    )

    # ========================================================
    # THRESHOLD
    # ========================================================

    processed = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    # ========================================================
    # MAIN OCR
    # ========================================================

    try:

        ocr_text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )

    except Exception:

        ocr_text = pytesseract.image_to_string(
            gray_for_ocr,
            config="--psm 6"
        )

    print(
        "\n========== RAW OCR TEXT =========="
    )

    print(ocr_text)

    print(
        "========== END RAW OCR TEXT ==========\n"
    )

    ocr_text = clean_text(
        ocr_text
    )

    # ========================================================
    # MRZ OCR
    # ========================================================

    mrz_text = extract_passport_mrz_text(
        image,
        gray
    )

    if mrz_text:

        combined_text = (
            ocr_text
            + "\n"
            + mrz_text
        ).strip()

    else:

        combined_text = ocr_text

    # ========================================================
    # PRESERVE RAW OCR
    # ========================================================

    result["raw_text"] = combined_text

    # ========================================================
    # DETECT DOCUMENT TYPE
    # ========================================================

    detected_type = detect_document_type(
        combined_text
    )

    result["document_type"] = detected_type

    # ========================================================
    # VISA-SPECIFIC EXTRA OCR
    #
    # IMPORTANT:
    #
    # This is performed only when the document has already
    # been detected as a visa.
    #
    # Therefore passport/Aadhaar/etc. existing logic is
    # not changed by this additional OCR.
    # ========================================================

    visa_layout_text = ""

    visa_image_fields = {}

    if detected_type == "visa":

        visa_layout_text = extract_visa_layout_ocr(
            image
        )

        if visa_layout_text:

            result["raw_text"] = (
                result["raw_text"]
                + "\n"
                + visa_layout_text
            ).strip()

        visa_image_fields = (
            extract_visa_fields_from_image(
                image
            )
        )

    # ========================================================
    # PASSPORT EXTRACTION
    # ========================================================

    if detected_type == "passport":

        passport_number = extract_passport_number(
            combined_text
        )

        result["document_number"] = (
            passport_number
        )

        passport_name = extract_passport_name(
            combined_text
        )

        result["name"] = passport_name

        result["nationality"] = (
            extract_nationality(
                combined_text
            )
        )

        result["gender"] = extract_gender(
            combined_text
        )

        dob = extract_date_of_birth(
            combined_text
        )

        if not dob:

            dates = extract_dates(
                combined_text
            )

            if dates:
                dob = dates[0]

        result["date_of_birth"] = dob

        expiry = extract_expiry_date(
            combined_text
        )

        if not expiry:

            dates = extract_dates(
                combined_text
            )

            if len(dates) >= 2:
                expiry = dates[-1]

        result["expiry_date"] = expiry

        result["address"] = None

    # ========================================================
    # AADHAAR EXTRACTION
    # ========================================================

    elif detected_type == "aadhaar":

        result["document_number"] = (
            extract_aadhaar_number(
                combined_text
            )
        )

        result["name"] = extract_generic_name(
            combined_text
        )

        result["gender"] = extract_gender(
            combined_text
        )

        result["date_of_birth"] = (
            extract_date_of_birth(
                combined_text
            )
        )

        address_match = re.search(
            r"(?:ADDRESS|ADDR)\s*[:\-]?\s*(.+?)(?:\n\s*\n|$)",
            combined_text,
            re.IGNORECASE | re.DOTALL
        )

        if address_match:

            result["address"] = clean_address(
                address_match.group(1)
            )

        result["expiry_date"] = None

        result["nationality"] = None

    # ========================================================
    # VISA EXTRACTION
    # ========================================================

    elif detected_type == "visa":

        # ----------------------------------------------------
        # PRIMARY METHOD:
        #
        # Spatial / layout-aware extraction
        # ----------------------------------------------------

        result["name"] = (
            visa_image_fields.get(
                "name"
            )
        )

        result["document_number"] = (
            visa_image_fields.get(
                "document_number"
            )
        )

        result["nationality"] = (
            visa_image_fields.get(
                "nationality"
            )
        )

        result["date_of_birth"] = (
            visa_image_fields.get(
                "date_of_birth"
            )
        )

        result["gender"] = (
            visa_image_fields.get(
                "gender"
            )
        )

        result["expiry_date"] = (
            visa_image_fields.get(
                "expiry_date"
            )
        )

        # ----------------------------------------------------
        # NAME FALLBACK
        # ----------------------------------------------------

        if not result["name"]:

            mrz_name = extract_visa_mrz_name(
                result["raw_text"]
            )

            if mrz_name:
                result["name"] = mrz_name

        # ----------------------------------------------------
        # NAME FALLBACK 2
        # ----------------------------------------------------

        if not result["name"]:

            result["name"] = extract_generic_name(
                result["raw_text"]
            )

        # ----------------------------------------------------
        # PASSPORT NUMBER FALLBACK
        # ----------------------------------------------------

        if not result["document_number"]:

            passport_number = (
                extract_passport_number(
                    result["raw_text"]
                )
            )

            if passport_number:

                result["document_number"] = (
                    passport_number
                )

        # ----------------------------------------------------
        # NATIONALITY FALLBACK
        # ----------------------------------------------------

        if not result["nationality"]:

            result["nationality"] = (
                extract_nationality(
                    result["raw_text"]
                )
            )

        # ----------------------------------------------------
        # GENDER FALLBACK
        # ----------------------------------------------------

        if not result["gender"]:

            result["gender"] = extract_gender(
                result["raw_text"]
            )

        # ----------------------------------------------------
        # DOB FALLBACK
        #
        # IMPORTANT:
        #
        # We DO NOT use the first generic date here.
        #
        # That was the source of the problem where:
        #
        #     30MAR2023
        #
        # was being treated as DOB.
        #
        # We only accept a date if it is explicitly associated
        # with Birth Date.
        # ----------------------------------------------------

        if not result["date_of_birth"]:

            layout_upper = normalize_ocr_text(
                visa_layout_text
            )

            birth_patterns = [

                r"BIRTH\s*DATE"
                r"[^\n]{0,100}?"
                r"(\d{2}[A-Z]{3}\d{4})",

                r"BIRTH\s*DATE"
                r"[^\n]{0,100}?"
                r"(\d{2}[-/.]\d{2}[-/.]\d{4})",

                r"BIRTH\s*DATE"
                r"[^\n]{0,150}?"
                r"(\d{2}\s+[A-Z]{3}\s+\d{4})",
            ]

            for pattern in birth_patterns:

                match = re.search(
                    pattern,
                    layout_upper,
                    re.IGNORECASE
                )

                if match:

                    result["date_of_birth"] = (
                        normalize_visa_date(
                            match.group(1)
                        )
                    )

                    break

        # ----------------------------------------------------
        # EXPIRY FALLBACK
        #
        # Only search near Expiration/Expiry.
        # Never use "last date" or "first date" for visas.
        # ----------------------------------------------------

        if not result["expiry_date"]:

            layout_upper = normalize_ocr_text(
                visa_layout_text
            )

            expiry_patterns = [

                r"EXPIRATION\s*DATE"
                r"[^\n]{0,100}?"
                r"(\d{2}[A-Z]{3}\d{4})",

                r"EXPIRATION\s*DATE"
                r"[^\n]{0,100}?"
                r"(\d{2}[-/.]\d{2}[-/.]\d{4})",

                r"EXPIRATION\s*DATE"
                r"[^\n]{0,150}?"
                r"(\d{2}\s+[A-Z]{3}\s+\d{4})",

                r"EXPIRY\s*DATE"
                r"[^\n]{0,100}?"
                r"(\d{2}[A-Z]{3}\d{4})",
            ]

            for pattern in expiry_patterns:

                match = re.search(
                    pattern,
                    layout_upper,
                    re.IGNORECASE
                )

                if match:

                    result["expiry_date"] = (
                        normalize_visa_date(
                            match.group(1)
                        )
                    )

                    break

        # ----------------------------------------------------
        # FINAL VISA DATE NORMALIZATION
        # ----------------------------------------------------

        if result["date_of_birth"]:

            result["date_of_birth"] = (
                normalize_visa_date(
                    result["date_of_birth"]
                )
            )

        if result["expiry_date"]:

            result["expiry_date"] = (
                normalize_visa_date(
                    result["expiry_date"]
                )
            )

    # ========================================================
    # TRAVEL PERMIT
    # ========================================================

    elif detected_type == "travel permit":

        result["name"] = extract_generic_name(
            combined_text
        )

        result["gender"] = extract_gender(
            combined_text
        )

        result["date_of_birth"] = (
            extract_date_of_birth(
                combined_text
            )
        )

        result["expiry_date"] = (
            extract_expiry_date(
                combined_text
            )
        )

        permit_patterns = [

            r"(?:TRAVEL\s*PERMIT|PERMIT)"
            r"\s*(?:NO|NUMBER)?\s*[:\-]?\s*"
            r"([A-Z0-9\-]{5,30})"
        ]

        for pattern in permit_patterns:

            match = re.search(
                pattern,
                combined_text,
                re.IGNORECASE
            )

            if match:

                result["document_number"] = (
                    match.group(1).strip()
                )

                break

        result["nationality"] = (
            extract_nationality(
                combined_text
            )
        )

    # ========================================================
    # NATIONAL ID
    # ========================================================

    elif detected_type == "national id":

        result["name"] = extract_generic_name(
            combined_text
        )

        result["gender"] = extract_gender(
            combined_text
        )

        result["date_of_birth"] = (
            extract_date_of_birth(
                combined_text
            )
        )

        result["expiry_date"] = (
            extract_expiry_date(
                combined_text
            )
        )

        result["nationality"] = (
            extract_nationality(
                combined_text
            )
        )

        id_patterns = [

            r"(?:ID\s*(?:NO|NUMBER)|IDENTITY\s*(?:NO|NUMBER))"
            r"\s*[:\-]?\s*([A-Z0-9\-]{5,30})"
        ]

        for pattern in id_patterns:

            match = re.search(
                pattern,
                combined_text,
                re.IGNORECASE
            )

            if match:

                result["document_number"] = (
                    match.group(1).strip()
                )

                break

    # ========================================================
    # UNKNOWN DOCUMENT
    # ========================================================

    else:

        result["name"] = extract_generic_name(
            combined_text
        )

        result["gender"] = extract_gender(
            combined_text
        )

        result["date_of_birth"] = (
            extract_date_of_birth(
                combined_text
            )
        )

        result["expiry_date"] = (
            extract_expiry_date(
                combined_text
            )
        )

        result["nationality"] = (
            extract_nationality(
                combined_text
            )
        )

    # ========================================================
    # FINAL CLEANUP
    # ========================================================

    for key in [
        "name",
        "document_number",
        "nationality",
        "date_of_birth",
        "gender",
        "expiry_date",
        "address",
    ]:

        value = result.get(key)

        if isinstance(value, str):

            value = value.strip()

            if not value:
                value = None

            result[key] = value

    return result


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " OCR DOCUMENT EXTRACTION TEST"
    )

    print(
        "========================================\n"
    )

    image_path = input(
        "Enter image path: "
    ).strip().strip('"')

    if not image_path:

        print(
            "No image path provided."
        )

        raise SystemExit

    extracted = extract_document_fields(
        image_path
    )

    print(
        "\n========== EXTRACTED FIELDS ==========\n"
    )

    for key, value in extracted.items():

        if key == "raw_text":
            continue

        print(
            f"{key:20}: {value}"
        )

    print(
        "\n========== RAW OCR TEXT ==========\n"
    )

    print(
        extracted.get(
            "raw_text",
            ""
        )
    )

    print(
        "\n========================================"
    )