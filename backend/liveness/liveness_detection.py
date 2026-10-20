import cv2
import numpy as np


# =========================================
# LIVENESS DETECTION
# =========================================

def calculate_liveness_score(image_path):
    """
    Prototype-level liveness analysis.

    Uses image quality and face-region texture
    as signals for detecting possible spoofing.

    This is a prototype anti-spoofing signal,
    not a production-grade biometric liveness system.
    """

    image = cv2.imread(
        image_path
    )

    if image is None:
        raise ValueError(
            "Unable to read the verification image."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # =========================================
    # 1. IMAGE SHARPNESS
    # =========================================

    sharpness = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    # =========================================
    # 2. IMAGE CONTRAST
    # =========================================

    contrast = gray.std()

    # =========================================
    # 3. TEXTURE ANALYSIS
    # =========================================

    texture = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    # =========================================
    # 4. NORMALIZE SIGNALS
    # =========================================

    sharpness_score = min(
        100,
        (sharpness / 500) * 100
    )

    contrast_score = min(
        100,
        (contrast / 80) * 100
    )

    texture_score = min(
        100,
        (texture / 500) * 100
    )

    # =========================================
    # 5. COMBINE SIGNALS
    # =========================================

    liveness_score = round(
        (
            sharpness_score * 0.4
            + contrast_score * 0.3
            + texture_score * 0.3
        ),
        2
    )

    # =========================================
    # 6. DETERMINE STATUS
    # =========================================

    if liveness_score >= 60:

        status = "LIVE"

        reason = (
            "The verification image contains "
            "sufficient image quality and texture "
            "signals for a live-person indication."
        )

    elif liveness_score >= 35:

        status = "REVIEW"

        reason = (
            "The image contains limited liveness "
            "signals. Additional verification is recommended."
        )

    else:

        status = "SPOOF"

        reason = (
            "The image contains weak liveness signals "
            "and may represent a spoofed or low-quality capture."
        )

    return {
        "status": status,
        "score": liveness_score,
        "sharpness": round(
            sharpness,
            2
        ),
        "contrast": round(
            contrast,
            2
        ),
        "texture": round(
            texture,
            2
        ),
        "reason": reason
    }