from backend.registry.database import get_connection


DOCUMENT_NUMBER = "Z7654321"

ORIGINAL_DOB = "25-08-2007"
TEST_DOB = "25-08-2006"


def update_dob(new_dob):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE registered_documents
        SET date_of_birth = ?
        WHERE document_number = ?
        """,
        (new_dob, DOCUMENT_NUMBER)
    )

    connection.commit()
    connection.close()

    print(
        f"\nRegistry DOB updated to: {new_dob}"
    )


def show_document():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            document_number,
            full_name,
            date_of_birth,
            gender,
            nationality,
            expiry_date
        FROM registered_documents
        WHERE document_number = ?
        """,
        (DOCUMENT_NUMBER,)
    )

    document = cursor.fetchone()

    connection.close()

    if document:

        print("\nCurrent Registry Record")
        print("==============================")
        print(
            "Document Number:",
            document["document_number"]
        )
        print(
            "Full Name:",
            document["full_name"]
        )
        print(
            "Date of Birth:",
            document["date_of_birth"]
        )
        print(
            "Gender:",
            document["gender"]
        )
        print(
            "Nationality:",
            document["nationality"]
        )
        print(
            "Expiry Date:",
            document["expiry_date"]
        )

    else:

        print(
            f"Document {DOCUMENT_NUMBER} was not found."
        )


if __name__ == "__main__":

    print("RESTORING ORIGINAL REGISTRY DATA")

    update_dob(ORIGINAL_DOB)

    print("\nRESTORED REGISTRY RECORD")

    show_document()