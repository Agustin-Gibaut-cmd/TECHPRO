"""Cliente HTTP ligero con cookies y CSRF para smoke tests."""

import http.cookiejar
import json
import urllib.error
import urllib.request
from typing import Any


class SmokeApiClient:
    """Envía peticiones HTTP y valida el código de estado esperado."""

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def send(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        use_csrf: bool = False,
        expected_status: int = 200,
    ) -> Any:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("Accept", "application/json")

        if body is not None:
            request.add_header("Content-Type", "application/json")
        if use_csrf:
            request.add_header("X-CSRFToken", self.fetch_csrf_token())

        status_code, raw_body = self._execute_request(request)
        if status_code != expected_status:
            decoded = raw_body.decode("utf-8", errors="replace")
            raise AssertionError(
                f"{method} {path} -> esperado {expected_status}, "
                f"obtenido {status_code}: {decoded}"
            )
        return json.loads(raw_body.decode("utf-8")) if raw_body else None

    def fetch_csrf_token(self) -> str:
        data = self.send("GET", "/api/auth/csrf/", expected_status=200)
        return str(data["csrfToken"])

    def login(self, email: str, password: str) -> dict[str, Any]:
        data = self.send(
            "POST",
            "/api/auth/login/",
            {"email": email, "password": password},
            use_csrf=True,
            expected_status=200,
        )
        return dict(data["user"])

    def _execute_request(self, request: urllib.request.Request) -> tuple[int, bytes]:
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return int(response.status), response.read()
        except urllib.error.HTTPError as error:
            try:
                return int(error.code), error.read()
            finally:
                error.close()
