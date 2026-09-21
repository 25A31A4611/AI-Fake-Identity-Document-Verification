def calculate_risk(
    validation_results,
    forensic_results,
    face_result,
    face_comparison_result=None
):
    """
    Prototype AI-assisted risk scoring engine.

    Combines document validation, forensic,
    face detection and face comparison signals.

    This score assists the authorized officer.
    It does NOT prove that a document is fake.
    """

    score = 0
    reasons = []

    # -----------------------------------------
    # 1. DOCUMENT VALIDATION
    # -----------------------------------------

    for result in validation_results:

        status = result.get(
            "status",
            ""
        ).upper()

        if status == "FAIL":

            score += 25

            reasons.append(
                result.get(
                    "message",
                    "Validation failure detected."
                )
            )

        elif status == "WARNING":

            score += 8

            reasons.append(
                result.get(
                    "message",
                    "Validation warning detected."
                )
            )


    # -----------------------------------------
    # 2. DOCUMENT FORENSICS
    # -----------------------------------------

    for result in forensic_results:

        status = result.get(
            "status",
            ""
        ).upper()

        if status == "REVIEW":

            score += 30

            reasons.append(
                result.get(
                    "message",
                    "Potential document manipulation signal detected."
                )
            )

        elif status == "FAIL":

            score += 25

            reasons.append(
                result.get(
                    "message",
                    "Forensic check failed."
                )
            )

        elif status == "WARNING":

            score += 5


    # -----------------------------------------
    # 3. FACE DETECTION
    # -----------------------------------------

    face_status = face_result.get(
        "status",
        ""
    ).upper()

    if face_status == "WARNING":

        score += 15

        reasons.append(
            face_result.get(
                "message",
                "Face detection requires review."
            )
        )

    elif face_status == "REVIEW":

        score += 20

        reasons.append(
            face_result.get(
                "message",
                "Multiple faces detected."
            )
        )

    elif face_status == "FAIL":

        score += 25

        reasons.append(
            face_result.get(
                "message",
                "Face detection failed."
            )
        )


    # -----------------------------------------
    # 4. FACE COMPARISON
    # -----------------------------------------

    if face_comparison_result:

        comparison_status = face_comparison_result.get(
            "status",
            ""
        ).upper()

        similarity = face_comparison_result.get(
            "similarity",
            0
        )


        if comparison_status == "FAIL":

            score += 30

            reasons.append(
                face_comparison_result.get(
                    "message",
                    "Low facial similarity detected."
                )
            )


        elif comparison_status == "REVIEW":

            score += 15

            reasons.append(
                face_comparison_result.get(
                    "message",
                    "Moderate facial similarity detected."
                )
            )


        elif comparison_status == "WARNING":

            score += 10

            reasons.append(
                face_comparison_result.get(
                    "message",
                    "Face comparison requires review."
                )
            )


    # -----------------------------------------
    # 5. LIMIT SCORE TO 100
    # -----------------------------------------

    score = min(
        score,
        100
    )


    # -----------------------------------------
    # 6. DETERMINE RISK LEVEL
    # -----------------------------------------

    if score >= 60:

        risk_level = "HIGH"

        risk_message = (
            "Multiple risk signals detected. "
            "Enhanced officer review recommended."
        )


    elif score >= 30:

        risk_level = "MEDIUM"

        risk_message = (
            "Some risk signals detected. "
            "Officer review recommended."
        )


    else:

        risk_level = "LOW"

        risk_message = (
            "No major risk signals detected "
            "in the prototype screening."
        )


    # -----------------------------------------
    # 7. REMOVE DUPLICATE REASONS
    # -----------------------------------------

    unique_reasons = []

    for reason in reasons:

        if reason not in unique_reasons:

            unique_reasons.append(
                reason
            )


    # -----------------------------------------
    # 8. FINAL RESULT
    # -----------------------------------------

    return {

        "score": score,

        "level": risk_level,

        "message": risk_message,

        "reasons": unique_reasons

    }