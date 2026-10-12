# Quadratic functions
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 2. Practice generators: quad, ineq

## What the syllabus asks
- Maximum and minimum values by completing the square, and using them for sketches and for range.
- The discriminant and the nature of the roots.
- Intersection of a line and a curve, and the tangent condition.
- Solving quadratic equations and quadratic inequalities.

## Core methods
- Complete the square: a x^2 + b x + c = a(x + p)^2 + q. The turning point is (-p, q). It is a minimum if a > 0 and a maximum if a < 0.
- Discriminant D = b^2 - 4ac. D > 0: two different real roots. D = 0: equal roots (the curve touches the x-axis). D < 0: no real roots.
- Line and curve: put y from the line into the curve to get a quadratic in x. D > 0: they cross twice. D = 0: the line is a tangent. D < 0: they miss.
- Quadratic inequality: factorise, sketch, mark roots, shade the part above or below the axis. Write the answer with x.
- 'Positive for all x' needs a > 0 and D < 0. 'Negative for all x' needs a < 0 and D < 0.

## Common traps
- Sign slips when the coefficient of x^2 is not 1: take it out of the first two terms first.
- Writing D = 0 when the question says 'two distinct roots' (that needs D > 0).
- Giving a single bracket answer for an inequality such as x^2 > 9: the answer is x < -3 or x > 3.
- Dividing by a variable that could be negative or zero.

## Worked examples (each one checked with sympy when this file was built)
### Completing the square
Question: Find the minimum value of 2x^2 - 12x + 7 and where it happens.
  1. Take 2 out of the x terms: 2(x^2 - 6x) + 7.
  2. Complete the square: 2[(x - 3)^2 - 9] + 7 = 2(x - 3)^2 - 11.
  3. The square is never negative, so the minimum is -11 when x = 3.
  Answer: Minimum value -11 at x = 3

### Tangent condition
Question: The line y = x + k is a tangent to y = x^2 - 3x + 5. Find k.
  1. Set equal: x^2 - 3x + 5 = x + k, so x^2 - 4x + (5 - k) = 0.
  2. Tangent means D = 0: 16 - 4(5 - k) = 0.
  3. 16 - 20 + 4k = 0, so k = 1.
  Answer: k = 1

### Positive for all x
Question: Find the values of k for which kx^2 + 4x + k > 0 for all real x.
  1. Need k > 0 (curve opens up) and D < 0.
  2. D = 16 - 4k^2 < 0 gives k^2 > 4, so k > 2 or k < -2.
  3. Combine with k > 0.
  Answer: k > 2

## Exam technique
- Show the discriminant line clearly: it earns a mark even if the arithmetic goes wrong later.
- For 'show that' questions, state the conclusion in words about the roots.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
