import pytesseract
from PIL import Image

# point directly to the exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print(pytesseract.get_tesseract_version())
print("✅ Tesseract ready!")
