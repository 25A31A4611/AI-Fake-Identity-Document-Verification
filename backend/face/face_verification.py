import os
import cv2


# =========================================
# MODEL PATHS
# =========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODELS_DIR = os.path.join(
    BASE_DIR,
    "models"
)

YUNET_MODEL = os.path.join(
    MODELS_DIR,
    "face_detection_yunet_2023mar.onnx"
)

SFACE_MODEL = os.path.join(
    MODELS_DIR,
    "face_recognition_sface_2021dec.onnx"
)


# =========================================
# LOAD AI MODELS
# =========================================

# Lower score threshold helps detect
# small faces inside ID documents.
face_detector = cv2.FaceDetectorYN.create(
    YUNET_MODEL,
    "",
    (320, 320),
    0.3,
    0.3,
    5000
)

face_recognizer = cv2.FaceRecognizerSF.create(
    SFACE_MODEL,
    ""
)


# =========================================
# DETECT FACE
# =========================================

def detect_face(image):
    """
    Detect the largest valid face in an image.

    Multiple scales are used to improve detection
    of small faces inside identity documents.
    """

    if image is None:
        return None

    scales = [1.0, 1.5, 2.0]

    best_face = None
    best_score = 0
    best_area = 0

    for scale in scales:

        # ---------------------------------
        # Resize image
        # ---------------------------------

        if scale == 1.0:

            resized = image

        else:

            resized = cv2.resize(
                image,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )


        height, width = resized.shape[:2]


        # ---------------------------------
        # Detect faces
        # ---------------------------------

        face_detector.setInputSize(
            (width, height)
        )

        _, faces = face_detector.detect(
            resized
        )


        if faces is None:

            continue


        # ---------------------------------
        # Select best face
        # ---------------------------------

        for face in faces:

            x, y, w, h = face[:4]

            confidence = face[-1]

            area = w * h


            # Prefer confidence first,
            # then face size.
            if (
                confidence > best_score
                or (
                    confidence == best_score
                    and area > best_area
                )
            ):

                best_score = confidence

                best_area = area

                best_face = face.copy()


                # Convert coordinates
                # back to original scale.
                best_face[:14] = (
                    best_face[:14] / scale
                )


    return best_face


# =========================================
# PREPARE DOCUMENT FACE
# =========================================

def prepare_document_face(
    document_image,
    detected_face
):
    """
    Crop the portrait region from the document,
    add padding, upscale it, and detect the face
    again for better recognition quality.
    """

    if detected_face is None:

        return None


    height, width = document_image.shape[:2]

    x, y, w, h = detected_face[:4]


    # ---------------------------------
    # Add padding around face
    # ---------------------------------

    padding_x = int(w * 0.35)

    padding_y = int(h * 0.35)


    x1 = max(
        0,
        int(x - padding_x)
    )

    y1 = max(
        0,
        int(y - padding_y)
    )

    x2 = min(
        width,
        int(x + w + padding_x)
    )

    y2 = min(
        height,
        int(y + h + padding_y)
    )


    portrait_crop = document_image[
        y1:y2,
        x1:x2
    ]


    if portrait_crop.size == 0:

        return None


    # ---------------------------------
    # Upscale portrait
    # ---------------------------------

    portrait_crop = cv2.resize(
        portrait_crop,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC
    )


    # ---------------------------------
    # Improve local contrast
    # ---------------------------------

    lab = cv2.cvtColor(
        portrait_crop,
        cv2.COLOR_BGR2LAB
    )

    l, a, b = cv2.split(
        lab
    )


    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )


    enhanced_l = clahe.apply(
        l
    )


    enhanced = cv2.merge(
        (
            enhanced_l,
            a,
            b
        )
    )


    enhanced = cv2.cvtColor(
        enhanced,
        cv2.COLOR_LAB2BGR
    )


    # ---------------------------------
    # Detect face again
    # ---------------------------------

    refined_face = detect_face(
        enhanced
    )


    if refined_face is None:

        return None


    return (
        enhanced,
        refined_face
    )


# =========================================
# ALIGN FACE
# =========================================

def get_document_aligned_face(
    document_image
):
    """
    Detect and prepare the face inside
    an identity document.
    """

    document_face = detect_face(
        document_image
    )


    if document_face is None:

        return None


    prepared_result = prepare_document_face(
        document_image,
        document_face
    )


    if prepared_result is None:

        # Fall back to the original image.
        return face_recognizer.alignCrop(
            document_image,
            document_face
        )


    prepared_image, refined_face = (
        prepared_result
    )


    return face_recognizer.alignCrop(
        prepared_image,
        refined_face
    )


def get_verification_aligned_face(
    verification_image
):
    """
    Detect and align the face from the
    verification photograph.
    """

    verification_face = detect_face(
        verification_image
    )


    if verification_face is None:

        return None


    return face_recognizer.alignCrop(
        verification_image,
        verification_face
    )


# =========================================
# COMPARE FACES
# =========================================

def compare_faces(
    document_image_path,
    verification_image_path
):
    """
    Face verification using:

    YuNet -> Face Detection
    Document Portrait Processing
    SFace -> Face Embedding
    Cosine Similarity -> Comparison
    """

    # ---------------------------------
    # Check files
    # ---------------------------------

    if not os.path.exists(
        document_image_path
    ):

        raise FileNotFoundError(
            "Document image was not found."
        )


    if not os.path.exists(
        verification_image_path
    ):

        raise FileNotFoundError(
            "Verification image was not found."
        )


    # ---------------------------------
    # Read images
    # ---------------------------------

    document_image = cv2.imread(
        document_image_path
    )

    verification_image = cv2.imread(
        verification_image_path
    )


    if document_image is None:

        raise ValueError(
            "Unable to read the document image."
        )


    if verification_image is None:

        raise ValueError(
            "Unable to read the verification image."
        )


    # ---------------------------------
    # Process document face
    # ---------------------------------

    document_aligned = (
        get_document_aligned_face(
            document_image
        )
    )


    if document_aligned is None:

        return {
            "status": "REVIEW",
            "score": 0,
            "match": False,
            "reason": (
                "No face could be detected "
                "in the uploaded document."
            )
        }


    # ---------------------------------
    # Process verification face
    # ---------------------------------

    verification_aligned = (
        get_verification_aligned_face(
            verification_image
        )
    )


    if verification_aligned is None:

        return {
            "status": "REVIEW",
            "score": 0,
            "match": False,
            "reason": (
                "No face could be detected "
                "in the verification image."
            )
        }


    # ---------------------------------
    # Generate embeddings
    # ---------------------------------

    document_feature = (
        face_recognizer.feature(
            document_aligned
        )
    )


    verification_feature = (
        face_recognizer.feature(
            verification_aligned
        )
    )


    # ---------------------------------
    # Calculate cosine similarity
    # ---------------------------------

    cosine_score = (
        face_recognizer.match(
            document_feature,
            verification_feature,
            cv2.FaceRecognizerSF_FR_COSINE
        )
    )


    # ---------------------------------
    # Display score
    # ---------------------------------

    score = round(
        max(
            0,
            min(
                cosine_score * 100,
                100
            )
        ),
        2
    )


    # ---------------------------------
    # Matching threshold
    # ---------------------------------

    match = (
        cosine_score >= 0.363
    )


    if match:

        status = "MATCH"

        reason = (
            "A face was detected in both images "
            "and the AI face comparison indicates "
            "a likely identity match."
        )

    else:

        status = "NO MATCH"

        reason = (
            "Faces were detected in both images, "
            "but the similarity score is below "
            "the prototype matching threshold."
        )


    # ---------------------------------
    # Return result
    # ---------------------------------

    return {
        "status": status,
        "score": score,
        "match": match,
        "reason": reason
    }