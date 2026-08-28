"""RAG 子包：用例文档切块入库与关键词检索。不要 from ai_tool.rag 再转 ingest，以免 -m 循环加载。

离线（ingest）：① load → ② chunk → ③ persist → chunks.json
在线（retrieve）：persist.load_chunks → ④ tokenize → ⑤ score → ⑥ retriever
编排：demo_task 使用 hits，不在本包生成用例。
"""
