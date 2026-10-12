# Straight-line graphs and the linear law
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 7. Practice generators: line, lin

## What the syllabus asks
- Equation of a line, parallel and perpendicular lines, midpoint, length of a segment, perpendicular bisector.
- Linear law: convert y = A x^n and y = A b^x to straight-line form, find the constants from the gradient and intercept. Also read relations such as y^2 against x^3.

## Core methods
- Gradient m = (y2 - y1)/(x2 - x1). Line: y - y1 = m(x - x1), or y = mx + c.
- Parallel lines: same gradient. Perpendicular: m1 m2 = -1 (negative reciprocal).
- Midpoint = ((x1 + x2)/2, (y1 + y2)/2). Length = sqrt((x2 - x1)^2 + (y2 - y1)^2).
- Perpendicular bisector of AB: passes through the midpoint of AB and has gradient equal to the negative reciprocal of the gradient of AB.
- Linear law method: write the relation in the form Y = mX + c where Y and X are the quantities plotted. The gradient is m and the vertical intercept is c.
- y = A x^n: take lg: lg y = n lg x + lg A. Plot lg y against lg x. Gradient n, intercept lg A.
- y = A b^x: lg y = x lg b + lg A. Plot lg y against x. Gradient lg b, intercept lg A.
- y = a x^2 + b: plot y against x^2. y = ax + b/x: multiply by x to get xy = a x^2 + b, plot xy against x^2.
- To find A from lg A = c, calculate A = 10^c (for lg) or e^c (for ln).

## Common traps
- Using the same gradient for a perpendicular line.
- Mixing up which axis is which: always say 'Y = ... against X = ...' first.
- Reading A as the intercept: the intercept is lg A, not A.
- Using the points on the graph in the wrong order for the gradient.

## Worked examples (each one checked with sympy when this file was built)
### Perpendicular bisector
Question: A is (1, 2) and B is (5, 10). Find the equation of the perpendicular bisector of AB.
  1. Gradient of AB = (10 - 2)/(5 - 1) = 2.
  2. Midpoint = (3, 6).
  3. Perpendicular gradient = -1/2.
  4. y - 6 = -1/2 (x - 3), so y = -x/2 + 15/2.
  Answer: y = -x/2 + 15/2, which is x + 2y = 15

### Linear law with y = A b^x
Question: A graph of lg y against x is a straight line through (0, 0.699) and (4, 1.903). Find A and b in y = A b^x.
  1. lg y = x lg b + lg A, so the gradient is lg b and the intercept is lg A.
  2. Gradient = (1.903 - 0.699)/4 = 0.301, so b = 10^0.301 = 2.00.
  3. Intercept 0.699 = lg A, so A = 10^0.699 = 5.00.
  Answer: A = 5.00 and b = 2.00 (to 3 s.f.), so y = 5(2^x)

## Exam technique
- Name the plotted variables first. Then show the line equation, then the gradient and intercept. Every step carries a mark.
- If the question gives a table, check the points lie on a straight line before you start.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
