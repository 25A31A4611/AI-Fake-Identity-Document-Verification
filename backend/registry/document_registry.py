from datetime import datetime

from backend.registry.database import (
    get_connection
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_value(value):

    if value is None:
        return ""

    value = str(value)

    value = value.strip().upper()

    # Normalize common punctuation differences
    value = value.replace(".", "")
    value = value.replace(",", "")
    
    # Convert multiple spaces into one
    value = " ".join(
        value.split()
    )

    return value


# ============================================================
# REGISTER DOCUMENT
# ============================================================

def register_document(
    document_type,
    document_number,
    full_name=None,
    date_of_birth=None,
    gender=None,
    nationality=None,
    issue_date=None,
    expiry_date=None,
    address=None,
    document_file=None,
    status="ACTIVE",
    source="REGISTRY"
):

    if not document_number:

        return {
            "success": False,
            "document_id": None,
            "message": "Document number is required."
        }

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO registered_documents (

                document_type,
                document_number,
                full_name,
                date_of_birth,
                gender,
                nationality,
                issue_date,
                expiry_date,
                address,
                document_file,
                status,
                source,
                updated_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,

            (
                document_type,
                document_number,
                full_name,
                date_of_birth,
                gender,
                nationality,
                issue_date,
                expiry_date,
                address,
                document_file,
                status,
                source
            )
        )

        connection.commit()

        document_id = cursor.lastrowid

        return {

            "success": True,

            "document_id": document_id,

            "message":
                "Document registered successfully."
        }

    except Exception as error:

        connection.rollback()

        return {

            "success": False,

            "document_id": None,

            "message": str(error)
        }

    finally:

        connection.close()


# ============================================================
# GET DOCUMENT
# ============================================================

def get_document_by_number(
    document_number
):

    if not document_number:

        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM registered_documents
        WHERE document_number = ?
        """,

        (
            document_number.strip(),
        )
    )

    document = cursor.fetchone()

    connection.close()

    if document:

        return dict(document)

    return None


# ============================================================
# UPDATE LAST VERIFIED TIME
# ============================================================

def update_last_verified(
    document_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE registered_documents

        SET last_verified_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,

        (
            document_id,
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# SAVE VERIFICATION HISTORY
# ============================================================

def save_verification_history(
    document_id,
    document_number,
    document_type,
    verification_status,
    matched_field_count,
    mismatched_field_count,
    risk_level=None,
    risk_score=None
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO verification_history (

            document_id,
            document_number,
            document_type,
            verification_status,
            matched_field_count,
            mismatched_field_count,
            risk_level,
            risk_score

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            document_id,
            document_number,
            document_type,
            verification_status,
            matched_field_count,
            mismatched_field_count,
            risk_level,
            risk_score
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# VERIFY DOCUMENT
# ============================================================

def verify_document(
    extracted_data
):

    document_number = (
        extracted_data.get(
            "document_number"
        )
    )

    document_type = (
        extracted_data.get(
            "document_type"
        )
    )

    # --------------------------------------------------------
    # No document number
    # --------------------------------------------------------

    if not document_number:

        return {

            "status": "NOT FOUND",

            "message":
                "Document number was not detected by OCR.",

            "matched_fields": [],

            "mismatched_fields": [],

            "registered_document": None,

            "document_id": None
        }

    # --------------------------------------------------------
    # Search central registry
    # --------------------------------------------------------

    stored_document = get_document_by_number(
        document_number
    )

    # --------------------------------------------------------
    # Document does not exist
    # --------------------------------------------------------

    if not stored_document:

        return {

            "status": "NOT FOUND",

            "message":
                "No registered document was found "
                "with this document number.",

            "matched_fields": [],

            "mismatched_fields": [],

            "registered_document": None,

            "document_id": None
        }

    # --------------------------------------------------------
    # Check registry status
    # --------------------------------------------------------

    registry_status = str(
        stored_document.get(
            "status",
            "ACTIVE"
        )
    ).upper()

    # --------------------------------------------------------
    # Fields to compare
    # --------------------------------------------------------

    fields_to_compare = {

        "document_type":
            "Document Type",

        "full_name":
            "Full Name",

        "date_of_birth":
            "Date of Birth",

        "gender":
            "Gender",

        "nationality":
            "Nationality",

        "expiry_date":
            "Expiry Date"
    }

    matched_fields = []

    mismatched_fields = []

    # --------------------------------------------------------
    # Compare OCR values with registry
    # --------------------------------------------------------

    for field, display_name in fields_to_compare.items():

        extracted_value = extracted_data.get(
            field
        )

        stored_value = stored_document.get(
            field
        )

        # If OCR did not detect the field,
        # don't incorrectly mark it as mismatch.
        if not extracted_value:

            continue

        # If registry doesn't contain the field,
        # don't incorrectly mark it as mismatch.
        if not stored_value:

            continue

        extracted_normalized = normalize_value(
            extracted_value
        )

        stored_normalized = normalize_value(
            stored_value
        )

        if extracted_normalized == stored_normalized:

            matched_fields.append({

                "field": display_name,

                "value": extracted_value

            })

        else:

            mismatched_fields.append({

                "field": display_name,

                "extracted": extracted_value,

                "registered": stored_value

            })

    # --------------------------------------------------------
    # Determine verification status
    # --------------------------------------------------------

    if registry_status in [
        "BLOCKED",
        "BLACKLISTED"
    ]:

        status = "BLOCKED"

        message = (
            "This document is marked as blocked "
            "in the central registry."
        )

    elif registry_status == "EXPIRED":

        status = "EXPIRED"

        message = (
            "This document exists in the registry "
            "but is marked as expired."
        )

    elif mismatched_fields:

        status = "MISMATCH"

        message = (
            "Document data does not match "
            "the registered record."
        )

    elif matched_fields:

        status = "VERIFIED"

        message = (
            "Document matches the registered "
            "central registry record."
        )

    else:

        status = "REVIEW"

        message = (
            "Document exists in the registry, "
            "but insufficient fields were detected "
            "for complete verification."
        )

    # --------------------------------------------------------
    # Update verification timestamp
    # --------------------------------------------------------

    update_last_verified(
        stored_document["id"]
    )

    # --------------------------------------------------------
    # Return complete verification result
    # --------------------------------------------------------

    return {

        "status": status,

        "message": message,

        "matched_fields":
            matched_fields,

        "mismatched_fields":
            mismatched_fields,

        "registered_document":
            stored_document,

        "document_id":
            stored_document["id"],

        "registry_status":
            registry_status,

        "document_number":
            document_number
    }


# ============================================================
# GET VERIFICATION HISTORY
# ============================================================

def get_verification_history(
    document_number=None
):

    connection = get_connection()

    cursor = connection.cursor()

    if document_number:

        cursor.execute(
            """
            SELECT *
            FROM verification_history
            WHERE document_number = ?
            ORDER BY verified_at DESC
            """,

            (
                document_number,
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM verification_history
            ORDER BY verified_at DESC
            """
        )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]