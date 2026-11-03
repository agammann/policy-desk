from __future__ import annotations

import hashlib
import io
import json
import math
from collections import Counter
import os
import re
import threading
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("POLICY_DATA_DIR", BASE / "data"))
DATA.mkdir(parents=True, exist_ok=True)
INDEX = DATA / "index.json"
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_DOCUMENTS = 10
lock = threading.RLock()
app = FastAPI(title="Policy Q&A API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_methods=["*"], allow_headers=["*"])

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def load() -> list[dict]:
    if not INDEX.exists():
        return []
    try:
        value = json.loads(INDEX.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        raise HTTPException(500, "The document index could not be read.")


def save(docs: list[dict]) -> None:
    temporary = INDEX.with_suffix(".tmp")
    temporary.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
    temporary.replace(INDEX)


def public(doc: dict) -> dict:
    return {"id": doc["id"], "name": doc["name"], "pages": doc["pages"], "chunks": len(doc["chunks"])}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_page(text: str, size: int = 850, overlap: int = 120) -> list[str]:
    text = clean(text)
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        part = text[start:end].strip()
        if part:
            chunks.append(part)
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


@app.get("/api/health")
def health():
    with lock:
        docs = load()
    return {"status": "ok", "documents": len(docs), "chunks": sum(len(d["chunks"]) for d in docs)}


@app.get("/api/documents")
def documents():
    with lock:
        return {"documents": [public(d) for d in load()]}


@app.post("/api/documents")
async def upload(files: Annotated[list[UploadFile], File()]):
    errors = []
    with lock:
        docs = load()
        for file in files:
            name = Path((file.filename or "document.pdf").replace("\\", "/")).name
            if len(docs) >= MAX_DOCUMENTS:
                errors.append(f"{name}: the library holds at most {MAX_DOCUMENTS} PDFs.")
                continue
            if not name.lower().endswith(".pdf"):
                errors.append(f"{name}: only PDF files are supported.")
                continue
            contents = await file.read(MAX_FILE_BYTES + 1)
            if len(contents) > MAX_FILE_BYTES:
                errors.append(f"{name}: file exceeds the 20 MB limit.")
                continue
            if not contents.startswith(b"%PDF-"):
                errors.append(f"{name}: this is not a valid PDF.")
                continue
            identifier = hashlib.sha256(contents).hexdigest()[:20]
            if any(d["id"] == identifier for d in docs):
                errors.append(f"{name}: this PDF is already in the library.")
                continue
            try:
                reader = PdfReader(io.BytesIO(contents))
                if reader.is_encrypted:
                    raise ValueError("encrypted PDFs are not supported")
                chunks = []
                for index, page in enumerate(reader.pages):
                    for text in split_page(page.extract_text() or ""):
                        chunks.append({"page": index + 1, "text": text})
                if not chunks:
                    raise ValueError("no selectable text found; scanned PDFs require OCR")
                doc = {"id": identifier, "name": name, "pages": len(reader.pages), "chunks": chunks}
                (DATA / f"{identifier}.pdf").write_bytes(contents)
                docs.append(doc)
                save(docs)
            except Exception as exc:
                errors.append(f"{name}: could not index PDF ({str(exc)[:160]}).")
        return {"documents": [public(d) for d in docs], "errors": errors}


@app.delete("/api/documents/{document_id}")
def delete(document_id: str):
    with lock:
        docs = load()
        remaining = [d for d in docs if d["id"] != document_id]
        if len(remaining) == len(docs):
            raise HTTPException(404, "Document not found.")
        save(remaining)
        (DATA / f"{document_id}.pdf").unlink(missing_ok=True)
    return {"documents": [public(d) for d in remaining]}


@app.get("/api/documents/{document_id}/file")
def pdf_file(document_id: str):
    with lock:
        doc = next((d for d in load() if d["id"] == document_id), None)
        path = DATA / f"{document_id}.pdf"
        if not doc or not path.is_file():
            raise HTTPException(404, "Document not found.")
        return FileResponse(path, media_type="application/pdf", filename=doc["name"], content_disposition_type="inline")


@app.post("/api/reset")
def reset():
    with lock:
        docs = load()
        save([])
        for doc in docs:
            (DATA / f"{doc['id']}.pdf").unlink(missing_ok=True)
    return {"documents": []}


STOP_WORDS = set("a an and are as at be been but by can could did do does for from had has have how i if in into is it its may of on or our should that the their then there these they this those to was we were what when where which who will with would you your".split())


def terms(text: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]
    # Normalize common inflections so "request" matches "requests", etc.
    def normalize(word: str) -> str:
        if len(word) > 5 and word.endswith("ies"):
            return word[:-3] + "y"
        if len(word) > 5 and word.endswith("ing"):
            return word[:-3]
        if len(word) > 4 and word.endswith("ed"):
            return word[:-2]
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word
    words = [normalize(w) for w in words]
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


def cosine_scores(question: str, documents: list[str]) -> list[float]:
    """Sparse TF-IDF cosine similarity over the uploaded passages."""
    tokenized = [terms(document) for document in documents]
    counts = [Counter(row) for row in tokenized]
    frequency = Counter(term for row in counts for term in row)
    n = len(documents)
    idf = {term: math.log((1 + n) / (1 + freq)) + 1 for term, freq in frequency.items()}
    query = Counter(terms(question))
    qvector = {term: (1 + math.log(count)) * idf[term] for term, count in query.items() if term in idf}
    qnorm = math.sqrt(sum(value * value for value in qvector.values()))
    if not qnorm:
        return [0.0] * n
    scores = []
    for row in counts:
        vector = {term: (1 + math.log(count)) * idf[term] for term, count in row.items()}
        norm = math.sqrt(sum(value * value for value in vector.values()))
        scores.append(sum(qvalue * vector.get(term, 0) for term, qvalue in qvector.items()) / (qnorm * norm) if norm else 0.0)
    return scores


def retrieve(question: str, docs: list[dict]) -> list[dict]:
    chunks = [{**chunk, "document_id": d["id"], "document_name": d["name"]} for d in docs for chunk in d["chunks"]]
    if not chunks:
        return []
    scores = cosine_scores(question, [chunk["text"] for chunk in chunks])
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    selected = []
    for index in ranked:
        if scores[index] < max(0.025, scores[ranked[0]] * 0.65):
            break
        item = chunks[index]
        if any(c["document_id"] == item["document_id"] and c["page"] == item["page"] for c in selected):
            continue
        selected.append({**item, "score": round(float(scores[index]), 4)})
        if len(selected) == 4:
            break
    return selected


def excerpt(question: str, text: str) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if s.strip()]
    if len(sentences) < 2:
        return text
    scores = cosine_scores(question, sentences)
    best = max(range(len(sentences)), key=lambda i: scores[i])
    # The next sentence often carries exceptions or deadlines that qualify a policy.
    # Keep it verbatim so the reader can judge the complete source passage.
    return " ".join(sentences[best:best + 2])[:1000]


def generate(question: str, citations: list[dict]) -> str | None:
    # Opt in to a locally running Ollama model; the default requires no external service.
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    if not model:
        return None
    context = "\n\n".join(f"[{c['id']}] {c['document_name']}, page {c['page']}: {c['text']}" for c in citations)
    prompt = ("Answer the question using only the evidence below. Cite every factual claim using [1], [2], etc. "
              "If the evidence is insufficient, say so. Never invent policy details.\n\n"
              f"Evidence:\n{context}\n\nQuestion: {question}\nAnswer:")
    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/generate", json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}})
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            # Don't present an unreferenced model response as grounded.
            if result and re.search(r"\[[1-" + str(len(citations)) + r"]\]", result):
                return result
    except (httpx.HTTPError, ValueError):
        pass
    return None


@app.post("/api/ask")
def ask(body: Question):
    question = body.question.strip()
    if not question:
        raise HTTPException(422, "Enter a question.")
    with lock:
        docs = load()
    if not docs:
        raise HTTPException(400, "Upload at least one text-based PDF first.")
    found = retrieve(question, docs)
    if not found:
        return {"answer": "I couldn't find relevant evidence in the uploaded documents. Try a more specific question or check that the right policy is uploaded.", "citations": [], "mode": "extractive"}
    citations = [{"id": index + 1, "document_id": item["document_id"], "document_name": item["document_name"], "page": item["page"], "text": excerpt(question, item["text"]), "score": item["score"]} for index, item in enumerate(found)]
    answer = generate(question, citations)
    if answer:
        return {"answer": answer, "citations": citations, "mode": "generated"}
    # Excerpts are verbatim, rather than an unsupported model synthesis.
    answer = "I found these related passages. They may not answer every part of your question; check the cited source for context:\n\n" + "\n\n".join(f"{c['text']} [{c['id']}]" for c in citations[:3])
    return {"answer": answer, "citations": citations[:3], "mode": "extractive"}

