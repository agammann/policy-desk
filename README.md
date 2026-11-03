# Policy Desk

Ask questions about a small collection of PDF policies and inspect page-level evidence. This demo combines a Next.js interface with a FastAPI retrieval service and a 15-question evaluation set.

## Run locally

Requirements: Python 3.10 or newer, Node.js 20.9 or newer, and npm. Clone the repository and open a terminal in its root. On Windows PowerShell, start the API with:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

On macOS or Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python`. In a second terminal, from the repository root, start the interface:

```bash
cd frontend
npm install
npm run dev
```

Alternatively, if you use pnpm, run `pnpm install --frozen-lockfile` and `pnpm dev` in `frontend`.

Open http://localhost:3000. Upload one or more text-based PDFs, ask a question, and select a citation to inspect its source. Three fictional example policies are in `sample_data/`. The library accepts up to 10 PDFs, each up to 20 MB; scanned or encrypted PDFs are not supported. Uploaded PDFs and their index are stored locally under `backend/data/` and are excluded from Git.

## How it works

The API extracts and chunks text by PDF page. It represents chunks and questions as TF-IDF vectors and ranks them by cosine similarity. By default the answer consists of verbatim retrieved passages with numbered citations, so it runs without an API key. Optional local Ollama generation is enabled by setting `OLLAMA_MODEL` before starting the backend; `OLLAMA_URL` defaults to `http://127.0.0.1:11434`. Generated answers can still be wrong or omit qualifications, so check the cited source.

## Evaluate

With the backend running, execute `python evaluation/run.py` from the project root. Review the resulting answer and citation CSVs against the PDFs, then run `python evaluation/run.py --score evaluation/results`. See [evaluation/README.md](evaluation/README.md) for the rubric and corpus controls. The sample benchmark measures answer correctness, citation grounding and citation coverage; its 15 fictional questions are a small demonstration, not a production-quality guarantee.

To run the backend concurrency regression tests, use the virtual environment's Python from the `backend` directory: `python -m unittest discover -s tests -v`.

## Scope

This is a single-user local demo, not a multi-user document service. It has no authentication or tenant isolation. Do not expose the API or use sensitive policy documents in an untrusted environment without adding appropriate access controls, storage protections, and operational safeguards.
