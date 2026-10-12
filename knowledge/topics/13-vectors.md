# Vectors in two dimensions
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 13. Practice generators: vec

## What the syllabus asks
- Notation: column vectors, i and j form, AB, single letters. Position vectors, unit vectors, magnitude. Add, subtract, scalar multiples.
- Vector geometry; equate like vectors. Velocity vectors; motion of particles, collisions.

## Core methods
- Magnitude |ai + bj| = sqrt(a^2 + b^2). Unit vector = vector / magnitude.
- AB = OB - OA = b - a (end minus start).
- Parallel vectors are scalar multiples: if p = lambda q then p is parallel to q. Collinear points A, B, C: AB = lambda BC.
- Point P on AB with AP:PB = m:n has OP = OA + m/(m + n) AB.
- Equating vectors: if a i + b j = c i + d j then a = c and b = d. Use this to get two equations.
- Moving particle: position r = r0 + v t (initial position r0, constant velocity v). Speed = |v|.
- Collision: two particles are at the same place at the same time. Equate the i components and the j components, solve for t, and CHECK it works in both.
- Distance between two moving particles at time t: find both position vectors at that time, subtract to get PQ, then take the magnitude.

## Common traps
- AB = a - b (the wrong way round).
- Forgetting to square-root a magnitude.
- Solving the i equation only: a collision needs both components to give the same t.
- Mixing speed (a number) and velocity (a vector).

## Worked examples (each one checked with sympy when this file was built)
### Basic vectors
Question: a = 3i + 4j and b = i - 2j. Find |a|, a unit vector along a, and AB.
  1. |a| = sqrt(9 + 16) = 5.
  2. Unit vector = (3i + 4j)/5.
  3. AB = b - a = (1 - 3)i + (-2 - 4)j = -2i - 6j. |AB| = sqrt(40) = 2 sqrt(10).
  Answer: 5; (3i + 4j)/5; -2i - 6j

### Point dividing a line
Question: A(1, 2), B(7, 5). P is on AB with AP:PB = 2:1. Find OP.
  1. AB = (6, 3).
  2. AP = 2/3 of AB = (4, 2).
  3. OP = OA + AP = (1 + 4, 2 + 2) = (5, 4).
  Answer: OP = 5i + 4j

### Collision
Question: P starts at (2i + j) with velocity (3i - j). Q starts at (17i - 8j) with velocity (-2i + 2j). Do they collide?
  1. P at time t: (2 + 3t)i + (1 - t)j. Q at time t: (17 - 2t)i + (-8 + 2t)j.
  2. i components equal: 2 + 3t = 17 - 2t, so t = 3.
  3. j components equal: 1 - t = -8 + 2t, so t = 3. Same value, so they collide.
  4. Position: (2 + 9)i + (1 - 3)j = 11i - 2j.
  Answer: Yes, at t = 3, at 11i - 2j

## Exam technique
- Draw a sketch with arrows. Use the capital-letter notation (AB) consistently.
- Do not mix notations in one line.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
