import hashlib
import json
import os
import re
import chromadb
from app.core.config import settings

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "question_bank.json")

_VOCAB_SIZE = 384  # matches typical small embedding dim, purely a design choice


class HashingEmbeddingFunction:
    """
    Deterministic, dependency-free embedding function.

    Why not the default ONNX MiniLM model? It requires downloading ~90MB from
    an external host at first use, which is unreliable on constrained networks
    (sandboxes, some free-tier hosts) and adds cold-start latency to a demo.
    A hashing-trick bag-of-words vector needs no downloads, is fully
    deterministic, and is more than sufficient for matching short interview
    questions against a role/topic -- the retrieval task here doesn't need
    deep semantic embeddings, just reliable keyword-level similarity.
    """

    def name(self) -> str:
        return "hashing-bow-v1"

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors = []
        for text in input:
            vec = [0.0] * _VOCAB_SIZE
            tokens = re.findall(r"[a-z0-9]+", text.lower())
            for tok in tokens:
                idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % _VOCAB_SIZE
                vec[idx] += 1.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
_collection = _client.get_or_create_collection(
    name="question_bank",
    embedding_function=HashingEmbeddingFunction(),
)


def seed_if_empty():
    """Load the question bank into Chroma on first run (idempotent)."""
    if _collection.count() > 0:
        return
    with open(_DATA_PATH) as f:
        items = json.load(f)
    _collection.add(
        ids=[f"q{i}" for i in range(len(items))],
        documents=[it["question"] for it in items],
        metadatas=[{"role": it["role"], "type": it["type"], "topic": it["topic"]} for it in items],
    )


def retrieve_questions(role: str, n: int = 5, q_type: str | None = None):
    """Retrieve the most relevant interview questions for a target role."""
    where = {"role": role} if not q_type else {"$and": [{"role": role}, {"type": q_type}]}
    results = _collection.query(
        query_texts=[f"interview questions for {role}"],
        n_results=n,
        where=where,
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return [{"question": d, **m} for d, m in zip(docs, metas)]


def add_custom_questions(role: str, questions: list[dict]):
    """Allow adding college-specific / user-specific questions to the bank."""
    start = _collection.count()
    _collection.add(
        ids=[f"custom{start + i}" for i in range(len(questions))],
        documents=[q["question"] for q in questions],
        metadatas=[{"role": role, "type": q.get("type", "technical"), "topic": q.get("topic", "general")} for q in questions],
    )
