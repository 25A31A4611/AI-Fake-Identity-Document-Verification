from flask import Flask, render_template, request, session
import os
import json
from werkzeug.utils import secure_filename

from ai.ocr import extract_text
from ai.paSSport_parSer import extract_passport_fields
from ai.validator import validate_passport
from ai.forenSicS import analyze_document
from ai.face_verification import detect_faces
from ai.face_compariSon import compare_faces

from ai.viSa_parSer import extract_visa_fields
from ai.viSa_validator import validate_visa
from ai.croSS_document import compare_documents

from ai.national_id_parSer import extract_national_id_fields
from ai.national_id_validator import validate_national_id
from ai.national_id_forenSicS import analyze_national_id

from databaSe.reference_db import check_reference_database


app = Flask(__name__)


# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = "sih-ai-screen-demo-secret"


# =========================================================
# APP CONFIGURATION
# =========================================================

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

UPLOAD_FOLDER = "uploads"

PASSPORT_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "passports"
)

VISA_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "visas"
)

NATIONAL_ID_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "national_id"
)

REFERENCE_FOLDER = os.path.join(
    "demo_data",
    "reference"
)


# =========================================================
# CREATE UPLOAD FOLDERS
# =========================================================

os.makedirs(
    PASSPORT_FOLDER,
    exist_ok=True
)

os.makedirs(
    VISA_FOLDER,
    exist_ok=True
)

os.makedirs(
    NATIONAL_ID_FOLDER,
    exist_ok=True
)


# =========================================================
# PASSPORT RISK CALCULATION
# =========================================================

def calculate_passport_risk(
    validation_results,
    forensic_results,
    face_result
):

    score = 0
    reasons = []

    # -----------------------------------------------------
    # Validation results
    # -----------------------------------------------------

    for result in validation_results:

        status = result.get(
            "status",
            ""
        ).upper()

        check = result.get(
            "check",
            "Validation check"
        )

        if status == "FAIL":

            score += 25

            reasons.append(
                check + " failed."
            )

        elif status == "WARNING":

            score += 10

            reasons.append(
                check + " requires review."
            )

        elif status == "REVIEW":

            score += 15

            reasons.append(
                check + " requires additional review."
            )

    # -----------------------------------------------------
    # Forensic results
    # -----------------------------------------------------

    for result in forensic_results:

        status = result.get(
            "status",
            ""
        ).upper()

        check = result.get(
            "check",
            "Forensic check"
        )

        if status == "FAIL":

            score += 30

            reasons.append(
                check + " failed."
            )

        elif status == "REVIEW":

            score += 15

            reasons.append(
                check + " requires review."
            )

        elif status == "WARNING":

            score += 10

            reasons.append(
                check + " produced a warning."
            )

    # -----------------------------------------------------
    # Face detection
    # -----------------------------------------------------

    face_status = face_result.get(
        "status",
        ""
    ).upper()

    face_count = face_result.get(
        "face_count",
        0
    )

    if face_status == "FAIL":

        score += 25

        reasons.append(
            "Face detection failed."
        )

    elif face_count == 0:

        score += 20

        reasons.append(
            "No face detected."
        )

    elif face_count > 1:

        score += 15

        reasons.append(
            "Multiple faces detected."
        )

    # -----------------------------------------------------
    # Limit score
    # -----------------------------------------------------

    if score > 100:
        score = 100

    # -----------------------------------------------------
    # Risk level
    # -----------------------------------------------------

    if score < 30:

        level = "LOW"

    elif score < 60:

        level = "MEDIUM"

    else:

        level = "HIGH"

    # -----------------------------------------------------
    # Default reason
    # -----------------------------------------------------

    if not reasons:

        reasons.append(
            "No major risk signals detected "
            "in the prototype screening."
        )

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login")
def login():

    return render_template(
        "login.html"
    )


# =========================================================
# HUMAN CHECK
# =========================================================

@app.route("/human-check")
def human_check():

    return render_template(
        "human_check.html"
    )


# =========================================================
# OVERRIDE
# =========================================================

@app.route("/override")
def override():

    return render_template(
        "override.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# =========================================================
# AIRPORT SECURITY
# =========================================================

@app.route("/airport")
def airport():

    return render_template(
        "airport_screening.html"
    )


# =========================================================
# PASSPORT SCREENING
# =========================================================

@app.route(
    "/passport",
    methods=["GET", "POST"]
)
def passport():

    # -----------------------------------------------------
    # GET request
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "passport.html"
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if "passport" not in request.files:

        return "No passport file uploaded."

    file = request.files["passport"]

    if file.filename == "":

        return "No passport file selected."

    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        PASSPORT_FOLDER,
        filename
    )

    file.save(filepath)

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    ocr_text = extract_text(
        filepath
    )

    print("")
    print("==========================================")
    print("           PASSPORT OCR TEXT")
    print("==========================================")
    print(ocr_text)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Passport field extraction
    # -----------------------------------------------------

    passport_fields = extract_passport_fields(
        ocr_text
    )

    print("")
    print("==========================================")
    print("        PASSPORT EXTRACTED FIELDS")
    print("==========================================")
    print(passport_fields)
    print("==========================================")
    print("")

    # =====================================================
    # SAVE PASSPORT INFORMATION
    # FOR CROSS-DOCUMENT ANALYSIS
    # =====================================================

    reference_file = os.path.join(
        UPLOAD_FOLDER,
        "passport_reference.json"
    )

    try:

        with open(
            reference_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                passport_fields,
                f,
                indent=4
            )

        print(
            "Passport reference information saved."
        )

    except Exception as e:

        print(
            "Could not save passport reference:",
            e
        )

    # -----------------------------------------------------
    # Passport validation
    # -----------------------------------------------------

    validation_results = validate_passport(
        passport_fields
    )

    # -----------------------------------------------------
    # Forensic analysis
    # -----------------------------------------------------

    forensic_results = analyze_document(
        filepath
    )

    # -----------------------------------------------------
    # Face detection
    # -----------------------------------------------------

    face_result = detect_faces(
        filepath
    )

    # -----------------------------------------------------
    # Risk calculation
    # -----------------------------------------------------

    risk_result = calculate_passport_risk(
        validation_results,
        forensic_results,
        face_result
    )

    # -----------------------------------------------------
    # Result page
    # -----------------------------------------------------

    return render_template(
        "upload_result.html",

        filename=filename,

        ocr_text=ocr_text,

        passport_fields=passport_fields,

        validation_results=validation_results,

        forensic_results=forensic_results,

        face_result=face_result,

        risk_result=risk_result
    )


# =========================================================
# VISA SCREENING
# =========================================================

@app.route(
    "/visa",
    methods=["GET", "POST"]
)
def visa():

    # -----------------------------------------------------
    # GET request
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "visa.html"
        )

    # -----------------------------------------------------
    # Check uploaded file
    # -----------------------------------------------------

    if "visa" not in request.files:

        return "No visa file uploaded."

    file = request.files["visa"]

    if file.filename == "":

        return "No visa file selected."

    # -----------------------------------------------------
    # Save visa file
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        VISA_FOLDER,
        filename
    )

    file.save(filepath)

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    ocr_text = extract_text(
        filepath
    )

    print("")
    print("==========================================")
    print("             VISA OCR TEXT")
    print("==========================================")
    print(ocr_text)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Extract visa fields
    # -----------------------------------------------------

    visa_fields = extract_visa_fields(
        ocr_text
    )

    print("")
    print("==========================================")
    print("          VISA EXTRACTED FIELDS")
    print("==========================================")
    print(visa_fields)
    print("==========================================")
    print("")

    # =====================================================
    # LOAD PREVIOUSLY SCREENED PASSPORT
    # =====================================================

    reference_file = os.path.join(
        UPLOAD_FOLDER,
        "passport_reference.json"
    )

    passport_reference = None

    if os.path.exists(reference_file):

        try:

            with open(
                reference_file,
                "r",
                encoding="utf-8"
            ) as f:

                passport_reference = json.load(f)

            print("")
            print("==========================================")
            print("       PASSPORT REFERENCE LOADED")
            print("==========================================")
            print(passport_reference)
            print("==========================================")
            print("")

        except Exception as e:

            print(
                "Could not load passport reference:",
                e
            )

            passport_reference = None

    else:

        print(
            "No passport_reference.json found."
        )

    # =====================================================
    # CROSS-DOCUMENT ANALYSIS
    # =====================================================

    if passport_reference:

        cross_document_result = compare_documents(
            passport_reference,
            visa_fields
        )

    else:

        cross_document_result = [

            {
                "check": "Passport ↔ Visa Consistency",

                "status": "WARNING",

                "message": (
                    "No passport screening data is available. "
                    "Please screen a passport first."
                )
            }

        ]

    print("")
    print("==========================================")
    print("       CROSS-DOCUMENT ANALYSIS")
    print("==========================================")
    print(cross_document_result)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Validate visa
    # -----------------------------------------------------

    visa_validation_results = validate_visa(
        visa_fields
    )

    print("")
    print("==========================================")
    print("          VISA VALIDATION RESULTS")
    print("==========================================")
    print(visa_validation_results)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Result page
    # -----------------------------------------------------

    return render_template(
        "visa_result.html",

        filename=filename,

        ocr_text=ocr_text,

        visa_fields=visa_fields,

        visa_validation_results=visa_validation_results,

        cross_document_result=cross_document_result
    )


# =========================================================
# NATIONAL ID SCREENING
# =========================================================

@app.route(
    "/national-id",
    methods=["GET", "POST"]
)
def national_id():

    # -----------------------------------------------------
    # GET request
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "national_id.html"
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if "national_id" not in request.files:

        return "No National ID file uploaded."

    file = request.files["national_id"]

    if file.filename == "":

        return "No National ID file selected."

    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        NATIONAL_ID_FOLDER,
        filename
    )

    file.save(filepath)

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    ocr_text = extract_text(
        filepath
    )

    print("")
    print("==========================================")
    print("        NATIONAL ID OCR TEXT")
    print("==========================================")
    print(ocr_text)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Extract fields
    # -----------------------------------------------------

    national_id_fields = extract_national_id_fields(
        ocr_text
    )

    print("")
    print("==========================================")
    print("      NATIONAL ID EXTRACTED FIELDS")
    print("==========================================")
    print(national_id_fields)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    national_id_validation_results = validate_national_id(
        national_id_fields
    )

    # -----------------------------------------------------
    # Forensics
    # -----------------------------------------------------

    national_id_forensic_results = analyze_national_id(
        filepath
    )

    # -----------------------------------------------------
    # Face detection
    # -----------------------------------------------------

    face_result = detect_faces(
        filepath
    )

    # =====================================================
    # FACE COMPARISON
    # =====================================================

    reference_face_path = os.path.join(
        REFERENCE_FOLDER,
        "reference_face.jpg"
    )

    if os.path.exists(reference_face_path):

        face_comparison_result = compare_faces(
            filepath,
            reference_face_path
        )

    else:

        face_comparison_result = {
            "status": "WARNING",
            "match": False,
            "similarity": 0,
            "message": (
                "Reference face image was not found."
            )
        }

    print("")
    print("==========================================")
    print("        FACE COMPARISON RESULT")
    print("==========================================")
    print(face_comparison_result)
    print("==========================================")
    print("")

    # -----------------------------------------------------
    # Synthetic reference database
    # -----------------------------------------------------

    reference_result = check_reference_database(
        national_id_fields
    )

    # -----------------------------------------------------
    # Result page
    # -----------------------------------------------------

    return render_template(
        "national_id_result.html",

        filename=filename,

        ocr_text=ocr_text,

        national_id_fields=national_id_fields,

        national_id_validation_results=(
            national_id_validation_results
        ),

        national_id_forensic_results=(
            national_id_forensic_results
        ),

        face_result=face_result,

        face_comparison_result=face_comparison_result,

        reference_result=reference_result
    )


# =========================================================
# TRAFFIC ENFORCEMENT
# =========================================================

@app.route("/traffic")
def traffic():

    return """
    <h1>Traffic Enforcement</h1>

    <p>
        Driving License • RC • Pollution Certificate
    </p>

    <a href="/dashboard">
        Back to Dashboard
    </a>
    """


# =========================================================
# BANKING
# =========================================================

@app.route("/banking")
def banking():

    return """
    <h1>Banking</h1>

    <p>
        Customer Identity • Documents
    </p>

    <a href="/dashboard">
        Back to Dashboard
    </a>
    """


# =========================================================
# BORDER INTEGRITY
# =========================================================

@app.route("/border")
def border():

    return """
    <h1>Border Integrity</h1>

    <p>
        Travel Documents • Identity
    </p>

    <a href="/dashboard">
        Back to Dashboard
    </a>
    """


# =========================================================
# GOVERNMENT SERVICES
# =========================================================

@app.route("/government")
def government():

    return """
    <h1>Government Services</h1>

    <p>
        Identity • Certificates • Documents
    </p>

    <a href="/dashboard">
        Back to Dashboard
    </a>
    """


# =========================================================
# START FLASK SERVER
# =========================================================

if __name__ == "__main__":

    print("")
    print("==========================================")
    print("     AI IDENTITY SCREENING SYSTEM")
    print("     Flask Server Starting...")
    print("==========================================")
    print("")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )