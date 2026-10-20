import os

import cv2
import numpy as np

from PIL import Image


def calculate_ela_score(image_path):
    """
    Prototype-level Error Level Analysis (ELA).

    ELA compares the uploaded image with a JPEG
    recompressed version to identify unusual
    pixel-level differences.

    This is a forensic signal, not proof of forgery.
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    # Temporary JPEG used for ELA comparison
    temp_path = image_path + "_ela_temp.jpg"

    image.save(
        temp_path,
        "JPEG",
        quality=90
    )

    recompressed = Image.open(
        temp_path
    ).convert("RGB")

    original_array = np.array(
        image
    ).astype(np.int16)

    recompressed_array = np.array(
        recompressed
    ).astype(np.int16)

    # Calculate pixel difference
    difference = np.abs(
        original_array
        - recompressed_array
    )

    # Convert RGB difference to grayscale
    difference_gray = np.mean(
        difference,
        axis=2
    )

    # Average error level
    mean_error = np.mean(
        difference_gray
    )

    # Identify unusually high-error pixels
    threshold = max(
        mean_error * 2.5,
        15
    )

    suspicious_pixels = (
        difference_gray > threshold
    )

    suspicious_ratio = (
        np.mean(
            suspicious_pixels
        ) * 100
    )

    # Convert to 0–100 score
    ela_score = min(
        100,
        int(
            suspicious_ratio * 5
        )
    )

    # Remove temporary file
    if os.path.exists(
        temp_path
    ):
        os.remove(
            temp_path
        )

    return (
        ela_score,
        suspicious_ratio
    )


def calculate_image_consistency(image_path):
    """
    Perform basic image consistency analysis
    using OpenCV.

    Signals:
    - Edge concentration
    - Image detail/sharpness

    These signals support the tampering analysis
    but do not independently prove manipulation.
    """

    image = cv2.imread(
        image_path
    )

    if image is None:
        raise ValueError(
            "Unable to read the uploaded document image."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Edge detection
    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_ratio = (
        np.count_nonzero(edges)
        / edges.size
    )

    # Image detail/sharpness
    laplacian_variance = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return {
        "edge_ratio": edge_ratio,
        "laplacian_variance": laplacian_variance
    }


def detect_tampering(image_path):
    """
    Main tampering detection function.

    Returns a dictionary that can be passed
    directly to the Flask template.
    """

    if not os.path.exists(
        image_path
    ):
        raise FileNotFoundError(
            "Uploaded document was not found."
        )

    # =========================================
    # 1. ELA ANALYSIS
    # =========================================

    ela_score, suspicious_ratio = (
        calculate_ela_score(
            image_path
        )
    )

    # =========================================
    # 2. IMAGE CONSISTENCY ANALYSIS
    # =========================================

    consistency = (
        calculate_image_consistency(
            image_path
        )
    )

    edge_ratio = consistency[
        "edge_ratio"
    ]

    laplacian_variance = consistency[
        "laplacian_variance"
    ]

    # =========================================
    # 3. INITIAL RISK SCORE
    # =========================================

    risk_score = ela_score

    reasons = []

    # -----------------------------------------
    # ELA SIGNAL
    # -----------------------------------------

    if ela_score >= 70:

        reasons.append(
            "Significant recompression differences detected in the document image."
        )

    elif ela_score >= 40:

        reasons.append(
            "Moderate image-level inconsistencies detected."
        )

    else:

        reasons.append(
            "No significant ELA inconsistencies detected."
        )

    # -----------------------------------------
    # EDGE ANALYSIS
    # -----------------------------------------

    if edge_ratio > 0.25:

        risk_score += 10

        reasons.append(
            "High edge concentration detected in parts of the document."
        )

    # -----------------------------------------
    # IMAGE QUALITY
    # -----------------------------------------

    if laplacian_variance < 50:

        reasons.append(
            "Document image quality is relatively low; forensic confidence may be reduced."
        )

    # Keep score between 0 and 100
    risk_score = min(
        100,
        int(risk_score)
    )

    # =========================================
    # 4. FINAL STATUS
    # =========================================

    if risk_score >= 70:

        status = "HIGH RISK"

    elif risk_score >= 40:

        status = "MEDIUM RISK"

    else:

        status = "LOW RISK"

    # =========================================
    # 5. RETURN RESULT
    # =========================================

    return {
        "status": status,
        "score": risk_score,

        "ela_score": ela_score,

        "suspicious_ratio": round(
            suspicious_ratio,
            2
        ),

        "edge_ratio": round(
            edge_ratio * 100,
            2
        ),

        "laplacian_variance": round(
            laplacian_variance,
            2
        ),

        "reasons": reasons
    }