import cv2
import pytesseract

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Load document image
image = cv2.imread("../../uploads/test_document.jpeg")

if image is None:
    print("ERROR: Image could not be loaded.")
    exit()

# Step 1: Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Step 2: Reduce noise
blurred = cv2.GaussianBlur(gray, (3, 3), 0)

# Step 3: Improve text contrast
processed = cv2.adaptiveThreshold(
    blurred,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,
    11
)

# Save processed image
cv2.imwrite("../../uploads/processed_document.jpeg", processed)

# OCR on processed image
text = pytesseract.image_to_string(processed)

print("\n========== PREPROCESSED OCR OUTPUT ==========\n")
print(text)
print("\n=============================================")

print("\nProcessed image saved as:")
print("../../uploads/processed_document.png")