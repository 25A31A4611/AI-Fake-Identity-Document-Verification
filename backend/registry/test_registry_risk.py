from backend.risk.risk_engine import calculate_risk


def test_registry_mismatch():

    validation_result = {
        "status": "VALID",
        "score": 100
    }

    tampering_result = {
        "status": "LOW RISK",
        "score": 0
    }

    face_result = {
        "status": "MATCH",
        "score": 70.54
    }

    liveness_result = {
        "status": "LIVE",
        "score": 91.97
    }

    # Deliberately create a registry mismatch
    registry_result = {
        "status": "MISMATCH",

        "message": (
            "Registry field mismatch detected."
        ),

        "matched_fields": [
            {
                "field": "Gender",
                "value": "FEMALE"
            },

            {
                "field": "Nationality",
                "value": "INDIAN"
            }
        ],

        "mismatched_fields": [
            {
                "field": "Date of Birth",
                "extracted": "25-08-2007",
                "registered": "25-08-2006"
            }
        ],

        "registered_document": {
            "document_number": "Z7654321"
        }
    }


    result = calculate_risk(
        validation_result,
        tampering_result,
        face_result,
        liveness_result,
        registry_result
    )


    print("\n==============================")
    print("REGISTRY MISMATCH TEST")
    print("==============================")

    print(
        "Registry Status:",
        result["registry_status"]
    )

    print(
        "Registry Contribution:",
        result["registry_contribution"]
    )

    print(
        "Final Risk Score:",
        result["score"]
    )

    print(
        "Risk Level:",
        result["level"]
    )

    print("\nRisk Reasons:")

    for reason in result["reasons"]:

        print(
            "-",
            reason
        )


if __name__ == "__main__":

    test_registry_mismatch()