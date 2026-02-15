"""
Example usage of the ML Inference Service using Python requests.
"""
import requests
import json
from typing import List

API_URL = "http://localhost:8000"


def health_check():
    """Check if service is healthy."""
    response = requests.get(f"{API_URL}/health")
    print(f"Health Check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()


def ready_check():
    """Check if service is ready to serve."""
    response = requests.get(f"{API_URL}/ready")
    print(f"Ready Check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()


def predict(features: List[float], request_id: str = None):
    """Make a prediction."""
    payload = {
        "features": features,
        "request_id": request_id
    }
    response = requests.post(f"{API_URL}/predict", json=payload)
    print(f"Prediction Request: {request_id or 'No ID'}")
    print(f"Status: {response.status_code}")
    if response.ok:
        result = response.json()
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"Error: {response.text}")
        return None


def main():
    """Run example requests."""
    print("=" * 50)
    print("ML Inference Service - Python Examples")
    print("=" * 50)
    print()
    
    # Health check
    print("1. Health Check")
    health_check()
    print()
    
    # Readiness check
    print("2. Readiness Check")
    ready_check()
    print()
    
    # Prediction examples
    examples = [
        {
            "name": "Iris Setosa",
            "features": [5.1, 3.5, 1.4, 0.2],
            "expected_class": 0
        },
        {
            "name": "Iris Versicolor",
            "features": [6.4, 3.2, 4.5, 1.5],
            "expected_class": 1
        },
        {
            "name": "Iris Virginica",
            "features": [6.3, 3.3, 6.0, 2.5],
            "expected_class": 2
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i + 2}. Prediction - {example['name']}")
        result = predict(
            features=example["features"],
            request_id=f"example-{i:03d}"
        )
        if result:
            print(f"   Expected: {example['expected_class']}, "
                  f"Predicted: {result['prediction']}, "
                  f"Confidence: {result['confidence']:.3f}")
        print()
    
    # Error handling example
    print("6. Invalid Request (should fail)")
    try:
        predict(features=[5.1, 3.5], request_id="invalid-001")
    except Exception as e:
        print(f"   Caught exception: {e}")
    print()
    
    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()