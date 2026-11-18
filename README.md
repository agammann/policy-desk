# Policy Desk

Ask questions about a small collection of PDF policies and inspect the passages and pages behind the answers. Policy Desk runs on your computer and includes three fictional policies to try.

## Run locally

Use Python 3.12.x, Node.js 22.13 or newer, and pnpm 11.25.0. The locked setup was tested on Windows with Python 3.12.14 and Node.js 24.19.0. Clone the repository or extract the GitHub source ZIP. Open PowerShell in the project root and start the API.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.lock
.\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The checked-in `requirements.lock` records the complete package resolution tested with Python 3.12.14 on Windows. Install it for the reproducible setup above; `requirements.txt` keeps the allowed direct dependency ranges for intentional refreshes. To refresh, resolve those ranges in a new virtual environment, run the backend tests, then regenerate and review `requirements.lock` with `python -m pip freeze`. Other Python/platform combinations should be checked before replacing the tested resolution.

On macOS or Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python`. In a second terminal, from the repository root, install and run the interface using the checked-in frontend lockfile.

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://127.0.0.1:3000`. Click **Upload PDFs**, add `sample_data/employee-leave-policy.pdf`, and ask “How many annual leave days do full-time employees receive?” Select a numbered citation to read the excerpt in **Sources**, or use its link to open the PDF at the cited page. `pnpm build` and `pnpm start` run the production build locally with the same backend.

The library accepts up to 10 text-based PDFs, each up to 20 MB. Scanned and encrypted PDFs are unsupported. Uploaded PDFs and their index are stored under `backend/data/` and persist across restarts. Set `POLICY_DATA_DIR` before starting the backend to use a separate library. Conversations are kept in the browser page and reset on reload.

## How it works

The API extracts and chunks text by PDF page. It represents chunks and questions as TF-IDF vectors and ranks them by cosine similarity. By default the answer consists of verbatim retrieved passages with numbered citations, so it runs without an API key. Optional local Ollama generation is enabled by setting `OLLAMA_MODEL` before starting the backend; `OLLAMA_URL` defaults to `http://127.0.0.1:11434`. Generated answers can still be wrong or omit qualifications, so check the cited source.

## Evaluate

With the backend running, execute `python evaluation/run.py` from the project root. Review the resulting answer and citation CSVs against the PDFs, then run `python evaluation/run.py --score evaluation/results`. See [evaluation/README.md](evaluation/README.md) for the rubric and corpus controls. The sample benchmark measures answer correctness, citation grounding and citation coverage; its 15 fictional questions are a small demonstration, not a production-quality guarantee.

To run the backend concurrency regression tests, use the virtual environment's Python from the `backend` directory: `python -m unittest discover -s tests -v`.

## Scope

Policy Desk is a single-user local application. It has no authentication or tenant isolation. Keep both services on loopback and use fictional or otherwise non-sensitive documents in an untrusted environment.
