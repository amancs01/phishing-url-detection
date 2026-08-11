"""Safe local URL parsing helpers.

These functions treat URLs as plain text only. They use standard-library
parsing and never resolve, request, open, or otherwise contact a destination.
"""

import ipaddress
import re
from urllib.parse import ParseResult, parse_qsl, urlparse


SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def strip_url(url: str) -> str:
    """Return the URL text with surrounding whitespace removed."""

    return str(url).strip()


def add_scheme_for_parsing(url: str) -> str:
    """Add a temporary scheme only when needed for reliable parsing.

    Character-count features should still use the original stripped URL text.
    This helper only improves parsing of inputs such as `example.com/login`,
    which `urllib.parse.urlparse` would otherwise treat as a path.
    """

    stripped_url = strip_url(url)

    if not stripped_url:
        return stripped_url

    if SCHEME_PATTERN.match(stripped_url) or stripped_url.startswith("//"):
        return stripped_url

    return f"http://{stripped_url}"


def parse_url(url: str) -> ParseResult:
    """Parse URL text locally without contacting the destination."""

    return urlparse(add_scheme_for_parsing(url))


def get_hostname(url: str) -> str:
    """Return the parsed hostname/domain text, or an empty string."""

    parsed_url = parse_url(url)
    return (parsed_url.hostname or "").lower()


def get_path(url: str) -> str:
    """Return the parsed path text."""

    return parse_url(url).path or ""


def get_query(url: str) -> str:
    """Return the parsed query string without the leading question mark."""

    return parse_url(url).query or ""


def uses_https_scheme(url: str) -> bool:
    """Return True when the URL text parses with an HTTPS scheme.

    This checks only the submitted text. It does not inspect certificates or
    verify that the remote website is actually reachable or secure.
    """

    return parse_url(url).scheme.lower() == "https"


def _netloc_contains_port(netloc: str) -> bool:
    """Return True when netloc text contains an explicit port section."""

    host_port_text = netloc.rsplit("@", maxsplit=1)[-1]

    if host_port_text.startswith("["):
        closing_bracket_index = host_port_text.find("]")
        return (
            closing_bracket_index != -1
            and host_port_text[closing_bracket_index + 1 :].startswith(":")
        )

    return ":" in host_port_text and bool(host_port_text.rsplit(":", maxsplit=1)[-1])


def has_explicit_port(url: str) -> bool:
    """Return True when the URL text includes a port after the hostname.

    Invalid port text is still treated as explicit port text, but it never
    raises an exception.
    """

    parsed_url = parse_url(url)

    try:
        return parsed_url.port is not None
    except ValueError:
        return _netloc_contains_port(parsed_url.netloc)


def hostname_is_ip_address(hostname: str) -> bool:
    """Return True when hostname text is an IPv4 or IPv6 literal."""

    if not hostname:
        return False

    try:
        ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        return False

    return True


def count_query_parameters(query: str) -> int:
    """Return the number of query parameters in a query string."""

    if not query:
        return 0

    return len(parse_qsl(query, keep_blank_values=True))


def main() -> None:
    """Run small local parsing checks for development."""

    assert get_hostname("example.com/login") == "example.com"
    assert get_path("example.com/login") == "/login"
    assert get_query("https://example.com/login?user=test") == "user=test"
    assert uses_https_scheme("https://example.com")
    assert not uses_https_scheme("example.com")
    assert has_explicit_port("https://example.com:8443/login")
    assert hostname_is_ip_address(get_hostname("http://192.0.2.1/account"))
    assert count_query_parameters("user=test&empty=") == 2

    print("Safe URL parsing checks passed.")


if __name__ == "__main__":
    main()
