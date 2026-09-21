import pytesseract
import cv2

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(image_path):
    """
    Extract text from an uploaded document image using OCR.
    """

    image = cv2.imread(image_path)

    if image is None:
        return "Unable to read the document image."

    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Improve text visibility
    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # OCR
    text = pytesseract.image_to_string(gray)

    return text