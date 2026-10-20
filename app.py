import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename

from backend.ocr.field_extraction import (
    extract_document_fields
)

from backend.validation.document_validation import (
    validate_document
)

from backend.tampering.tampering_detection import (
    detect_tampering
)

from backend.face.face_verification import (
    compare_faces
)

from backend.risk.risk_engine import (
    calculate_risk
)

from backend.liveness.liveness_detection import (
    calculate_liveness_score
)

from backend.registry.database import (
    initialize_database
)

from backend.registry.document_registry import (
    verify_document,
    save_verification_history
)

from backend.verification.cross_document import (
    compare_documents
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


app.config["SECRET_KEY"] = "identityguard-demo-secret-key"


# Maximum upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Create upload folder automatically
os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        officer_id = request.form.get(
            "officer_id"
        )

        password = request.form.get(
            "password"
        )

        # Prototype login
        if officer_id and password:

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Please enter Officer ID and Password."
        )

    return render_template(
        "login.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# ============================================================
# IMMIGRATION VERIFICATION
# ============================================================

@app.route("/immigration")
def immigration():

    return render_template(
        "immigration.html"
    )


# ============================================================
# TRAFFIC VERIFICATION
# ============================================================

@app.route("/traffic")
def traffic():

    return render_template(
        "traffic.html"
    )


# ============================================================
# BANKING & KYC
# ============================================================

@app.route("/kyc")
def kyc():

    return render_template(
        "kyc.html"
    )

# ============================================================
# BORDER CHECKPOINT
# ============================================================

@app.route("/border")
def border():

    return render_template(
        "border.html"
    )


# ============================================================
# UPLOAD PAGE
# ============================================================

@app.route(
    "/upload/<document_type>"
)
def upload(document_type):

    return render_template(
        "upload.html",
        document_type=document_type
    )


# ============================================================
# PROCESS UPLOAD
# REAL OCR PROCESSING
# ============================================================

@app.route(
    "/process-upload",
    methods=["POST"]
)
def process_upload():

    # ========================================================
    # GET DOCUMENT TYPE
    # ========================================================

    document_type = request.form.get(
        "document_type"
    )


    # ========================================================
    # GET UPLOADED FILES
    # ========================================================

    document = request.files.get(
        "document"
    )

    face_photo = request.files.get(
        "face_photo"
    )


    # ========================================================
    # OPTIONAL SECOND DOCUMENT
    #
    # Used for cross-document consistency checking.
    # ========================================================

    comparison_document = request.files.get(
        "comparison_document"
    )

    comparison_document_type = request.form.get(
        "comparison_document_type"
    )


    # ========================================================
    # DOCUMENT VALIDATION
    # ========================================================

    if (
        not document
        or not document.filename
    ):

        flash(
            "Please upload a document."
        )

        return redirect(
            url_for(
                "upload",
                document_type=document_type
            )
        )


    if not allowed_file(
        document.filename
    ):

        flash(
            "Invalid document file type. "
            "Only PNG, JPG and JPEG are allowed."
        )

        return redirect(
            url_for(
                "upload",
                document_type=document_type
            )
        )


    # ========================================================
    # SECURE DOCUMENT FILENAME
    # ========================================================

    original_filename = secure_filename(
        document.filename
    )

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()


    # Generate unique filename
    document_filename = (
        f"document_{uuid.uuid4().hex}.{extension}"
    )


    document_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        document_filename
    )


    # ========================================================
    # SAVE DOCUMENT
    # ========================================================

    document.save(
        document_path
    )


    # ========================================================
    # RUN REAL OCR
    # ========================================================

    try:

        extracted_data = (
            extract_document_fields(
                document_path
            )
        )

    except Exception as error:

        # Remove uploaded file if OCR fails
        if os.path.exists(
            document_path
        ):
            os.remove(
                document_path
            )

        flash(
            f"OCR processing failed: {error}"
        )

        return redirect(
            url_for(
                "upload",
                document_type=document_type
            )
        )


    # ========================================================
    # CROSS-DOCUMENT VERIFICATION
    #
    # This is the new feature.
    #
    # The first document is always processed normally.
    # If a second document is supplied, it is also processed
    # using the same real OCR engine.
    # ========================================================

    cross_document_result = {
        "status": "REVIEW",
        "message": (
            "A second document was not provided. "
            "Cross-document comparison was not performed."
        ),
        "documents_checked": 1,
        "matched_fields": [],
        "mismatched_fields": [],
        "risk_points": 0
    }


    comparison_document_filename = None
    comparison_document_path = None
    comparison_extracted_data = None


    # ========================================================
    # PROCESS SECOND DOCUMENT IF PROVIDED
    # ========================================================

    if (
        comparison_document
        and comparison_document.filename
    ):

        # Validate second document file type
        if not allowed_file(
            comparison_document.filename
        ):

            # Remove primary document because the
            # complete upload request is invalid.
            if os.path.exists(
                document_path
            ):
                os.remove(
                    document_path
                )

            flash(
                "Invalid comparison document file type. "
                "Only PNG, JPG and JPEG are allowed."
            )

            return redirect(
                url_for(
                    "upload",
                    document_type=document_type
                )
            )


        # ----------------------------------------------------
        # Secure second document filename
        # ----------------------------------------------------

        comparison_original_filename = secure_filename(
            comparison_document.filename
        )

        comparison_extension = (
            comparison_original_filename.rsplit(
                ".",
                1
            )[1].lower()
        )


        comparison_document_filename = (
            f"comparison_{uuid.uuid4().hex}."
            f"{comparison_extension}"
        )


        comparison_document_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            comparison_document_filename
        )


        # ----------------------------------------------------
        # Save second document
        # ----------------------------------------------------

        comparison_document.save(
            comparison_document_path
        )


        # ----------------------------------------------------
        # Run REAL OCR on second document
        # ----------------------------------------------------

        try:

            comparison_extracted_data = (
                extract_document_fields(
                    comparison_document_path
                )
            )

        except Exception as error:

            # Remove both files if second OCR fails
            if os.path.exists(
                document_path
            ):
                os.remove(
                    document_path
                )

            if os.path.exists(
                comparison_document_path
            ):
                os.remove(
                    comparison_document_path
                )

            flash(
                f"Comparison document OCR processing failed: {error}"
            )

            return redirect(
                url_for(
                    "upload",
                    document_type=document_type
                )
            )


        # ----------------------------------------------------
        # Prepare data for cross-document comparison
        #
        # Your cross_document.py expects:
        #
        # full_name
        # date_of_birth
        # gender
        # nationality
        #
        # OCR currently uses fields such as:
        # name / dob
        #
        # Therefore we map the existing OCR output into
        # the comparison module without changing the OCR logic.
        # ----------------------------------------------------

        primary_comparison_data = {

            "document_type": document_type,

            "document_number": extracted_data.get(
                "document_number"
            ),

            "full_name": extracted_data.get(
                "full_name",
                extracted_data.get("name")
            ),

            "date_of_birth": extracted_data.get(
                "date_of_birth",
                extracted_data.get("dob")
            ),

            "gender": extracted_data.get(
                "gender"
            ),

            "nationality": extracted_data.get(
                "nationality"
            )
        }


        comparison_comparison_data = {

            "document_type": (
                comparison_document_type
                or "comparison document"
            ),

            "document_number": comparison_extracted_data.get(
                "document_number"
            ),

            "full_name": comparison_extracted_data.get(
                "full_name",
                comparison_extracted_data.get("name")
            ),

            "date_of_birth": comparison_extracted_data.get(
                "date_of_birth",
                comparison_extracted_data.get("dob")
            ),

            "gender": comparison_extracted_data.get(
                "gender"
            ),

            "nationality": comparison_extracted_data.get(
                "nationality"
            )
        }


        # ----------------------------------------------------
        # REAL CROSS-DOCUMENT COMPARISON
        # ----------------------------------------------------

        try:

            cross_document_result = compare_documents(
                [
                    primary_comparison_data,
                    comparison_comparison_data
                ]
            )

        except Exception as error:

            cross_document_result = {
                "status": "REVIEW",
                "message": (
                    "Cross-document comparison could not "
                    f"be completed: {error}"
                ),
                "documents_checked": 2,
                "matched_fields": [],
                "mismatched_fields": [],
                "risk_points": 0
            }


    # ========================================================
    # DOCUMENT REGISTRY VERIFICATION
    # ========================================================

    registry_result = verify_document({

        **extracted_data,

        "document_type": document_type,

        "full_name": extracted_data.get(
            "name"
        )
    })


    # ========================================================
    # DOCUMENT VALIDATION
    # ========================================================

    validation_result = validate_document(
        extracted_data,
        document_type,
        document_path
    )


    # ========================================================
    # TAMPERING DETECTION
    # ========================================================

    try:

        tampering_result = detect_tampering(
            document_path
        )

    except Exception as error:

        tampering_result = {
            "status": "REVIEW",
            "score": 50,
            "ela_score": 0,
            "suspicious_ratio": 0,
            "edge_ratio": 0,
            "laplacian_variance": 0,
            "reasons": [
                f"Tampering analysis could not be completed: {error}"
            ]
        }


    # ========================================================
    # OPTIONAL FACE PHOTO
    # ========================================================

    face_filename = None


    if (
        face_photo
        and face_photo.filename
    ):

        if not allowed_file(
            face_photo.filename
        ):

            # Remove document because
            # complete upload is invalid
            if os.path.exists(
                document_path
            ):
                os.remove(
                    document_path
                )

            # Remove comparison document if it exists
            if (
                comparison_document_path
                and os.path.exists(
                    comparison_document_path
                )
            ):
                os.remove(
                    comparison_document_path
                )

            flash(
                "Invalid face image type. "
                "Only PNG, JPG and JPEG are allowed."
            )

            return redirect(
                url_for(
                    "upload",
                    document_type=document_type
                )
            )


        face_original_filename = (
            secure_filename(
                face_photo.filename
            )
        )


        face_extension = (
            face_original_filename.rsplit(
                ".",
                1
            )[1].lower()
        )


        face_filename = (
            f"face_{uuid.uuid4().hex}.{face_extension}"
        )


        face_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            face_filename
        )


        face_photo.save(
            face_path
        )


        # ====================================================
        # FACE VERIFICATION
        # ====================================================

        try:

            face_result = compare_faces(
                document_path,
                face_path
            )

        except Exception as error:

            face_result = {
                "status": "REVIEW",
                "score": 0,
                "match": False,
                "reason": (
                    f"Face verification could not be completed: {error}"
                )
            }

    else:

        face_result = {
            "status": "NOT PROVIDED",
            "score": 0,
            "match": False,
            "reason": (
                "Verification face image was not provided."
            )
        }


    # ========================================================
    # LIVENESS DETECTION
    # ========================================================

    try:

        if face_filename:

            liveness_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                face_filename
            )

            liveness_result = (
                calculate_liveness_score(
                    liveness_path
                )
            )

        else:

            liveness_result = {
                "status": "NOT PROVIDED",
                "score": 0,
                "sharpness": 0,
                "contrast": 0,
                "texture": 0,
                "reason": (
                    "Verification image was not provided."
                )
            }

    except Exception as error:

        liveness_result = {
            "status": "REVIEW",
            "score": 0,
            "sharpness": 0,
            "contrast": 0,
            "texture": 0,
            "reason": (
                f"Liveness analysis could not be completed: {error}"
            )
        }


    # ========================================================
    # AI RISK ASSESSMENT
    #
    # Existing risk engine logic is intentionally unchanged.
    #
    # Cross-document result is passed into the existing risk engine
    # so its risk contribution can be included in the overall risk assessment.
    # ========================================================

    risk_result = calculate_risk(
        validation_result,
        tampering_result,
        face_result,
        liveness_result,
        registry_result,
        cross_document_result
    )


    # ========================================================
    # ADD CROSS-DOCUMENT INFORMATION TO RISK RESULT
    #
    # Keep the cross-document status and risk contribution
    # available to the results page.
    # ========================================================

    risk_result["cross_document_status"] = (
        cross_document_result.get(
            "status",
            "REVIEW"
        )
    )

    risk_result["cross_document_risk_points"] = (
        cross_document_result.get(
            "risk_points",
            0
        )
    )


    # ========================================================
    # SHOW ANALYSIS PAGE
    # ========================================================

    return render_template(
        "analysis.html",

        document_type=document_type,

        document_filename=document_filename,

        face_filename=face_filename,

        extracted_data=extracted_data,

        validation_result=validation_result,

        registry_result=registry_result,

        tampering_result=tampering_result,

        face_result=face_result,

        liveness_result=liveness_result,

        risk_result=risk_result,

        # ====================================================
        # NEW CROSS-DOCUMENT DATA
        # ====================================================

        cross_document_result=cross_document_result,

        comparison_document_filename=(
            comparison_document_filename
        ),

        comparison_extracted_data=(
            comparison_extracted_data
        )
    )


# ============================================================
# DEMO RESULTS
# ============================================================

@app.route(
    "/demo-results/<document_type>"
)
def demo_results(document_type):

    extracted_data = {

        "name": "DEMO USER",

        "document_number": "DEMO123456",

        "nationality": "INDIA",

        "dob": "01/01/2000",

        "expiry_date": "01/01/2035"

    }


    return render_template(
        "results.html",

        document_type=document_type,

        extracted_data=extracted_data
    )


# ============================================================
# OFFICER DECISION
# ============================================================

@app.route(
    "/decision",
    methods=["POST"]
)
def decision():

    document_type = request.form.get(
        "document_type"
    )

    officer_decision = request.form.get(
        "officer_decision"
    )


    return render_template(
        "decision.html",

        document_type=document_type,

        officer_decision=officer_decision
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
