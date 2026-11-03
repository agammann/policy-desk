# Evaluation

The 15 questions in `questions.json` cover all three fictional sample PDFs. They provide reference answers, expected document/page, and evidence to help a reviewer. These policies are invented for demonstration, not company guidance.

Start the FastAPI service, then from the project root run:

```bash
python evaluation/run.py
```

The script uploads the three sample PDFs and asks each question. Use `--no-upload` if they are already in the active corpus. You can set `--base-url` and `--output` if needed. The script does not clear the existing corpus; for a controlled benchmark start with a fresh corpus and use only the supplied sample PDFs. Running the script again overwrites its result files by default.

Review the generated files in `evaluation/results/` against the source PDFs:

- In `answers.csv`, mark `correct_1_or_0` as 1 only when the response is factually correct and complete against the reference, including material conditions; otherwise mark 0. An unsupported but accidentally correct answer still scores 1 here: grounding is a separate metric.
- In `citations.csv`, mark `grounded_1_or_0` as 1 only when the cited page and quoted text actually support the answer claim associated with that citation; mark unrelated, inaccurate, or unverifiable citations 0. Check the PDF page itself, not just the returned text. Add notes for ambiguous cases.

Then run:

```bash
python evaluation/run.py --score evaluation/results
```

The score is the share of the 15 answers marked correct and the share of returned citations marked grounded. It also reports citation coverage, the share of answers with at least one citation, because grounding alone can look artificially strong if the system cites rarely. Grounding is undefined if no citations are returned. The script refuses to score until all review rows are labeled; it does not claim to judge semantic correctness automatically. This small, hand-authored benchmark is useful for iteration, not a comprehensive production evaluation. Treat document retrieval and answers as nondeterministic when using a generative model.
