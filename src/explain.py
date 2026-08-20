"""User-facing risk levels and model observations."""


RISK_THRESHOLDS = {
    "low_upper": 0.35,
    "moderate_upper": 0.65,
    "high_upper": 0.85,
}


def get_risk_level(phishing_probability: float) -> str:
    """Return a UI risk level from phishing probability.

    These fixed thresholds are for dashboard interpretation only. They are not
    academically optimized decision thresholds and should not be treated as
    guaranteed security verdicts.
    """

    if phishing_probability < 0 or phishing_probability > 1:
        raise ValueError("Phishing probability must be between 0 and 1.")

    if phishing_probability < RISK_THRESHOLDS["low_upper"]:
        return "Low"
    if phishing_probability < RISK_THRESHOLDS["moderate_upper"]:
        return "Moderate"
    if phishing_probability < RISK_THRESHOLDS["high_upper"]:
        return "High"

    return "Very High"


def generate_observations(features: dict) -> list[str]:
    """Generate neutral observations from extracted URL-text features."""

    observations = []

    if features.get("url_length", 0) >= 75:
        observations.append(
            "The URL contains many characters; URL length may contribute to phishing risk."
        )

    if features.get("number_of_subdomains", 0) >= 3:
        observations.append(
            "The model received a URL with several subdomains."
        )

    if features.get("domain_is_ip", 0) == 1:
        observations.append(
            "The hostname text is an IP address literal rather than a domain name."
        )

    if features.get("has_suspicious_keyword", 0) == 1:
        observations.append(
            "The URL contains one or more account, login, verification, or security-related keywords."
        )

    if features.get("number_of_digits", 0) >= 8:
        observations.append(
            "The URL contains many digits, which the model received as a lexical signal."
        )

    if features.get("number_of_at_symbols", 0) > 0:
        observations.append(
            "The URL contains an @ symbol, a character sometimes used in confusing URL text."
        )

    if features.get("number_of_query_parameters", 0) >= 3:
        observations.append(
            "The URL contains multiple query parameters."
        )

    if features.get("known_shortener_domain", 0) == 1:
        observations.append(
            "The hostname matches a known URL-shortener domain from the local project list."
        )

    if features.get("special_character_count", 0) >= 12:
        observations.append(
            "The URL contains a high number of non-letter and non-digit characters."
        )

    if features.get("has_port", 0) == 1:
        observations.append(
            "The URL text includes an explicit port number."
        )

    if not observations:
        observations.append(
            "No strong lexical warning signs from the observation rules were found."
        )

    return observations


def main() -> None:
    """Run small local checks for risk levels and observations."""

    example_features = {
        "url_length": 90,
        "number_of_subdomains": 3,
        "domain_is_ip": 0,
        "has_suspicious_keyword": 1,
        "number_of_digits": 4,
        "number_of_at_symbols": 0,
        "number_of_query_parameters": 2,
        "known_shortener_domain": 0,
        "special_character_count": 14,
        "has_port": 0,
    }

    print(get_risk_level(0.90))
    print(generate_observations(example_features))


if __name__ == "__main__":
    main()
