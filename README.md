# ai-enhanced-test-toolkit
Demo for test‑development：Contains self‑developed device management service, pytest API automation, MCP+RAG AI‑driven interface testing tool.

# AI‑Enhanced‑Test‑Toolkit
> 测试开发秋招个人Demo项目

## 项目介绍
本仓库包含三套模块：
1. **device_server.py**：自研设备管理模拟后端服务(FastAPI+SQLite)，作为被测系统，提供设备注册、状态修改、删除查询等REST接口。
2. **device‑api‑automation【项目1】**：基于pytest+requests实现传统接口自动化。完成正向、异常、边界场景测试，支持接口‑数据库一致性校验，输出测试报告。
3. **mcp‑rag‑ai‑tester【项目2｜核心主项目】** 基于MCP协议+RAG实现AI接口测试工具。
- RAG解析OpenAPI接口文档，检索测试相关信息
- Agent生成测试用例，通过MCP调用可插拔Skill执行http请求、数据库校验
- 支持降级运行：大模型不可用时，可脱离AI直接执行回归用例
- 输出Markdown格式测试报告

## 技术栈
Python3 | FastAPI | SQLite | Pytest | Requests | MCP | Chroma(RAG) | SQLAlchemy

## 项目边界 & 后续扩展方向
本项目为个人Demo，聚焦接口层自动化。
计划扩展：
- 接入Playwright实现UI‑Skill，完成GUI自动化
- 引入Reranker优化检索效果
- 增加自动缺陷报告生成能力