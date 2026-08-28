"""RAG 模块⑤ 打分：BM25 + 查询短语字面加分。

分词走 tokenize.py；对外入口是 score_documents。
"""

from __future__ import annotations

import math
import re
from collections import Counter

from ai_tool.rag.tokenize import tokenize


def _idf(df: int, n_docs: int) -> float:
    return math.log(1 + (n_docs - df + 0.5) / (df + 0.5))


def bm25_scores(query: str, docs: list[str]) -> list[float]:
    """对每个文档返回一个 BM25 分数。"""
    q_tokens = tokenize(query)
    if not q_tokens or not docs:
        return [0.0] * len(docs)

    doc_tokens = [tokenize(doc) for doc in docs]
    n_docs = len(doc_tokens)
    avgdl = sum(len(toks) for toks in doc_tokens) / n_docs
    df: Counter[str] = Counter()
    for toks in doc_tokens:
        df.update(set(toks))

    k1, b = 1.5, 0.75
    scores: list[float] = []
    q_set = set(q_tokens)
    for toks in doc_tokens:
        tf = Counter(toks)
        dl = len(toks) or 1
        score = 0.0
        for term in q_set:
            if tf[term] == 0:
                continue
            denom = tf[term] + k1 * (1 - b + b * dl / avgdl)
            score += _idf(df[term], n_docs) * (tf[term] * (k1 + 1) / denom)
        scores.append(score)
    return scores


def add_phrase_bonus(query: str, docs: list[str], scores: list[float]) -> list[float]:
    """整词/短语命中加分，避免只靠中文 2-gram。"""
    phrases = [p for p in re.split(r"\s+", query.strip()) if p]
    boosted = list(scores)
    for i, text in enumerate(docs):
        bonus = sum(1.5 for p in phrases if p.lower() in text.lower())
        boosted[i] += bonus
    return boosted


def score_documents(query: str, docs: list[str]) -> list[float]:
    """BM25 之后再加短语加分，供 retriever 排序。"""
    return add_phrase_bonus(query, docs, bm25_scores(query, docs))
