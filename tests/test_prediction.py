"""Tests for prediction, risk levels, and safety contracts."""

import inspect
import math

import pytest

from src.explain import generate_observations, get_risk_level
from src.feature_definitions import FEATURE_NAMES
from src.predict import build_feature_frame, predict_url


SAFE_URLS = [
    "https://example.com",
    "example.org/login",
    "http://192.0.2.1/account",
    "https://test.example/search?q=test&page=2",
]


def test_feature_order_matches_training_feature_order() -> None:
    """Prediction feature frames should follow FEATURE_NAMES exactly."""

    prediction = predict_url("https://example.com")
    feature_frame = build_feature_frame(prediction["features"])

    assert list(feature_frame.columns) == FEATURE_NAMES


def test_prediction_returns_expected_keys() -> None:
    """Prediction output should expose the expected structured keys."""

    prediction = predict_url("https://example.com")

    assert set(prediction) == {
        "prediction_label",
        "prediction_name",
        "phishing_probability",
        "legitimate_probability",
        "confidence",
        "features",
    }


def test_probabilities_are_between_zero_and_one() -> None:
    """Model probabilities should be valid probability-like values."""

    prediction = predict_url("https://example.com")

    assert 0 <= prediction["phishing_probability"] <= 1
    assert 0 <= prediction["legitimate_probability"] <= 1


def test_probabilities_sum_to_one() -> None:
    """Binary class probabilities should approximately sum to 1."""

    prediction = predict_url("https://example.com")
    total = prediction["phishing_probability"] + prediction["legitimate_probability"]

    assert math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9)


def test_confidence_is_between_zero_and_one() -> None:
    """Confidence should be the predicted class probability."""

    prediction = predict_url("https://example.com")

    assert 0 <= prediction["confidence"] <= 1


def test_prediction_label_is_expected_class() -> None:
    """Predicted labels should be one of the project labels."""

    prediction = predict_url("https://example.com")

    assert prediction["prediction_label"] in {0, 1}
    assert prediction["prediction_name"] in {"Phishing", "Legitimate"}


def test_blank_url_is_rejected() -> None:
    """Blank input should fail before model prediction."""

    with pytest.raises(ValueError, match="blank"):
        predict_url("   ")


def test_same_url_gives_deterministic_prediction() -> None:
    """The same input should produce the same prediction result."""

    url = "https://sub.example.com/login?user=test"

    assert predict_url(url) == predict_url(url)


def test_risk_levels_map_correctly_at_boundaries() -> None:
    """Risk thresholds should match the documented dashboard behavior."""

    assert get_risk_level(0.00) == "Low"
    assert get_risk_level(0.3499) == "Low"
    assert get_risk_level(0.35) == "Moderate"
    assert get_risk_level(0.6499) == "Moderate"
    assert get_risk_level(0.65) == "High"
    assert get_risk_level(0.8499) == "High"
    assert get_risk_level(0.85) == "Very High"
    assert get_risk_level(1.00) == "Very High"


def test_model_observations_return_a_list() -> None:
    """Observation generation should return user-facing text."""

    prediction = predict_url("https://sub.example.com/login?user=test")
    observations = generate_observations(prediction["features"])

    assert isinstance(observations, list)
    assert observations
    assert all(isinstance(observation, str) for observation in observations)


@pytest.mark.parametrize("url", SAFE_URLS)
def test_invented_harmless_urls_can_be_processed(url: str) -> None:
    """Reserved or harmless URLs should pass through the prediction pipeline."""

    prediction = predict_url(url)

    assert prediction["prediction_label"] in {0, 1}


def test_url_without_explicit_scheme_works() -> None:
    """URLs without schemes should still be parsed locally."""

    prediction = predict_url("example.com/login")

    assert prediction["features"]["domain_length"] == len("example.com")


def test_ip_literal_url_works() -> None:
    """IP-literal URLs should be handled without DNS resolution."""

    prediction = predict_url("http://192.0.2.1/account")

    assert prediction["features"]["domain_is_ip"] == 1


def test_query_parameters_work() -> None:
    """Query parameters should be counted from URL text."""

    prediction = predict_url("https://test.example/search?q=test&page=2")

    assert prediction["features"]["number_of_query_parameters"] == 2


def test_no_network_dependent_feature_exists() -> None:
    """Feature names should not depend on live network or webpage inspection."""

    banned_terms = {
        "dns",
        "whois",
        "ssl",
        "certificate",
        "favicon",
        "html",
        "content",
        "request",
        "response",
        "socket",
    }

    for feature_name in FEATURE_NAMES:
        assert not any(term in feature_name for term in banned_terms)


def test_prediction_code_does_not_import_network_libraries() -> None:
    """Prediction modules should not import HTTP, browser, or DNS libraries."""

    import src.predict as predict_module

    source = inspect.getsource(predict_module)
    banned_snippets = [
        "requests",
        "urllib.request",
        "selenium",
        "playwright",
        "socket",
        "whois",
        "urlopen",
    ]

    for snippet in banned_snippets:
        assert snippet not in source
