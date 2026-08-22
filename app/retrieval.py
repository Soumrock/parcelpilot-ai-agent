from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(frozen=True)
class Document:
    name: str
    path: Path
    status: str
    authority: str
    effective_date: str | None
    account_id: str | None
    content: str


class DocumentRetriever:
    """Small, transparent retrieval layer for the supplied assessment documents.

    We keep source metadata explicit so the agent can reason about authority and
    freshness. Deprecated policy is retained as historical evidence but excluded
    from normal current-state retrieval.
    """

    SOURCE_RULES = {
        "01_Support_Policy_v3_CURRENT.pdf": {"status": "CURRENT", "authority": "current_support_policy", "effective": "2026-05-01", "account_id": None},
        "02_Support_Policy_v2_DEPRECATED.pdf": {"status": "DEPRECATED", "authority": "historical_policy", "effective": "2025-01-01", "account_id": None},
        "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {"status": "CURRENT", "authority": "current_sop", "effective": "2026-06-15", "account_id": None},
        "04_Product_Operations_Guide_and_Known_Issues.pdf": {"status": "CURRENT", "authority": "current_product_docs", "effective": "2026-08-14", "account_id": None},
        "05_Northstar_Logistics_Enterprise_Agreement.pdf": {"status": "ACTIVE", "authority": "signed_customer_agreement", "effective": "2026-01-01", "account_id": "ACCT-001"},
        "06_LumenWorks_Service_Agreement.pdf": {"status": "ACTIVE", "authority": "signed_customer_agreement", "effective": "2026-03-01", "account_id": "ACCT-002"},
    }

    def __init__(self, data_dir: Path):
        self.documents: list[Document] = []
        for path in sorted(data_dir.glob("*.pdf")):
            rule = self.SOURCE_RULES.get(path.name)
            if not rule:
                continue
            text = self._extract(path)
            self.documents.append(Document(path.name, path, rule["status"], rule["authority"], rule["effective"], rule["account_id"], text))
        self.chunks: list[dict[str, Any]] = []
        for doc in self.documents:
            self.chunks.extend(self._chunk(doc))
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), lowercase=True)
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in self.chunks]) if self.chunks else None

    @staticmethod
    def _extract(path: Path) -> str:
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    def _chunk(self, doc: Document) -> list[dict[str, Any]]:
        """Keep each supplied PDF as one authoritative retrieval unit.

        The assessment documents are short (one page each). Keeping the full
        document together prevents PDF line-wrap artifacts from separating
        critical clauses and values, such as a contract's threshold and credit
        amount, into different retrieval chunks.
        """
        text = doc.content.strip()
        if not text:
            return []
        return [{
            "doc": doc.name,
            "status": doc.status,
            "authority": doc.authority,
            "effective_date": doc.effective_date,
            "account_id": doc.account_id,
            "text": text,
        }]

    @staticmethod
    def _source_rank(item: dict[str, Any]) -> int:
        ranks = {
            "signed_customer_agreement": 5,
            "current_support_policy": 4,
            "current_sop": 4,
            "current_product_docs": 3,
            "historical_policy": 1,
        }
        return ranks.get(item["authority"], 0)

    def search(self, query: str, account_id: str | None = None, include_deprecated: bool = False, top_k: int = 6) -> dict[str, Any]:
        if not self.chunks:
            return {"results": [], "reliability_note": "No documents loaded."}
        import numpy as np
        q = self.vectorizer.transform([query])
        scores = (self.matrix @ q.T).toarray().ravel()
        ranked = []
        for idx, score in enumerate(scores):
            item = self.chunks[idx]
            if item["status"] == "DEPRECATED" and not include_deprecated:
                continue
            if account_id and item["account_id"] not in (None, account_id):
                continue
            lexical = float(score)
            source_bonus = self._source_rank(item) * 0.05
            ranked.append((lexical + source_bonus, item))
        ranked.sort(key=lambda x: x[0], reverse=True)
        results = [{"score": round(score, 4), **item} for score, item in ranked[:top_k]]
        return {
            "results": results,
            "source_precedence": [
                "signed_customer_agreement",
                "current_support_policy",
                "current_product_docs",
                "historical_ticket_context",
            ],
            "reliability_note": "Deprecated policy is excluded from normal current-state retrieval. Historical guidance should not be treated as policy authority.",
        }
