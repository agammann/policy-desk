# Initial benchmark run

Run against the default local extractive mode on November 2, 2026, with only the three supplied sample PDFs indexed. The review applied the reference answers in `questions.json` as a strict completeness standard, including stated qualifications. No generative model was configured.

- Answer correctness: **5/15 (33.3%)**.
- Citation grounding: **40/40 (100%)**; each returned extract matched the cited PDF page and supported the verbatim passage in the answer.
- Citation coverage: **15/15 (100%)** answers had citations.

These grounding and coverage numbers do not measure relevance: many extracted passages were unrelated to the question. The run exposed a frequent failure to include the next sentence when it contained a required condition or deadline. The same assistant authored the dataset and performed the review, so this is a small development benchmark, not independent validation.
