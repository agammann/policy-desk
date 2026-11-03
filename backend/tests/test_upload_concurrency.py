"""Regression coverage for simultaneous document uploads."""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
import main  # noqa: E402


class SynchronizedUpload:
    """Force two uploads to yield together before their bytes are read."""

    def __init__(self, path: Path, gate: asyncio.Event, counter: list[int]):
        self.filename = path.name
        self.contents = path.read_bytes()
        self.gate = gate
        self.counter = counter

    async def read(self, size: int) -> bytes:
        self.counter[0] += 1
        if self.counter[0] == 2:
            self.gate.set()
        await self.gate.wait()
        return self.contents[:size]


class ConcurrentUploadTest(unittest.IsolatedAsyncioTestCase):
    async def test_simultaneous_uploads_preserve_both_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_data, old_index = main.DATA, main.INDEX
            main.DATA, main.INDEX = Path(tmp), Path(tmp) / "index.json"
            try:
                samples = BACKEND.parent / "sample_data"
                gate, counter = asyncio.Event(), [0]
                files = [
                    SynchronizedUpload(samples / name, gate, counter)
                    for name in ("remote-work-policy.pdf", "employee-leave-policy.pdf")
                ]
                results = await asyncio.wait_for(
                    asyncio.gather(*(main.upload([file]) for file in files)), timeout=5
                )
                self.assertTrue(all(not result["errors"] for result in results))
                documents = main.load()
                self.assertEqual({doc["name"] for doc in documents}, {file.filename for file in files})
                for document in documents:
                    self.assertTrue((main.DATA / f'{document["id"]}.pdf').is_file())
            finally:
                main.DATA, main.INDEX = old_data, old_index

    async def test_simultaneous_duplicate_is_indexed_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_data, old_index = main.DATA, main.INDEX
            main.DATA, main.INDEX = Path(tmp), Path(tmp) / "index.json"
            try:
                sample = BACKEND.parent / "sample_data" / "remote-work-policy.pdf"
                gate, counter = asyncio.Event(), [0]
                files = [SynchronizedUpload(sample, gate, counter) for _ in range(2)]
                results = await asyncio.wait_for(
                    asyncio.gather(*(main.upload([file]) for file in files)), timeout=5
                )
                self.assertEqual(len(main.load()), 1)
                self.assertEqual(sum(len(result["errors"]) for result in results), 1)
                self.assertTrue(any("already in the library" in error for result in results for error in result["errors"]))
            finally:
                main.DATA, main.INDEX = old_data, old_index


if __name__ == "__main__":
    unittest.main()
