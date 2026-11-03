# Benchmark results

Run against the default local extractive mode on November 2, 2026, with only the three supplied fictional sample PDFs indexed. The review applied the reference answers in `questions.json` as a strict completeness standard, including the stated qualifications. No generative model was configured.

| Measure | Initial run | After retrieval changes |
| --- | ---: | ---: |
| Answer correctness | 5/15 (33.3%) | 15/15 (100%) |
| Citation grounding | 40/40 (100%) | 15/15 (100%) |
| Citation coverage | 15/15 (100%) | 15/15 (100%) |

Grounding means the returned extract matched its cited PDF page and supported the quoted answer. It does not by itself measure whether a passage is relevant. Many initial passages were unrelated; in the final run, two correct answers still included an unrelated neighboring section.

The same assistant authored the dataset and performed the review, so this is a small development benchmark rather than independent validation. Retrieval improvements were made after inspecting this dataset and its first-run results, so these are in-sample results, not estimates of performance on new policies or questions. `answers.csv`, `citations.csv`, and `responses.json` preserve the final review and responses; the initial run is in `../baseline/`.
