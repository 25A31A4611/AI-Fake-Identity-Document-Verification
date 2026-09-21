import cv2
import os


def analyze_national_id(image_path):
    """
    Prototype forensic analysis for a synthetic National ID.

    Checks basic image properties that may indicate
    possible document manipulation.

    This does NOT prove that a document is fake.
    """

    results = []

    # Check whether the image can be opened
    image = cv2.imread(image_path)

    if image is None:
        results.append({
            "check": "Image Readability",
            "status": "FAIL",
            "message": "The uploaded document image could not be read."
        })

        return results

    # --------------------------------------------------
    # IMAGE QUALITY CHECK
    # --------------------------------------------------

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sharpness = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    if sharpness < 50:

        results.append({
            "check": "Image Quality",
            "status": "REVIEW",
            "message": "The document image appears blurry or low quality."
        })

    else:

        results.append({
            "check": "Image Quality",
            "status": "PASS",
            "message": "Document image quality is sufficient for basic analysis."
        })

    # --------------------------------------------------
    # EDGE / DOCUMENT STRUCTURE CHECK
    # --------------------------------------------------

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = cv2.countNonZero(edges)

    total_pixels = edges.shape[0] * edges.shape[1]

    edge_ratio = edge_pixels / total_pixels

    if edge_ratio < 0.01:

        results.append({
            "check": "Document Structure",
            "status": "REVIEW",
            "message": "Document structure could not be confidently analyzed."
        })

    else:

        results.append({
            "check": "Document Structure",
            "status": "PASS",
            "message": "Document contains detectable visual structure."
        })

    # --------------------------------------------------
    # METADATA CHECK
    # --------------------------------------------------

    file_extension = os.path.splitext(
        image_path
    )[1].lower()

    if file_extension in [".jpg", ".jpeg", ".png"]:

        results.append({
            "check": "File Format",
            "status": "PASS",
            "message": "Supported image format detected."
        })

    else:

        results.append({
            "check": "File Format",
            "status": "REVIEW",
            "message": "File format requires additional review."
        })

    # --------------------------------------------------
    # FINAL FORENSIC STATUS
    # --------------------------------------------------

    has_fail = any(
        result["status"] == "FAIL"
        for result in results
    )

    has_review = any(
        result["status"] == "REVIEW"
        for result in results
    )

    if has_fail:

        final_status = "FAIL"

        final_message = (
            "Forensic analysis could not be completed successfully."
        )

    elif has_review:

        final_status = "REVIEW"

        final_message = (
            "Some visual characteristics require officer review."
        )

    else:

        final_status = "PASS"

        final_message = (
            "Basic forensic checks completed successfully."
        )

    results.append({
        "check": "Overall Forensic Screening",
        "status": final_status,
        "message": final_message
    })

    return results