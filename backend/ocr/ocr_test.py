import pytesseract
from PIL import Image

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Open document image
image = Image.open("../../uploads/test_document.jpeg")

# Extract text
text = pytesseract.image_to_string(image)

print("\n========== EXTRACTED TEXT ==========\n")
print(text)
print("\n====================================")