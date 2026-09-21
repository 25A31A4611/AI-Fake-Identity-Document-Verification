import cv2
import os


# Load OpenCV's built-in Haar Cascade face detector
CASCADE_PATH = cv2.data.haarcascades + (
    "haarcascade_frontalface_default.xml"
)

face_cascade = cv2.CascadeClassifier(
    CASCADE_PATH
)


def detect_faces(image_path):
    """
    Detect faces present in a document image.

    Prototype purpose:
    Identify whether a photograph/face is present.

    This does NOT identify the person.
    """

    image = cv2.imread(image_path)

    if image is None:
        return {
            "status": "FAIL",
            "message": "Unable to read document image.",
            "face_count": 0
        }

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    face_count = len(faces)

    if face_count == 0:

        return {
            "status": "WARNING",
            "message": (
                "No face detected in the uploaded document."
            ),
            "face_count": 0
        }

    elif face_count == 1:

        return {
            "status": "PASS",
            "message": (
                "One face detected in the document."
            ),
            "face_count": 1
        }

    else:

        return {
            "status": "REVIEW",
            "message": (
                "Multiple faces detected. "
                "Officer review recommended."
            ),
            "face_count": face_count
        }