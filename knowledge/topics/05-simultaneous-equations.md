# Simultaneous equations
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 5. Practice generators: simul

## What the syllabus asks
- Solve two equations in two unknowns where one is linear and one is non-linear (including circles and curves).

## Core methods
- Rearrange the LINEAR equation to make one variable the subject (choose the one with no fraction).
- Substitute into the non-linear equation. Expand carefully, collect to the form ax^2 + bx + c = 0, and solve.
- Put each answer back into the LINEAR equation to find the other variable. This avoids false pairs.
- Present as pairs: (x1, y1) and (x2, y2).
- Discriminant of the quadratic tells how many intersection points: two, one (tangent) or none.

## Common traps
- Pairing x values with the wrong y values.
- Substituting into the non-linear equation to find the second variable: it can give extra false pairs.
- Expanding (a - b)^2 incorrectly.
- Stopping after finding only the x values.

## Worked examples (each one checked with sympy when this file was built)
### Line and a product
Question: Solve 2x + y = 5 and x^2 + xy = 6.
  1. y = 5 - 2x.
  2. x^2 + x(5 - 2x) = 6 gives -x^2 + 5x - 6 = 0, so x^2 - 5x + 6 = 0.
  3. x = 2 or 3. Then y = 5 - 2x gives y = 1 and y = -1.
  Answer: (2, 1) and (3, -1)

### Line and a circle
Question: Solve x - y = 2 and x^2 + y^2 = 10.
  1. x = y + 2.
  2. (y + 2)^2 + y^2 = 10 gives 2y^2 + 4y - 6 = 0, so y^2 + 2y - 3 = 0.
  3. (y + 3)(y - 1) = 0, so y = -3 or 1. Then x = y + 2 gives x = -1 or 3.
  Answer: (-1, -3) and (3, 1)

## Exam technique
- Write the substitution line clearly. Check at least one pair in both original equations.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
