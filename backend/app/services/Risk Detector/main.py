from dotenv import load_dotenv
load_dotenv()  # Loads from .env automatically

import os
print("Credentials path:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

import json
from risk_radar import generate_risk_radar_response

if __name__ == "__main__":
    test_clause = (
        "The tenant shall indemnify the landlord against any damages "
        "and penalties incurred due to breach of contract."
    )
    try:
        result = generate_risk_radar_response(test_clause)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error occurred: {e}")
