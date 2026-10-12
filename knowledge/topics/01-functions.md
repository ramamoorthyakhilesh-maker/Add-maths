# Functions
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 1. Practice generators: func

## What the syllabus asks
- Function notation, domain and range. One-one and many-one functions.
- Composite functions fg(x) and inverse functions f^-1(x).
- The graph of an inverse is the reflection of the graph in y = x.
- The graph of y = |f(x)| and how it relates to y = f(x), for linear, quadratic, cubic and trig f.

## Core methods
- A function gives exactly one output for each input. Domain = allowed inputs, range = outputs that actually happen.
- fg(x) means f(g(x)): apply g first, then f. Replace every x in f by the whole of g.
- Inverse: write y = f(x), make x the subject, then swap the letters. The domain of f^-1 is the range of f. The range of f^-1 is the domain of f.
- Only one-one functions have an inverse. If f is many-one, restrict the domain (for example x >= 2) so that it becomes one-one.
- To find the range of a quadratic, complete the square and use the minimum or maximum, but only inside the stated domain.
- Sketch y = |f(x)|: sketch y = f(x), then reflect every part below the x-axis in the x-axis. The result never goes below the axis.
- f f^-1(x) = x and f^-1 f(x) = x. A point (a, b) on f means (b, a) is on f^-1.

## Common traps
- f^-1(x) is NOT 1/f(x). The -1 marks the inverse function.
- fg and gf are usually different. Check the order of application.
- Forgetting to state the domain or range when the question asks for it.
- Giving the range of a quadratic over all real x when the domain is restricted.
- In |f(x)|, reflecting the wrong part, or forgetting that turning points below the axis become peaks above it.

## Worked examples (each one checked with sympy when this file was built)
### Composite functions
Question: f(x) = 2x + 3 and g(x) = x^2 - 1. Find fg(x) and gf(x).
  1. fg(x) = f(g(x)) = 2(x^2 - 1) + 3.
  2. This simplifies to 2x^2 + 1.
  3. gf(x) = g(f(x)) = (2x + 3)^2 - 1.
  4. Expanding gives 4x^2 + 12x + 8.
  Answer: fg(x) = 2x^2 + 1, gf(x) = 4x^2 + 12x + 8

### Inverse of a fraction
Question: f(x) = (3x + 1)/(x - 2), x not equal to 2. Find f^-1(x) and state its domain.
  1. y = (3x + 1)/(x - 2), so y(x - 2) = 3x + 1.
  2. xy - 2y = 3x + 1, so xy - 3x = 2y + 1.
  3. x(y - 3) = 2y + 1, so x = (2y + 1)/(y - 3).
  4. Swap letters: f^-1(x) = (2x + 1)/(x - 3).
  5. f never takes the value 3 (y = 3 would need 0 = 7), so the range of f is y not equal to 3. That is the domain of f^-1.
  Answer: f^-1(x) = (2x + 1)/(x - 3), x not equal to 3

### Range on a restricted domain
Question: f(x) = x^2 - 4x + 1 for x >= 2. Find the range.
  1. Complete the square: x^2 - 4x + 1 = (x - 2)^2 - 3.
  2. The minimum is -3 at x = 2, which is in the domain.
  3. For x >= 2 the function only increases.
  Answer: f(x) >= -3

## Exam technique
- Write the order of application before you start (g first, then f).
- For 'find the inverse', end with f^-1(x) = ... in terms of x.
- State domain and range using inequalities or set words, as the question asks.

## Teaching order
1. Start with a mapping diagram idea: input, rule, output.
2. Teach composite (concrete numbers first, then algebra).
3. Teach inverse as undoing steps in reverse order, then the algebra method.
4. Do domain and range with a sketch, and |f(x)| last.
