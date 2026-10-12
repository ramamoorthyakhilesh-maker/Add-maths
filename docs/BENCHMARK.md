# Benchmark

Which free model is worth using? `bench/bench.py` asks each model the same generated questions and scores the answers with the same checker Edith uses.

## Method

- Raw models: no tools, no hints, temperature 0. This is a floor for Edith, who has tools and a hint ladder.
- Questions come from `tools/gen.py`, spread over every topic and level. The suite is fixed by a seed, so models see the same questions.
- The model must finish with a line `ANSWER: ...`. LaTeX in the answer is converted to plain text before marking.
- Scoring uses `gen.verdict`, so the answer key is the one the tests check.
- The report uses only questions that every model answered, with Wilson 95% intervals, and shows per-level and per-topic tables.

## Run it

```
export OPENROUTER_API_KEY=...            # PowerShell: $env:OPENROUTER_API_KEY = "..."
python bench/bench.py list-free
python bench/bench.py run --models-file bench/models.txt --levels medium,hard
python bench/bench.py report             # writes bench/REPORT.md
```

The free tier allows 50 requests a day unless you have bought credits, so a large run takes several days. Run the same command each day. It resumes where it stopped and retries requests that failed with an error. A rejected API key stops the run at once.

## Results

Not published yet. Add `bench/REPORT.md` here once a run has at least 40 questions in common across the models.
