"""编排模块：离线跑 REG-P01（不接 LLM）。

顺序：retrieve_knowledge → call_api 注册 → query_device 对库 → write_report → DELETE 清理。
入口：python -m ai_tool.demo_task（须先 ingest，且 device_server 已启动）
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from ai_tool import load_config
from ai_tool.mcp_client import ToolHub

TASK_NAME = "验证设备注册正向（REG-P01）"
QUERY = "注册设备 正向 默认 offline REG-P01"


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _server_up(hub: ToolHub) -> dict[str, Any]:
    probe = hub.call_api("GET", "/device/list")
    if probe.get("error") == "connection_refused" or not probe.get("ok"):
        print(probe.get("hint") or "被测服务不可达。")
        print("请先在仓库根目录运行: python test_projects/device_server.py")
        raise SystemExit(2)
    return probe


def _build_report(
    *,
    device_id: str,
    rag: dict[str, Any],
    http: dict[str, Any],
    db: dict[str, Any],
    passed: bool,
    reasons: list[str],
) -> str:
    hit_lines = []
    for hit in rag.get("hits") or []:
        snippet = (hit.get("text") or "").replace("\n", " ").strip()[:180]
        hit_lines.append(f"- **{hit.get('title')}** (score={hit.get('score')}): {snippet}")
    if not hit_lines:
        hit_lines.append("- （无命中，请先 `python -m ai_tool.rag.ingest`）")

    verdict = "PASS" if passed else "FAIL"
    return "\n".join(
        [
            f"- 任务：{TASK_NAME}",
            f"- 设备 ID：`{device_id}`",
            f"- 结论：**{verdict}**",
            "",
            "## 核对",
            *[f"- {item}" for item in reasons],
            "",
            "## RAG 检索",
            f"- query：`{rag.get('query', QUERY)}`",
            *hit_lines,
            "",
            "## HTTP",
            "```json",
            _dump(http),
            "```",
            "",
            "## DB",
            "```json",
            _dump(db),
            "```",
        ]
    )


def run_reg_p01() -> int:
    cfg = load_config()
    if cfg.get("llm", {}).get("enabled"):
        print("llm.enabled=true，但本轮骨架不接模型，仍走离线编排。")

    hub = ToolHub()
    _server_up(hub)

    # 1. RAG：从接口测试.md 检索注册正向
    rag = hub.retrieve_knowledge(QUERY)
    if rag.get("error") == "index_missing":
        print(rag.get("hint"))
        return 1

    device_id = f"ai_reg_{uuid.uuid4().hex[:8]}"  # 避免和 pytest 的 dev002 冲突
    payload = {
        "device_id": device_id,
        "device_name": "红外传感器",
        "device_type": "sensor",
    }

    http: dict[str, Any] = {}
    db: dict[str, Any] = {}
    reasons: list[str] = []
    passed = False
    try:
        # 2. API Skill：真实注册  3. DB Skill：核对默认 offline
        http = hub.call_api("POST", "/device/register", json_body=payload)
        body = http.get("body") if isinstance(http.get("body"), dict) else {}
        db = hub.query_device(device_id)

        rag_text = " ".join(
            f"{h.get('title', '')} {h.get('text', '')}" for h in (rag.get("hits") or [])
        )
        checks = [
            (bool(rag.get("hits")), "RAG 有命中（接口测试文档）"),
            ("REG-P01" in rag_text or "注册" in rag_text, "RAG 命中注册正向相关内容"),
            (http.get("ok") is True, "HTTP 调用成功"),
            (http.get("status_code") == 200, f"HTTP 200，实际 {http.get('status_code')}"),
            (body.get("code") == 0, f"body.code=0，实际 {body.get('code')}"),
            (body.get("msg") == "注册成功", f"msg=注册成功，实际 {body.get('msg')}"),
            (
                (body.get("data") or {}).get("device_id") == device_id,
                "响应 data.device_id 与请求一致",
            ),
            (db.get("found") is True, "库中存在该 device_id"),
            (
                (db.get("device") or {}).get("status") == "offline",
                f"库中默认 status=offline，实际 {(db.get('device') or {}).get('status')}",
            ),
            (
                (db.get("device") or {}).get("device_name") == payload["device_name"],
                "库中 device_name 与注册一致",
            ),
        ]
        for ok, reason in checks:
            reasons.append(("通过：" if ok else "失败：") + reason)
        passed = all(ok for ok, _ in checks)
    finally:
        body_md = _build_report(
            device_id=device_id,
            rag=rag,
            http=http,
            db=db,
            passed=passed,
            reasons=reasons or ["未完成核对"],
        )
        try:
            hub.write_report(TASK_NAME, body_md)  # 4. 出报告
        finally:
            hub.call_api("DELETE", f"/device/{device_id}")  # 无论成败都清理

    return 0 if passed else 1


def main() -> None:
    raise SystemExit(run_reg_p01())


if __name__ == "__main__":
    main()
