# Circular measure (radians)
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 9. Practice generators: circ, tgraph

## What the syllabus asks
- Convert between degrees and radians.
- Arc length s = r theta, sector area A = (1/2) r^2 theta, with theta in radians. Problems that combine sectors with triangles.

## Core methods
- pi radians = 180 degrees. Degrees to radians: multiply by pi/180. Radians to degrees: multiply by 180/pi.
- Arc length s = r theta. Sector area A = (1/2) r^2 theta. Perimeter of a sector = 2r + r theta.
- Triangle area = (1/2) a b sin C (given in the formula list). Segment area = sector area - triangle area = (1/2) r^2 (theta - sin theta).
- Chord length = 2 r sin (theta/2). Use right triangles by splitting the isosceles triangle.
- Keep angles in radians when you use a calculator for sin theta. Check the mode.

## Common traps
- Using the formulas with degrees.
- Calculator in the wrong mode.
- Forgetting the two radii in the perimeter of a sector.
- Using the segment formula with theta in degrees.

## Worked examples (each one checked with sympy when this file was built)
### Arc and area
Question: A sector has radius 8 cm and angle 0.7 radians. Find the arc length and the area.
  1. s = 8 x 0.7 = 5.6 cm.
  2. A = (1/2)(64)(0.7) = 22.4 cm^2.
  Answer: 5.6 cm and 22.4 cm^2

### Convert
Question: Write 150 degrees in radians and find the arc length for r = 6.
  1. 150 x pi/180 = 5pi/6.
  2. s = 6 x 5pi/6 = 5pi, about 15.7 cm.
  Answer: 5pi/6; arc 5pi cm

### Segment
Question: A sector has radius 10 cm and angle 1.2 radians. Find the area of the segment.
  1. Sector = (1/2)(100)(1.2) = 60.
  2. Triangle = (1/2)(100) sin 1.2 = 46.602.
  3. Segment = 60 - 46.602 = 13.398.
  Answer: 13.4 cm^2 (3 s.f.)

### Find the angle
Question: A sector of radius 5 has area 30. Find the angle and the arc length.
  1. 30 = (1/2)(25) theta, so theta = 2.4.
  2. s = 5 x 2.4 = 12.
  Answer: theta = 2.4 radians, arc 12

## Exam technique
- Write the formula first. Use exact pi when asked for exact answers.
- State the units of the answer.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
