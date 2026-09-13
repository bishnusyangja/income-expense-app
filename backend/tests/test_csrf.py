from tests.helpers import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    CSRF_URL,
    REGISTER_URL,
    assert_api_error,
    assert_envelope,
    assert_status,
)


class TestCsrfTokenEndpoint:
    def test_csrf_token_returns_200_and_token(self, bare_client):
        response = bare_client.get(CSRF_URL)

        body = assert_envelope(response, 200)
        token = body["data"]["csrf_token"]
        assert isinstance(token, str)
        assert len(token) > 0

    def test_csrf_token_sets_cookie(self, bare_client):
        response = bare_client.get(CSRF_URL)

        body = assert_envelope(response, 200)
        assert CSRF_COOKIE_NAME in response.cookies
        assert response.cookies[CSRF_COOKIE_NAME] == body["data"]["csrf_token"]

    def test_csrf_token_reuses_existing_cookie(self, bare_client):
        first = bare_client.get(CSRF_URL)
        second = bare_client.get(CSRF_URL)

        assert_status(second, 200)
        assert first.json()["data"]["csrf_token"] == second.json()["data"]["csrf_token"]


class TestCsrfPostProtection:
    def test_post_without_csrf_returns_403(self, bare_client, valid_payload):
        response = bare_client.post(REGISTER_URL, json=valid_payload)

        assert_api_error(
            response,
            403,
            errors={"csrf": "CSRF token missing"},
            message="CSRF check failed",
        )

    def test_post_with_header_but_no_cookie_returns_403(self, bare_client, valid_payload):
        token = bare_client.get(CSRF_URL).json()["data"]["csrf_token"]
        bare_client.cookies.clear()
        response = bare_client.post(
            REGISTER_URL,
            json=valid_payload,
            headers={CSRF_HEADER_NAME: token},
        )

        assert_api_error(response, 403, errors={"csrf": "CSRF token missing"})

    def test_post_with_cookie_but_no_header_returns_403(self, bare_client, valid_payload):
        bare_client.get(CSRF_URL)
        response = bare_client.post(REGISTER_URL, json=valid_payload)

        assert_api_error(response, 403, errors={"csrf": "CSRF token missing"})

    def test_post_with_mismatched_csrf_returns_403(self, bare_client, valid_payload):
        bare_client.get(CSRF_URL)
        response = bare_client.post(
            REGISTER_URL,
            json=valid_payload,
            headers={CSRF_HEADER_NAME: "not-the-real-token"},
        )

        assert_api_error(response, 403, errors={"csrf": "CSRF token invalid"})

    def test_post_with_valid_csrf_is_not_blocked(self, client, valid_payload):
        response = client.post(REGISTER_URL, json=valid_payload)

        assert_status(response, 201)

    def test_put_without_csrf_returns_403(self, bare_client):
        response = bare_client.put(REGISTER_URL, json={})

        assert_api_error(response, 403, errors={"csrf": "CSRF token missing"})
