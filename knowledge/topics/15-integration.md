# Integration
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 14 (calculus: integration). Practice generators: integ, area

## What the syllabus asks
- Integration as the reverse of differentiation, with a constant of integration.
- Powers of x including 1/x, (ax + b)^n for any rational n (including n = -1), sin(ax + b), cos(ax + b), sec^2(ax + b), e^(ax + b).
- Definite integrals. Area under a curve, between a curve and a line, between two curves, and sums of areas.

## Core methods
- x^n gives x^(n + 1)/(n + 1) for n not equal to -1. 1/x gives ln|x|. e^x gives e^x.
- Linear inside: divide by the coefficient of x. (ax + b)^n gives (ax + b)^(n + 1)/(a(n + 1)). 1/(ax + b) gives (1/a) ln|ax + b|. e^(ax + b) gives e^(ax + b)/a. sin(ax + b) gives -cos(ax + b)/a. cos(ax + b) gives sin(ax + b)/a. sec^2(ax + b) gives tan(ax + b)/a.
- Always add + c to an indefinite integral. For a definite integral no constant is needed.
- Find c with a given point: substitute the point into the integrated function.
- Area under y = f(x) from x = a to x = b is the integral of f if f >= 0 on the interval. Where the curve is below the axis the integral is negative: take the size.
- Area between curves: integral of (top - bottom). Find the intersections first.
- Several regions: split at the x-intercepts, integrate each, take the positive size of each, add.

## Common traps
- Forgetting + c or the division by the coefficient of x.
- Using x^(n + 1)/(n + 1) for 1/x.
- Writing a negative area as the answer.
- Using the wrong limits order: upper limit minus lower limit.
- Integrating the product of two functions term by term. It is not allowed.

## Worked examples (each one checked with sympy when this file was built)
### Mixed integral
Question: Find the integral of 3x^2 - 4/x^2 + 2e^(2x).
  1. Rewrite 4/x^2 as 4x^-2.
  2. Integrate each: x^3, +4/x (since the integral of -4x^-2 is 4x^-1), and e^(2x).
  3. Add the constant.
  Answer: x^3 + 4/x + e^(2x) + c

### Reverse chain rule
Question: Find the integral of (2x - 1)^4, then of 1/(3x + 1), then of sec^2(2x).
  1. (2x - 1)^5 / (5 x 2) = (2x - 1)^5 / 10 + c.
  2. (1/3) ln|3x + 1| + c.
  3. (1/2) tan 2x + c.
  Answer: (2x - 1)^5/10 + c; (1/3) ln|3x + 1| + c; (1/2) tan 2x + c

### Area between a line and a curve
Question: Find the area between y = x^2 and y = 2x.
  1. Intersections: x^2 = 2x gives x = 0, 2.
  2. Between them the line is above the curve.
  3. Area = integral from 0 to 2 of (2x - x^2) dx = [x^2 - x^3/3] = 4 - 8/3 = 4/3.
  Answer: 4/3

### Exact trig integral
Question: Evaluate the integral of cos 2x from 0 to pi/6.
  1. Integral = (1/2) sin 2x.
  2. At pi/6: (1/2) sin(pi/3) = sqrt(3)/4. At 0: 0.
  Answer: sqrt(3)/4

## Exam technique
- Show the integrated function in brackets or square brackets, then the limits.
- Leave exact values (pi, e, ln, surds) when the question says exact.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
