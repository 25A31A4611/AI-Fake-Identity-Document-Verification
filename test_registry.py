from backend.registry.document_registry import (
    register_document,
    get_document_by_number
)


# Register a test passport
result = register_document(
    document_type="passport",
    document_number="Z7654321",
    full_name="GUNNAM DHARISHRI",
    date_of_birth="25-08-2007",
    gender="FEMALE",
    nationality="INDIAN",
    issue_date="10-09-2023",
    expiry_date="09-09-2033",
    address="VIJAYAWADA, ANDHRA PRADESH, INDIA",
    document_file="uploads/test_passport.jpg"
)

print("\n========== REGISTRATION RESULT ==========")
print(result)


# Retrieve the same document
document = get_document_by_number("Z7654321")

print("\n========== STORED DOCUMENT ==========")
print(document)