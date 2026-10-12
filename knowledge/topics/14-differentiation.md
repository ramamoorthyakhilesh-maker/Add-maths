# Differentiation
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 14 (calculus: differentiation). Practice generators: diff, stat, tangent, rates

## What the syllabus asks
- Notation f'(x), f''(x), dy/dx, d2y/dx2.
- Derivatives of x^n (any rational n), sin x, cos x, tan x, e^x, ln x; constant multiples and sums.
- Chain rule, product rule, quotient rule.
- Tangents and normals. Stationary points and their nature.
- Connected rates of change, small increments, practical maximum and minimum problems.

## Core methods
- x^n gives n x^(n - 1). sin x gives cos x. cos x gives -sin x. tan x gives sec^2 x. e^x gives e^x. ln x gives 1/x. For e^(ax) the derivative is a e^(ax).
- Rewrite roots and fractions as powers first: sqrt(x) = x^(1/2), 1/x^2 = x^-2.
- Chain rule: dy/dx = dy/du x du/dx. Product rule: d(uv) = u v' + v u'. Quotient rule: d(u/v) = (v u' - u v')/v^2.
- Tangent at x = x0: gradient m = dy/dx at x0, point (x0, y0), line y - y0 = m(x - x0). Normal gradient = -1/m.
- Stationary points: dy/dx = 0. Nature: d2y/dx2 > 0 minimum, < 0 maximum. If d2y/dx2 = 0, check the sign of dy/dx either side.
- Small change: delta y is approximately (dy/dx) delta x. Connected rates: dy/dt = dy/dx x dx/dt.
- Optimisation: write the quantity as a function of ONE variable using the constraint, differentiate, set to zero, prove it is a max or a min, answer the question that was asked.

## Common traps
- Forgetting the chain rule factor, such as d/dx sin(3x) = 3 cos 3x.
- Quotient rule order: v u' - u v', not u v' - v u'.
- Differentiating the constant: it becomes 0.
- Stopping at the x value of a stationary point when the question wants coordinates.
- Using the tangent gradient for the normal.

## Worked examples (each one checked with sympy when this file was built)
### Product rule
Question: Differentiate y = x^2 e^(3x).
  1. u = x^2, v = e^(3x). u' = 2x, v' = 3e^(3x).
  2. dy/dx = x^2 (3e^(3x)) + e^(3x)(2x) = e^(3x)(3x^2 + 2x).
  Answer: dy/dx = e^(3x)(3x^2 + 2x)

### Quotient rule
Question: Differentiate y = (2x + 1)/(x^2 + 1).
  1. u = 2x + 1, v = x^2 + 1. u' = 2, v' = 2x.
  2. dy/dx = [(x^2 + 1)(2) - (2x + 1)(2x)]/(x^2 + 1)^2.
  3. Numerator: 2x^2 + 2 - 4x^2 - 2x = -2x^2 - 2x + 2.
  Answer: dy/dx = (-2x^2 - 2x + 2)/(x^2 + 1)^2

### Stationary points
Question: Find and classify the stationary points of y = x^3 - 6x^2 + 9x + 1.
  1. dy/dx = 3x^2 - 12x + 9 = 3(x - 1)(x - 3) = 0, so x = 1 or 3.
  2. y(1) = 5 and y(3) = 1.
  3. d2y/dx2 = 6x - 12. At x = 1 it is -6 (maximum). At x = 3 it is +6 (minimum).
  Answer: (1, 5) maximum; (3, 1) minimum

### Tangent and normal
Question: Find the tangent and normal to y = ln(3x - 2) at x = 1.
  1. dy/dx = 3/(3x - 2) = 3 at x = 1. y = ln 1 = 0.
  2. Tangent: y - 0 = 3(x - 1), so y = 3x - 3.
  3. Normal gradient -1/3: y = -(x - 1)/3.
  Answer: tangent y = 3x - 3; normal y = -(x - 1)/3

## Exam technique
- Name the rule you use in a few words. Show u, v, u', v' for product and quotient questions.
- For 'show that' stationary point questions, show both the derivative equal to zero and the value.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
