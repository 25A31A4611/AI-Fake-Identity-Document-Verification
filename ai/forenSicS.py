import cv2
import os


def analyze_document(image_path):
    """
    Prototype document-forensics analysis.

    This module detects image-level signals that may
    indicate possible document manipulation.

    It does NOT prove that a document is fake.
    Final decisions remain with the authorized officer.
    """

    results = []

    # ==================================================
    # 1. READ IMAGE
    # ==================================================

    image = cv2.imread(image_path)

    if image is None:

        return [
            {
                "check": "Image Integrity",
                "status": "FAIL",
                "message": "Unable to read the document image."
            }
        ]


    # ==================================================
    # 2. IMAGE QUALITY
    # ==================================================

    height, width = image.shape[:2]

    if width < 500 or height < 300:

        results.append({
            "check": "Image Quality",
            "status": "WARNING",
            "message": (
                "Low-resolution image may affect "
                "forensic analysis."
            )
        })

    else:

        results.append({
            "check": "Image Quality",
            "status": "PASS",
            "message": (
                "Image resolution is sufficient "
                "for prototype analysis."
            )
        })


    # ==================================================
    # 3. IMAGE SHARPNESS
    # ==================================================

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    sharpness = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()


    if sharpness < 80:

        results.append({
            "check": "Image Sharpness",
            "status": "WARNING",
            "message": (
                "Image appears blurred or compressed."
            )
        })

    else:

        results.append({
            "check": "Image Sharpness",
            "status": "PASS",
            "message": (
                "Image sharpness is acceptable."
            )
        })


    # ==================================================
    # 4. DOCUMENT STRUCTURE
    # ==================================================

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = cv2.countNonZero(edges)

    total_pixels = (
        edges.shape[0] *
        edges.shape[1]
    )

    edge_ratio = edge_pixels / total_pixels


    if edge_ratio < 0.01:

        results.append({
            "check": "Document Structure",
            "status": "WARNING",
            "message": (
                "Very few document features detected."
            )
        })

    else:

        results.append({
            "check": "Document Structure",
            "status": "PASS",
            "message": (
                "Document features detected."
            )
        })


    # ==================================================
    # 5. LOCAL TEXTURE ANALYSIS
    # ==================================================

    block_size = 100

    texture_values = []


    for y in range(
        0,
        height - block_size,
        block_size
    ):

        for x in range(
            0,
            width - block_size,
            block_size
        ):

            block = gray[
                y:y + block_size,
                x:x + block_size
            ]

            variance = cv2.Laplacian(
                block,
                cv2.CV_64F
            ).var()

            texture_values.append(
                variance
            )


    # ==================================================
    # 6. LOCAL TEXTURE CONSISTENCY
    # ==================================================

    if len(texture_values) >= 4:

        average_texture = (
            sum(texture_values)
            / len(texture_values)
        )

        suspicious_blocks = 0


        for value in texture_values:

            if average_texture > 0:

                difference = (
                    abs(
                        value -
                        average_texture
                    )
                    / average_texture
                )

                if difference > 2.0:

                    suspicious_blocks += 1


        suspicious_ratio = (
            suspicious_blocks /
            len(texture_values)
        )


        if suspicious_ratio > 0.15:

            results.append({
                "check": "Local Texture Consistency",
                "status": "REVIEW",
                "message": (
                    "Localized texture inconsistency detected. "
                    "Possible edited or recompressed region."
                )
            })

        else:

            results.append({
                "check": "Local Texture Consistency",
                "status": "PASS",
                "message": (
                    "No strong localized texture inconsistency "
                    "detected."
                )
            })


    else:

        results.append({
            "check": "Local Texture Consistency",
            "status": "WARNING",
            "message": (
                "Image is too small for reliable "
                "local texture analysis."
            )
        })


    # ==================================================
    # 7. IMAGE METADATA
    # ==================================================

    extension = os.path.splitext(
        image_path
    )[1].lower()


    if extension in [
        ".jpg",
        ".jpeg",
        ".png"
    ]:

        # OpenCV does not preserve/read all EXIF
        # metadata reliably. Therefore, we do not
        # mark normal images as suspicious simply
        # because metadata is unavailable.

        results.append({
            "check": "Image Metadata",
            "status": "PASS",
            "message": (
                "Image metadata check completed. "
                "No metadata-based warning generated."
            )
        })

    else:

        results.append({
            "check": "Image Metadata",
            "status": "REVIEW",
            "message": (
                "File format requires additional "
                "metadata inspection."
            )
        })


    # ==================================================
    # 8. FINAL TAMPERING SCREENING
    # ==================================================

    review_required = any(
        item["status"] == "REVIEW"
        for item in results
    )


    fail_detected = any(
        item["status"] == "FAIL"
        for item in results
    )


    if fail_detected:

        final_status = "FAIL"

        final_message = (
            "Forensic analysis encountered a "
            "critical image-processing issue."
        )


    elif review_required:

        final_status = "REVIEW"

        final_message = (
            "Some visual characteristics require "
            "additional officer review."
        )


    else:

        final_status = "PASS"

        final_message = (
            "No strong image-level manipulation signal "
            "detected in this prototype analysis."
        )


    results.append({

        "check": "Tampering Screening",

        "status": final_status,

        "message": final_message

    })


    return results