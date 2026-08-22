import json
import time

import allure
import requests

from common.logger import get_logger

logger = get_logger("request")


def _log_request(method, url, kwargs):
    logger.info("%s %s", method, url)
    if "json" in kwargs:
        logger.debug("request json=%s", kwargs["json"])
    if "data" in kwargs:
        logger.debug("request data=%s", kwargs["data"])


def _log_response(response, elapsed):
    logger.info(
        "%s %s -> %s (%.3fs)",
        response.request.method,
        response.url,
        response.status_code,
        elapsed,
    )
    logger.debug("response body=%s", response.text)


def _attach_http(method, url, kwargs, response, elapsed):
    parts = [f"{method} {url}"]
    if "json" in kwargs:
        parts.append(json.dumps(kwargs["json"], ensure_ascii=False, default=str))
    if "data" in kwargs:
        parts.append(str(kwargs["data"]))
    allure.attach("\n".join(parts), "request", allure.attachment_type.TEXT)
    allure.attach(
        f"{response.status_code} ({elapsed:.3f}s)\n{response.text}",
        "response",
        allure.attachment_type.TEXT,
    )


def request(method, url, **kwargs):
    _log_request(method, url, kwargs)
    started = time.perf_counter()
    try:
        with allure.step(f"{method} {url}"):
            response = requests.request(method=method, url=url, **kwargs)
            elapsed = time.perf_counter() - started
            _log_response(response, elapsed)
            _attach_http(method, url, kwargs, response, elapsed)
    except requests.RequestException:
        logger.exception("request failed: %s %s", method, url)
        raise
    return response
