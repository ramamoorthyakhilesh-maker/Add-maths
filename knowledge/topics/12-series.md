# Series: binomial, arithmetic and geometric progressions
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 12. Practice generators: binom, prog

## What the syllabus asks
- Binomial expansion of (a + b)^n for positive integer n; general term; the term independent of x.
- Arithmetic and geometric progressions: nth term and sum.
- Sum to infinity of a GP and the condition for convergence.
- Contextual problems.

## Core methods
- Binomial: (a + b)^n = sum over r of nCr a^(n - r) b^r. General term (r + 1th) = nCr a^(n - r) b^r. Pascal's triangle gives nCr for small n.
- Coefficient of x^m: write the general term with all powers of x, set the power equal to m, solve for r.
- Brackets like (1 + 2x)^5: keep the constants and signs inside the power.
- AP: u_n = a + (n - 1)d. S_n = (n/2)[2a + (n - 1)d] = (n/2)(a + l). GP: u_n = a r^(n - 1). S_n = a(1 - r^n)/(1 - r) = a(r^n - 1)/(r - 1). S_infinity = a/(1 - r) only if |r| < 1.
- Two given terms: write two equations in a and d (or a and r). Subtract for d. Divide for r.
- Least n such that a sum exceeds K: write the inequality, solve with algebra (quadratic) or logs (GP), then round UP to a whole n and check n and n - 1.
- Dividing inequalities by log of a number less than 1 reverses the inequality sign.

## Common traps
- Writing the (r)th term when you mean the (r + 1)th term.
- Using S_infinity when |r| >= 1.
- Forgetting the sign when b is negative: (2 - 3x)^4 has alternating signs.
- Rounding n down.

## Worked examples (each one checked with sympy when this file was built)
### Coefficient
Question: Find the coefficient of x^3 in (2 + 3x)^5.
  1. General term = 5Cr 2^(5 - r) (3x)^r. For x^3, r = 3.
  2. 5C3 x 2^2 x 3^3 = 10 x 4 x 27 = 1080.
  Answer: 1080

### Term independent of x
Question: Find the term independent of x in (x^2 + 2/x)^6.
  1. General term = 6Cr (x^2)^(6 - r) (2/x)^r = 6Cr 2^r x^(12 - 3r).
  2. Power 0: 12 - 3r = 0, r = 4.
  3. 6C4 x 2^4 = 15 x 16 = 240.
  Answer: 240

### AP from two terms
Question: In an AP the 3rd term is 14 and the 8th is 34. Find a, d and S_10.
  1. a + 2d = 14 and a + 7d = 34. Subtract: 5d = 20, d = 4, a = 6.
  2. S_10 = (10/2)(2 x 6 + 9 x 4) = 5 x 48 = 240.
  Answer: a = 6, d = 4, S_10 = 240

### Sum to infinity
Question: A GP has first term 3 and ratio 2/3. Find S_infinity.
  1. |r| = 2/3 < 1, so it converges.
  2. S_infinity = 3/(1 - 2/3) = 9.
  Answer: 9

### Least n
Question: The GP 5, 10, 20, ... has sum S_n = 5(2^n - 1). Find the least n for which S_n > 10000.
  1. 2^n - 1 > 2000, so 2^n > 2001.
  2. n > ln 2001 / ln 2 = 10.97, so n = 11.
  3. Check: S_11 = 5 x 2047 = 10235 > 10000 and S_10 = 5115 < 10000.
  Answer: n = 11

## Exam technique
- For 'show that' sum questions, quote the formula, substitute, and simplify to the target.
- Write the condition |r| < 1 before using S_infinity.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
