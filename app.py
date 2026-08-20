"""Streamlit dashboard for URL-text phishing detection."""

import json

import pandas as pd
import streamlit as st

from src.config import FINAL_TEST_METRICS_FILE
from src.explain import generate_observations, get_risk_level
from src.feature_definitions import FEATURE_NAMES
from src.predict import predict_url


SAFETY_NOTICE = (
    "This application analyses only the URL text. It does not open, visit, "
    "request, download from, or connect to the submitted website."
)


def load_final_metrics() -> dict:
    """Load final test metrics saved during model evaluation."""

    if not FINAL_TEST_METRICS_FILE.exists():
        return {}

    return json.loads(FINAL_TEST_METRICS_FILE.read_text(encoding="utf-8"))


def format_probability(value: float) -> str:
    """Format a probability for display."""

    return f"{value:.2%}"


def show_model_information(metrics_data: dict) -> None:
    """Display model and final evaluation information."""

    metrics = metrics_data.get("metrics", {})

    st.subheader("Model Information")
    st.write("Algorithm: Decision Tree Classifier")
    st.write("Dataset: UCI PhiUSIIL Phishing URL Dataset")
    st.write(f"Number of URL-text features: {len(FEATURE_NAMES)}")

    if metrics:
        metric_table = pd.DataFrame(
            [
                {"Metric": "Final test accuracy", "Value": metrics["accuracy"]},
                {
                    "Metric": "Phishing precision",
                    "Value": metrics["precision_phishing"],
                },
                {"Metric": "Phishing recall", "Value": metrics["recall_phishing"]},
                {"Metric": "Phishing F1-score", "Value": metrics["f1_phishing"]},
                {"Metric": "ROC-AUC", "Value": metrics["roc_auc_phishing"]},
            ]
        )
        metric_table["Value"] = metric_table["Value"].map(lambda value: f"{value:.4f}")
        st.dataframe(metric_table, hide_index=True, use_container_width=True)
    else:
        st.info("Final test metrics file was not found.")


def show_prediction(url: str) -> None:
    """Run prediction and display dashboard result sections."""

    result = predict_url(url)
    risk_level = get_risk_level(result["phishing_probability"])
    observations = generate_observations(result["features"])

    st.subheader("Prediction")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prediction", result["prediction_name"])
    col2.metric("Confidence", format_probability(result["confidence"]))
    col3.metric(
        "Phishing probability",
        format_probability(result["phishing_probability"]),
    )
    col4.metric("Risk level", risk_level)

    st.caption(
        "Probability and confidence are model outputs, not guaranteed security verdicts."
    )

    st.subheader("Model Observations")
    for observation in observations:
        st.write(f"- {observation}")

    with st.expander("Extracted features"):
        feature_table = pd.DataFrame(
            {
                "feature": list(result["features"].keys()),
                "value": list(result["features"].values()),
            }
        )
        st.dataframe(feature_table, hide_index=True, use_container_width=True)


def main() -> None:
    """Render the Streamlit dashboard."""

    st.set_page_config(
        page_title="Phishing URL Detection",
        page_icon="DT",
        layout="wide",
    )

    st.title("Phishing URL Detection")
    st.write("Decision Tree based URL-text classification")
    st.warning(SAFETY_NOTICE)

    url_input = st.text_input(
        "Enter a URL as plain text",
        placeholder="https://example.com/login",
    )

    if st.button("Analyze URL", type="primary"):
        try:
            show_prediction(url_input)
        except Exception as error:
            st.error(f"Analysis could not be completed: {error}")

    show_model_information(load_final_metrics())

    with st.expander("Project limitations"):
        st.write(
            "- The model analyses URL text only and does not examine webpage content."
        )
        st.write("- A prediction is not proof that a website is safe or unsafe.")
        st.write("- Domain reputation, DNS, WHOIS, and SSL certificates are not checked.")
        st.write("- New phishing patterns may differ from the training dataset.")


if __name__ == "__main__":
    main()
