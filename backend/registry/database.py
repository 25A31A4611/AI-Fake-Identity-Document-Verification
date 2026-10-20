import sqlite3
import os


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "identityguard.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.

    Row factory allows us to access database columns
    using column names.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Main registered document table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_documents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_type TEXT NOT NULL,

            document_number TEXT UNIQUE NOT NULL,

            full_name TEXT,

            date_of_birth TEXT,

            gender TEXT,

            nationality TEXT,

            issue_date TEXT,

            expiry_date TEXT,

            address TEXT,

            document_file TEXT,

            status TEXT DEFAULT 'ACTIVE',

            source TEXT DEFAULT 'REGISTRY',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            last_verified_at TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Existing database migration
    # --------------------------------------------------------
    # If the old database already exists, these columns
    # are added without deleting existing records.
    # --------------------------------------------------------

    existing_columns = set()

    cursor.execute(
        "PRAGMA table_info(registered_documents)"
    )

    columns = cursor.fetchall()

    for column in columns:
        existing_columns.add(
            column["name"]
        )

    migration_columns = {

        "status":
            "ALTER TABLE registered_documents "
            "ADD COLUMN status TEXT DEFAULT 'ACTIVE'",

        "source":
            "ALTER TABLE registered_documents "
            "ADD COLUMN source TEXT DEFAULT 'REGISTRY'",

        "updated_at":
            "ALTER TABLE registered_documents "
            "ADD COLUMN updated_at "
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",

        "last_verified_at":
            "ALTER TABLE registered_documents "
            "ADD COLUMN last_verified_at TIMESTAMP"
    }

    for column_name, sql in migration_columns.items():

        if column_name not in existing_columns:

            try:

                cursor.execute(sql)

            except sqlite3.OperationalError:

                # Column may already exist due to
                # another initialization process.
                pass

    # --------------------------------------------------------
    # Verification history table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            document_id INTEGER,

            document_number TEXT,

            document_type TEXT,

            verification_status TEXT,

            matched_field_count INTEGER DEFAULT 0,

            mismatched_field_count INTEGER DEFAULT 0,

            risk_level TEXT,

            risk_score REAL,

            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(document_id)
                REFERENCES registered_documents(id)
        )
    """)

    # --------------------------------------------------------
    # Index for faster document-number searching
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_registered_document_number
        ON registered_documents(document_number)
    """)

    # --------------------------------------------------------
    # Index for document type
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_registered_document_type
        ON registered_documents(document_type)
    """)

    connection.commit()

    connection.close()


# ============================================================
# DATABASE STATUS
# ============================================================

def database_exists():

    return os.path.exists(
        DATABASE_PATH
    )


# ============================================================
# INITIALIZE WHEN RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print(
        "IdentityGuard database initialized successfully."
    )

    print(
        f"Database location: {DATABASE_PATH}"
    )