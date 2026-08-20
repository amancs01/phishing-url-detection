"""Reusable URL prediction service for the optimized Decision Tree model."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import OPTIMIZED_MODEL_FILE
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features
from src.url_utils import strip_url


PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1
LABEL_NAMES = {
    PHISHING_LABEL: "Phishing",
    LEGITIMATE_LABEL: "Legitimate",
}


class PredictionError(Exception):
    """Raised when prediction cannot be completed safely."""


def load_optimized_model(model_path: Path = OPTIMIZED_MODEL_FILE) -> Any:
    """Load the packaged optimized Decision Tree model."""

    if not model_path.exists():
        raise FileNotFoundError(
            f"Optimized model file was not found: {model_path}"
        )

    return joblib.load(model_path)


def validate_model(model: Any) -> None:
    """Validate that the model matches the expected feature contract."""

    if not hasattr(model, "predict") or not hasattr(model, "predict_proba"):
        raise PredictionError("Loaded model must support predict and predict_proba.")

    if not hasattr(model, "classes_"):
        raise PredictionError("Loaded model does not expose fitted class labels.")

    class_labels = set(model.classes_.tolist())
    expected_labels = {PHISHING_LABEL, LEGITIMATE_LABEL}

    if class_labels != expected_labels:
        raise PredictionError(
            f"Model classes {sorted(class_labels)} do not match expected "
            f"classes {sorted(expected_labels)}."
        )

    if hasattr(model, "n_features_in_") and model.n_features_in_ != len(FEATURE_NAMES):
        raise PredictionError(
            f"Model expects {model.n_features_in_} features, but "
            f"FEATURE_NAMES contains {len(FEATURE_NAMES)}."
        )


def build_feature_frame(features: dict[str, float | int]) -> pd.DataFrame:
    """Build a one-row feature frame in the exact training feature order."""

    return pd.DataFrame([[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)


def get_class_probability(model: Any, probabilities, class_label: int) -> float:
    """Return the probability for a class by inspecting model.classes_."""

    class_labels = list(model.classes_)

    if class_label not in class_labels:
        raise PredictionError(f"Model does not contain class label {class_label}.")

    class_index = class_labels.index(class_label)
    return float(probabilities[class_index])


def predict_url(url: str, model: Any | None = None) -> dict:
    """Predict whether one raw URL string is phishing or legitimate.

    The submitted URL is never opened or contacted. It is parsed only as local
    text, converted to the project feature set, and passed to the optimized
    Decision Tree in the exact `FEATURE_NAMES` order.
    """

    stripped_url = strip_url(url)

    if not stripped_url:
        raise ValueError("URL input cannot be blank.")

    if model is None:
        model = load_optimized_model()

    validate_model(model)

    features = extract_url_features(stripped_url)
    feature_frame = build_feature_frame(features)
    prediction_label = int(model.predict(feature_frame)[0])
    probabilities = model.predict_proba(feature_frame)[0]

    phishing_probability = get_class_probability(
        model,
        probabilities,
        PHISHING_LABEL,
    )
    legitimate_probability = get_class_probability(
        model,
        probabilities,
        LEGITIMATE_LABEL,
    )
    confidence = (
        phishing_probability
        if prediction_label == PHISHING_LABEL
        else legitimate_probability
    )

    return {
        "prediction_label": prediction_label,
        "prediction_name": LABEL_NAMES[prediction_label],
        "phishing_probability": phishing_probability,
        "legitimate_probability": legitimate_probability,
        "confidence": float(confidence),
        "features": features,
    }


def main() -> None:
    """Run manual prediction checks with harmless example URLs."""

    example_urls = [
        "https://example.com",
        "https://sub.example.com/login?user=test",
        "http://192.0.2.1/account",
    ]

    for example_url in example_urls:
        print(example_url)
        print(predict_url(example_url))


if __name__ == "__main__":
    main()
