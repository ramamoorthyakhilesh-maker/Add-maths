# Edith benchmark report

Generated 2026-10-15. Raw models, no tools, no hints, temperature 0.
Questions answered by every model (the fair comparison set): 67. Models: 3.

## Overall (common set)

| Rank | Model | Correct | Accuracy | 95% interval | Median seconds | Format failures | Request errors |
|---|---|---|---|---|---|---|---|
| 1 | k2-horizon:free | 64/67 | 96% | 88% to 98% | 16 | 3 | 0 |
| 2 | agnes-3.0-flash:free | 64/67 | 96% | 88% to 98% | 18 | 3 | 0 |
| 3 | deepseek-v4.1-flash:free | 64/67 | 96% | 88% to 98% | 23 | 3 | 5 |

Format failures are answers the checker could not read, or answers with a missing ANSWER line, ambiguous division, or a decimal where an exact value was needed. They count as wrong.

## Accuracy by level

| level | agnes-3.0-flash:free | deepseek-v4.1-flash:fr | k2-horizon:free |
|---|---|---|---|
| easy | 22/24 | 23/24 | 23/24 |
| medium | 21/22 | 21/22 | 21/22 |
| hard | 21/21 | 20/21 | 20/21 |

## Accuracy by topic

| topic | agnes-3.0-flash:free | deepseek-v4.1-flash:fr | k2-horizon:free |
|---|---|---|---|
| area | 3/3 | 3/3 | 3/3 |
| binom | 3/3 | 3/3 | 3/3 |
| cgeo | 3/3 | 3/3 | 3/3 |
| circ | 1/3 | 1/3 | 1/3 |
| diff | 3/3 | 3/3 | 3/3 |
| factor | 3/3 | 3/3 | 3/3 |
| func | 3/3 | 2/3 | 3/3 |
| ineq | 3/3 | 3/3 | 3/3 |
| integ | 3/3 | 3/3 | 3/3 |
| kin | 2/2 | 2/2 | 1/2 |
| lin | 3/3 | 3/3 | 3/3 |
| line | 2/2 | 2/2 | 2/2 |
| log | 3/3 | 3/3 | 3/3 |
| mod | 2/2 | 2/2 | 2/2 |
| perm | 2/2 | 2/2 | 2/2 |
| prog | 3/3 | 3/3 | 3/3 |
| quad | 3/3 | 3/3 | 3/3 |
| rates | 2/2 | 2/2 | 2/2 |
| simul | 2/3 | 3/3 | 3/3 |
| stat | 3/3 | 3/3 | 3/3 |
| tangent | 3/3 | 3/3 | 3/3 |
| tgraph | 3/3 | 3/3 | 3/3 |
| trig | 3/3 | 3/3 | 3/3 |
| vec | 3/3 | 3/3 | 3/3 |

## Suggested fallback order

Highest accuracy first, ties broken by speed. Drop models with a wide interval and low accuracy, and models with many request errors:

1. k2-horizon:free
2. agnes-3.0-flash:free
3. deepseek-v4.1-flash:free

## What this does and does not show

- It measures raw model arithmetic and algebra on generated 0606-style questions. Edith also has the question generator, the answer checker and the syllabus notes, so her real accuracy on practice questions is higher than these numbers.
- It does not measure how well a model teaches. Read a few chat transcripts for that.
- Small samples are noisy. The interval column shows how much. Free models also change or disappear, so re-run before quoting a result.
- Questions come from tools/gen.py with fixed seeds, so the run can be repeated exactly (suite seed shown in the results file IDs).
