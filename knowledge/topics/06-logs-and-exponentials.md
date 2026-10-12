# Logarithmic and exponential functions
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 6. Practice generators: log

## What the syllabus asks
- Graphs and asymptotes of y = e^x and y = ln x.
- Laws of logarithms and change of base.
- Solve a^x = b and equations involving logarithms.

## Core methods
- Laws (any valid base): log xy = log x + log y. log (x/y) = log x - log y. log x^n = n log x. log_a a = 1. log_a 1 = 0.
- Change of base: log_a b = log_c b / log_c a. In particular log_a b = 1/(log_b a).
- ln x is log base e. e^x and ln x are inverses: e^(ln x) = x and ln(e^x) = x.
- Solve a^x = b: take logs of both sides, x log a = log b, x = log b / log a.
- Equations with logs: combine into one log with the laws, write as a power (log_a N = c means N = a^c), solve, then CHECK that every log argument is positive.
- Equations like 2^(2x) - 6(2^x) + 8 = 0: let u = 2^x, solve the quadratic, then solve 2^x = u. A value u <= 0 gives no solution.
- Graphs: y = e^x goes through (0, 1), is always positive, and has the x-axis as an asymptote. y = ln x goes through (1, 0), exists only for x > 0, and has the y-axis as an asymptote. They are mirror images in y = x.

## Common traps
- Writing log(x + y) = log x + log y. There is no such law.
- Forgetting to reject solutions that put a negative number inside a log.
- Treating log x^2 as (log x)^2.
- Rounding too early. Keep full calculator values until the end.

## Worked examples (each one checked with sympy when this file was built)
### Exponential equation
Question: Solve 3^x = 20, giving the answer to 3 significant figures.
  1. Take logs: x ln 3 = ln 20.
  2. x = ln 20 / ln 3 = 2.727.
  3. To 3 significant figures: 2.73.
  Answer: x = 2.73

### Combine logs
Question: Solve log2 x + log2 (x - 2) = 3.
  1. log2 [x(x - 2)] = 3, so x(x - 2) = 2^3 = 8.
  2. x^2 - 2x - 8 = 0, so (x - 4)(x + 2) = 0.
  3. x = 4 or x = -2. For x = -2, log2 (-2) does not exist, so reject it.
  Answer: x = 4

### Quadratic in 2^x
Question: Solve 2^(2x) - 6(2^x) + 8 = 0.
  1. Let u = 2^x: u^2 - 6u + 8 = 0, so u = 2 or 4.
  2. 2^x = 2 gives x = 1. 2^x = 4 gives x = 2.
  Answer: x = 1 or x = 2

### Change of base
Question: Solve log2 x + 3 log_x 2 = 4.
  1. log_x 2 = 1/(log2 x). Let u = log2 x: u + 3/u = 4.
  2. u^2 - 4u + 3 = 0, so u = 1 or 3.
  3. x = 2^1 = 2 or x = 2^3 = 8.
  Answer: x = 2 or x = 8

## Exam technique
- Show the law you use. State the rejection of an invalid root in words.
- Give logs answers exactly when asked, as ln 5 / ln 3, not a decimal.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
