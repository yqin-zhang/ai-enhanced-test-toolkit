from jsonschema import ValidationError, validate

from common.logger import get_logger

logger = get_logger("assert")


def assert_json(response, status_code, schema=None):
    """状态码 → 解析 body → 可选 schema。返回 body。"""
    if response.status_code != status_code:
        logger.error(
            "status expected=%s actual=%s body=%s",
            status_code,
            response.status_code,
            response.text,
        )
    assert response.status_code == status_code

    try:
        body = response.json()
    except ValueError:
        logger.error("response is not json: %s", response.text)
        raise

    if schema is not None:
        title = schema.get("title") or "untitled"
        try:
            validate(instance=body, schema=schema)
        except ValidationError as exc:
            logger.error("schema failed [%s]: %s", title, exc.message)
            raise
        logger.debug("schema ok [%s]", title)

    return body
