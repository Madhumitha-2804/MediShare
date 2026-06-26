import cv2
import easyocr

from ai_models.utils import (
    clean_text,
    extract_expiry_date,
    parse_expiry_date,
    is_expired,
    extract_medicine_name
)


class MedicineVerifier:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)

    def verify_medicine(self, image_paths):
        all_text = []

        for image_path in image_paths:
            print(f"\nReading image: {image_path}")

            image = cv2.imread(image_path)

            if image is None:
                print(f"Could not load image: {image_path}")
                continue

            print(f"Image loaded successfully: {image_path}")

            results = self.reader.readtext(image)

            print("OCR raw results:", results)

            extracted_text = " ".join([res[1] for res in results]).strip()

            print("Extracted OCR text:", extracted_text)

            if extracted_text:
                all_text.append(extracted_text)

        full_text = " ".join(all_text).strip()
        full_text = clean_text(full_text)

        print("\nFinal combined OCR text:", full_text)

        if not full_text:
            return {
                "status": "NEEDS_MANUAL_VERIFICATION",
                "reason": "No readable text found in uploaded images",
                "medicine_name": "UNKNOWN",
                "expiry_date": None,
                "ocr_text": ""
            }

        medicine_name = extract_medicine_name(full_text)
        expiry_date = extract_expiry_date(full_text)

        if not expiry_date:
            return {
                "status": "NEEDS_MANUAL_VERIFICATION",
                "reason": "Expiry date not found in uploaded images",
                "medicine_name": medicine_name,
                "expiry_date": None,
                "ocr_text": full_text
            }

        expiry_obj = parse_expiry_date(expiry_date)

        if expiry_obj is None:
            return {
                "status": "NEEDS_MANUAL_VERIFICATION",
                "reason": "Expiry date format could not be understood",
                "medicine_name": medicine_name,
                "expiry_date": expiry_date,
                "ocr_text": full_text
            }

        if is_expired(expiry_obj):
            return {
                "status": "REJECTED",
                "reason": "Medicine is expired",
                "medicine_name": medicine_name,
                "expiry_date": expiry_date,
                "ocr_text": full_text
            }

        return {
            "status": "VERIFIED",
            "reason": "Medicine verified successfully",
            "medicine_name": medicine_name,
            "expiry_date": expiry_date,
            "ocr_text": full_text
        }