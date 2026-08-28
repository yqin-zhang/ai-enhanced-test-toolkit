"""RAG 模块④ 分词：英文按词，中文二字切。

给 score.py 用，不装 jieba。检索时 retriever 不直接调本文件。
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[A-Za-z0-9_./-]+")
_CJK = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """英文 token + 连续汉字 2-gram。"""
    lowered = text.lower()
    tokens = [m.group(0) for m in _WORD.finditer(lowered)]
    for run in _CJK.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens
