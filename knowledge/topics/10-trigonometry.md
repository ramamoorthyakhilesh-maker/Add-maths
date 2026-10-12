# Trigonometry
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 10. Practice generators: trig, tgraph

## What the syllabus asks
- sin, cos, tan, sec, cosec, cot. Exact values for standard angles (30, 45, 60 degrees and the radian equivalents).
- Graphs of a sin(bx) + c, a cos(bx) + c, a tan(bx) + c: amplitude and period.
- The three Pythagorean identities. Solve trig equations in a given range. Prove identities.
- Degrees or radians as the question states.

## Core methods
- sec x = 1/cos x, cosec x = 1/sin x, cot x = 1/tan x. tan x = sin x / cos x.
- sin^2 x + cos^2 x = 1. 1 + tan^2 x = sec^2 x. 1 + cot^2 x = cosec^2 x. These three are in the formula list.
- Exact values: sin 30 = 1/2, cos 60 = 1/2, sin 45 = cos 45 = sqrt(2)/2, sin 60 = cos 30 = sqrt(3)/2, tan 30 = 1/sqrt(3), tan 45 = 1, tan 60 = sqrt(3).
- Graph of a sin(bx) + c: amplitude |a|, period 360/b degrees (2 pi / b radians), midline y = c. For tan the period is 180/b degrees.
- Solve: get one trig function equal to a number. Find the acute angle, then use the graph or the CAST diagram for all angles in the range. For sin (bx), widen the range for bx first, then divide.
- Quadratics in sin, cos or tan: use an identity to get one function, factorise, solve each. Reject values outside -1 to 1 for sin and cos.
- Do not divide by sin x or cos x when solving: move everything to one side and factorise, or you lose solutions.
- Prove an identity: work on one side only (usually the more complicated), change to sin and cos, and reach the other side.

## Common traps
- Dividing by sin x (loses solutions where sin x = 0).
- Forgetting solutions from the other quadrants.
- Not widening the range when the angle is 2x or 3x.
- Calculator mode mismatch (degrees vs radians).
- Writing sin^2 x as sin x^2.

## Worked examples (each one checked with sympy when this file was built)
### Identity into a quadratic
Question: Solve 2 sin^2 x + cos x - 1 = 0 for 0 <= x <= 360 degrees.
  1. Replace sin^2 x with 1 - cos^2 x: 2 - 2cos^2 x + cos x - 1 = 0.
  2. -2cos^2 x + cos x + 1 = 0, so 2cos^2 x - cos x - 1 = 0.
  3. (2cos x + 1)(cos x - 1) = 0. cos x = -1/2 gives 120 and 240. cos x = 1 gives 0 and 360.
  Answer: x = 0, 120, 240, 360

### Do not divide
Question: Solve tan x = 2 sin x for 0 <= x <= 360 degrees.
  1. sin x / cos x = 2 sin x, so sin x = 2 sin x cos x.
  2. sin x (1 - 2 cos x) = 0.
  3. sin x = 0 gives 0, 180, 360. cos x = 1/2 gives 60 and 300.
  Answer: x = 0, 60, 180, 300, 360

### Prove an identity
Question: Prove tan x + cot x = sec x cosec x.
  1. LHS = sin x / cos x + cos x / sin x.
  2. Common denominator: (sin^2 x + cos^2 x)/(sin x cos x).
  3. The top is 1, so LHS = 1/(sin x cos x) = sec x cosec x.
  Answer: Proved

### Radians
Question: Solve sin x = 1/2 for 0 <= x <= 2 pi.
  1. Acute angle: pi/6.
  2. sin is positive in the first and second quadrants: x = pi/6 and pi - pi/6.
  Answer: x = pi/6 and 5pi/6

## Exam technique
- Write 'hence' answers using the result just proved.
- In an identity proof, never treat it as an equation and do the same thing to both sides.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
