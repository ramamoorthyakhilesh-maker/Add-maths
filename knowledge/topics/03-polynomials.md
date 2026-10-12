# Factors of polynomials
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 3. Practice generators: factor

## What the syllabus asks
- Remainder theorem and factor theorem.
- Finding factors of cubics and solving cubic equations.

## Core methods
- Remainder theorem: the remainder when f(x) is divided by (x - r) is f(r). For (ax - b) the remainder is f(b/a).
- Factor theorem: (x - r) is a factor exactly when f(r) = 0.
- To factorise a cubic: try r = +-1, +-2, +-3 (divisors of the constant term, over divisors of the leading coefficient) until f(r) = 0.
- Then divide (long division or inspection) to get a quadratic, and factorise that.
- Unknown constants: substitute the root or the remainder condition to make an equation, then solve. Two unknowns need two conditions.

## Common traps
- Using f(-r) instead of f(r): (x + 2) goes with x = -2.
- Stopping after one root. A cubic can have three.
- Dropping the leading coefficient when dividing, such as the 2 in 2x^3.
- Division errors from skipped zero terms: write 0x^2 when a power is missing.

## Worked examples (each one checked with sympy when this file was built)
### Factorise and solve a cubic
Question: Solve 2x^3 - 3x^2 - 11x + 6 = 0.
  1. Try x = 3: 54 - 27 - 33 + 6 = 0, so (x - 3) is a factor.
  2. Divide: 2x^3 - 3x^2 - 11x + 6 = (x - 3)(2x^2 + 3x - 2).
  3. Factorise the quadratic: 2x^2 + 3x - 2 = (2x - 1)(x + 2).
  4. Roots: x = 3, 1/2, -2.
  Answer: x = 3, 1/2, -2

### Remainder with an unknown
Question: x^3 + ax^2 - 2x + 4 leaves remainder 10 when divided by (x - 2). Find a.
  1. Remainder = f(2) = 8 + 4a - 4 + 4 = 8 + 4a.
  2. 8 + 4a = 10, so a = 1/2.
  Answer: a = 1/2

### Two conditions
Question: (x + 1) is a factor of x^3 + px^2 + qx - 6 and the remainder is 12 on division by (x - 2). Find p and q.
  1. f(-1) = 0: -1 + p - q - 6 = 0, so p - q = 7.
  2. f(2) = 12: 8 + 4p + 2q - 6 = 12, so 2p + q = 5.
  3. Add the equations: 3p = 12, p = 4. Then q = -3.
  Answer: p = 4, q = -3

## Exam technique
- Write 'f(r) = 0' explicitly before concluding that something is a factor.
- In 'hence' questions use the factor you just found.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
