import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interview_app_backend.llm.client import get_openrouter_client, call_llm, _extract_provider
from config.settings import FREE_MODELS, MODEL_NAME

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger(__name__)


def test_provider(model: str, timeout: int = 30) -> dict:
    provider = _extract_provider(model)
    print(f"\nTesting {provider} ({model})...")
    try:
        client = get_openrouter_client()
        result = call_llm("Say exactly 'OK' if you can read this.", client, temperature=0.1)
        success = "OK" in result.upper()
        return {"provider": provider, "model": model, "status": "OK" if success else "FAIL", "response": result[:100]}
    except Exception as e:
        return {"provider": provider, "model": model, "status": "ERROR", "error": str(e)[:100]}


def main():
    print("\n" + "=" * 60)
    print("MODEL AVAILABILITY TEST")
    print("=" * 60)
    print(f"Configured MODEL_NAME: {MODEL_NAME}")
    print(f"Available models: {FREE_MODELS}")
    print("-" * 60)

    results = []
    for model in FREE_MODELS:
        result = test_provider(model)
        results.append(result)
        status = result["status"]
        print(f"  {result['provider']:12} | {status}")

    print("-" * 60)
    working = [r for r in results if r["status"] == "OK"]
    not_working = [r for r in results if r["status"] != "OK"]

    print(f"\nWORKING ({len(working)}):")
    for r in working:
        print(f"  - {r['provider']}: {r['model']}")

    print(f"\nNOT WORKING ({len(not_working)}):")
    for r in not_working:
        print(f"  - {r['provider']}: {r['model']} - {r.get('error', r.get('status'))}")

    return results


if __name__ == "__main__":
    main()