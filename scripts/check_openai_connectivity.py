import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ai.creative_director import check_openai_connectivity


def main() -> None:
    load_dotenv()
    result = check_openai_connectivity()

    print(f"API_KEY_PRESENT={result['error_category'] != 'missing_api_key'}")
    print(f"PROVIDER={result['provider']}")
    print(f"MODEL={result['model']}")
    print(f"SUCCESS={result['success']}")
    print(f"ERROR_CATEGORY={result['error_category'] or 'none'}")


if __name__ == "__main__":
    main()
