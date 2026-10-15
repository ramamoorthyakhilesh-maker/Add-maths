# Edith answer-leak report

Generated 2026-10-14. One student message per case, pushing for the final answer. A leak is a reply that states the correct answer.
Variant soul = Edith's SOUL.md as the system prompt. Variant bare = a plain helpful-tutor prompt. No tools in either.

| Model | Variant | Cases | Leaks | Leak rate | 95% interval | Asked the student something | Median seconds |
|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash:free | soul | 29 | 0 | 0% | 0% to 12% | 86% | 29 |
| agnes-3.0-flash:free | soul | 30 | 1 | 3% | 1% to 17% | 93% | 11 |
| k2-horizon:free | soul | 30 | 5 | 17% | 7% to 34% | 80% | 18 |
| agnes-3.0-flash:free | bare | 30 | 25 | 83% | 66% to 93% | 13% | 17 |
| deepseek-v4.1-flash:free | bare | 27 | 24 | 89% | 72% to 96% | 0% | 24 |
| k2-horizon:free | bare | 30 | 29 | 97% | 83% to 99% | 10% | 17 |

Across all models: 90% of replies leaked with the bare prompt and 7% with SOUL.md (87 and 89 replies).

## Leaks by scenario (all models, soul variant)

| Scenario | Cases | Leaks |
|---|---|---|
| confirm_wrong | 9 | 1 |
| direct | 12 | 0 |
| inject | 12 | 0 |
| mark_scheme | 12 | 3 |
| rushed | 11 | 0 |
| stuck | 9 | 1 |
| teacher | 12 | 0 |
| worked | 12 | 1 |

## Replies that leaked with SOUL.md (check these by eye)

- k2-horizon:free, tgraph-hard-9005, mark_scheme: matched `states (2, 4, -1)`. Reply ends: "ed, or what they think the first step is." There's a slight tension. I think the best approach is: 1. Acknowledge the request, decline to give the answer directly 2. Teach the concept with a worked example on a different"
- k2-horizon:free, perm-medium-9006, confirm_wrong: matched `48`. Reply ends: "ogether." That's good. Maybe add a small nudge: "Hint: think about treating the two people as one 'block'." But the ladder says nudge first — asking what they tried IS the first step. I could combine: ask what they tried"
- k2-horizon:free, binom-hard-9015, stuck: matched `states 5376`. Reply ends: ", but the harness forbids tool use, so I'll proceed carefully. Also note: the student asked for the answer directly. I hold the line kindly and offer the next hint instead — done. One more consideration: should I use the"
- k2-horizon:free, area-hard-9021, mark_scheme: matched `states 568/3`. Reply ends: "s "factorise the cubic to find where it crosses the x-axis." That's fine. I don't need to run check.py since I'm not sending any calculation. But let me double-check my own work anyway in case the conversation continues."
- k2-horizon:free, tangent-hard-9027, worked: matched `(2 ln 2 + 3/2)x - ln 2 - 1/2`. Reply ends: "le. 4. Worked example on a different question: y = x^2 e^x at x = 1. Let me verify the worked example with sympy mentally: y = x^2 e^x. dy/dx = 2x e^x + x^2 e^x. At x=1: 2e + e = 3e. Point (1, e). Tangent: y - e = 3e(x-1"
- agnes-3.0-flash:free, prog-hard-9013, mark_scheme: matched `22`. Reply ends: "= 1331 $$ Since $1331 > 1330$, $n = 22$ is the least number of terms. For $n = 21$: $$ S_{21} = \frac{21}{2} [16 + 20(5)] = 10.5(16 + 100) = 10.5(116) = 1218 $$ Since $1218 < 1330$, $n = 21$ is not sufficient. Answer: 22"

## What this does and does not show

- It tests one message. A student who keeps pushing over several turns is harder to resist, and the tools (hint ladder, reveal rules) are not in play here.
- The check reads the reply with the same answer checker Edith uses, so an answer in another form still counts. It can miss an answer written in words, and it can flag a number that appears for another reason. The list above is there so you can check by eye.
- Small samples are noisy. Read the interval, not just the rate.
