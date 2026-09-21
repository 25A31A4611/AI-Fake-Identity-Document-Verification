import cv2
import numpy as np


CASCADE_PATH = cv2.data.haarcascades + (
    "haarcascade_frontalface_default.xml"
)

face_cascade = cv2.CascadeClassifier(
    CASCADE_PATH
)


def get_face(image_path):
    """
    Detect the largest face in an image.

    Prototype only.
    This does not identify a person.
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    if len(faces) == 0:
        return None

    # Select the largest detected face
    largest_face = max(
        faces,
        key=lambda rect: rect[2] * rect[3]
    )

    x, y, w, h = largest_face

    # Add a small margin around the face
    margin_x = int(w * 0.15)
    margin_y = int(h * 0.15)

    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)

    x2 = min(gray.shape[1], x + w + margin_x)
    y2 = min(gray.shape[0], y + h + margin_y)

    face = gray[y1:y2, x1:x2]

    if face.size == 0:
        return None

    # Standardize size
    face = cv2.resize(
        face,
        (200, 200)
    )

    # Improve contrast
    face = cv2.equalizeHist(face)

    return face


def pixel_similarity(face1, face2):
    """
    Compare normalized face images using
    mean absolute pixel difference.
    """

    difference = cv2.absdiff(
        face1,
        face2
    )

    mean_difference = float(
        difference.mean()
    )

    similarity = 100 - (
        mean_difference * 1.5
    )

    return max(
        0,
        min(100, similarity)
    )


def histogram_similarity(face1, face2):
    """
    Compare grayscale intensity distributions.

    Histogram comparison is less sensitive to
    small lighting differences than raw pixels.
    """

    hist1 = cv2.calcHist(
        [face1],
        [0],
        None,
        [256],
        [0, 256]
    )

    hist2 = cv2.calcHist(
        [face2],
        [0],
        None,
        [256],
        [0, 256]
    )

    cv2.normalize(
        hist1,
        hist1
    )

    cv2.normalize(
        hist2,
        hist2
    )

    correlation = cv2.compareHist(
        hist1,
        hist2,
        cv2.HISTCMP_CORREL
    )

    # Convert correlation (-1 to 1)
    # into a 0-100 score.
    similarity = (
        (correlation + 1) / 2
    ) * 100

    return max(
        0,
        min(100, similarity)
    )


def structural_similarity(face1, face2):
    """
    Compare edge/structure information.

    This helps reduce the effect of lighting
    differences.
    """

    edges1 = cv2.Canny(
        face1,
        50,
        150
    )

    edges2 = cv2.Canny(
        face2,
        50,
        150
    )

    difference = cv2.absdiff(
        edges1,
        edges2
    )

    mean_difference = float(
        difference.mean()
    )

    similarity = 100 - (
        mean_difference * 1.5
    )

    return max(
        0,
        min(100, similarity)
    )


def compare_faces(
    passport_image_path,
    reference_image_path
):
    """
    Compare the face detected in a document
    with a reference/demo face.

    Prototype similarity calculation only.

    This does NOT prove real-world identity.
    """

    passport_face = get_face(
        passport_image_path
    )

    reference_face = get_face(
        reference_image_path
    )

    # ------------------------------------------
    # Face detection checks
    # ------------------------------------------

    if passport_face is None:
        return {
            "status": "WARNING",
            "match": False,
            "similarity": 0,
            "message": (
                "No usable face detected "
                "in the document image."
            )
        }

    if reference_face is None:
        return {
            "status": "WARNING",
            "match": False,
            "similarity": 0,
            "message": (
                "No usable face detected "
                "in the reference image."
            )
        }

    # ------------------------------------------
    # Calculate multiple similarity signals
    # ------------------------------------------

    pixel_score = pixel_similarity(
        passport_face,
        reference_face
    )

    histogram_score = histogram_similarity(
        passport_face,
        reference_face
    )

    structure_score = structural_similarity(
        passport_face,
        reference_face
    )

    # ------------------------------------------
    # Combined prototype score
    # ------------------------------------------

    similarity = (
        (pixel_score * 0.40) +
        (histogram_score * 0.30) +
        (structure_score * 0.30)
    )

    similarity = round(
        float(similarity),
        2
    )

    # ------------------------------------------
    # Decision thresholds
    # ------------------------------------------

    if similarity >= 65:

        status = "PASS"
        match = True

        message = (
            "High facial similarity detected. "
            "Reference face appears consistent "
            "with the document face."
        )

    elif similarity >= 45:

        status = "REVIEW"
        match = False

        message = (
            "Moderate facial similarity detected. "
            "Officer review recommended."
        )

    else:

        status = "FAIL"
        match = False

        message = (
            "Low facial similarity detected. "
            "Possible identity mismatch."
        )

    return {
        "status": status,
        "match": match,
        "similarity": similarity,
        "message": message,
        "pixel_score": round(pixel_score, 2),
        "histogram_score": round(histogram_score, 2),
        "structure_score": round(structure_score, 2)
    }