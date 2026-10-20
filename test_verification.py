from backend.registry.document_registry import verify_document


# Simulated OCR result from our working passport extraction
extracted_data = {
    "document_type": "passport",
    "document_number": "Z7654321",
    "full_name": "GUNNAM DHARISHRI",
    "date_of_birth": "25-08-2007",
    "gender": "FEMALE",
    "nationality": "INDIAN",
    "expiry_date": "09-09-2033"
}


result = verify_document(extracted_data)


print("\n========== VERIFICATION RESULT ==========")
print("Status:", result["status"])
print("Message:", result["message"])


print("\n========== MATCHED FIELDS ==========")

for field in result["matched_fields"]:
    print(
        f"✓ {field['field']}: {field['value']}"
    )


print("\n========== MISMATCHED FIELDS ==========")

for field in result["mismatched_fields"]:
    print(
        f"✗ {field['field']}: "
        f"OCR = {field['extracted']} | "
        f"Registered = {field['registered']}"
    )