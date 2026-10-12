# Equations, inequalities and graphs (modulus, substitution, cubics)
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 4. Practice generators: mod, ineq

## What the syllabus asks
- Solve |ax + b| = c, |ax + b| = cx + d, |ax + b| = |cx + d|, |ax^2 + bx + c| = d.
- Solve modulus inequalities such as k|ax + b| > c, |ax + b| <= cx + d, |ax^2 + bx + c| > d.
- Solve equations that become quadratics after a substitution.
- Sketch a cubic given as a product of three linear factors, and its modulus. Solve cubic inequalities with a graph.

## Core methods
- |a| is the distance from zero. |a| = c (c > 0) means a = c or a = -c.
- |a| = b + (something): solve the two cases a = rhs and a = -rhs, then CHECK each answer. The right side must not be negative.
- |f| = |g|: either f = g or f = -g. Squaring both sides also works.
- |x - a| < b means a - b < x < a + b. |x - a| > b means x < a - b or x > a + b.
- For harder modulus inequalities: find the critical values (where the two sides are equal), then test a value in each region. A sketch of both sides helps.
- Substitution: x^4 - 10x^2 + 9 = 0 with u = x^2 gives u^2 - 10u + 9 = 0. Solve for u, then for x. Reject impossible values, such as x^2 = -4.
- Cubic inequality: mark the roots on the axis, sketch the curve using the sign of the leading coefficient, and read off where it is above or below the axis.

## Common traps
- Not checking answers in |ax + b| = cx + d. One of the two cases is often false.
- Writing x > a or x < b as one chain: a combined chain such as 5 < x < 2 is impossible.
- Squaring an inequality without care. Squaring |A| < |B| is fine since both sides are non-negative.
- Forgetting the negative square root after substitution.
- In a sketch of |f(x)|, leaving parts below the axis.

## Worked examples (each one checked with sympy when this file was built)
### Modulus with x on both sides
Question: Solve |2x - 3| = x + 1.
  1. Case 1: 2x - 3 = x + 1, so x = 4.
  2. Case 2: 2x - 3 = -(x + 1), so 3x = 2 and x = 2/3.
  3. Check: x + 1 is positive for both, so both are valid. (At x = 4: |5| = 5. At x = 2/3: |-5/3| = 5/3.)
  Answer: x = 4 or x = 2/3

### Modulus of a quadratic
Question: Solve |x^2 - 5x| = 6.
  1. x^2 - 5x = 6 gives (x - 6)(x + 1) = 0, so x = 6 or -1.
  2. x^2 - 5x = -6 gives (x - 2)(x - 3) = 0, so x = 2 or 3.
  3. All four satisfy the original equation.
  Answer: x = -1, 2, 3, 6

### Modulus inequality
Question: Solve |x - 2| > 3.
  1. Either x - 2 > 3 or x - 2 < -3.
  2. So x > 5 or x < -1.
  Answer: x < -1 or x > 5

### Substitution
Question: Solve x^4 - 10x^2 + 9 = 0.
  1. Let u = x^2: u^2 - 10u + 9 = 0, so (u - 1)(u - 9) = 0.
  2. u = 1 gives x = +-1. u = 9 gives x = +-3.
  Answer: x = -3, -1, 1, 3

### Cubic inequality
Question: Solve (x + 2)(x - 1)(x - 3) < 0.
  1. Roots at -2, 1, 3. The leading coefficient is positive, so the curve goes up on the far right.
  2. From the right: positive beyond 3, negative between 1 and 3, positive between -2 and 1, negative below -2.
  3. Negative regions: x < -2 and 1 < x < 3.
  Answer: x < -2 or 1 < x < 3

## Exam technique
- Always show the case split in modulus work. Method marks are given for it.
- Finish with a statement about which values are valid.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
