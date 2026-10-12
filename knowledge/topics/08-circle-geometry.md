# Coordinate geometry of the circle
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 8. Practice generators: cgeo, simul

## What the syllabus asks
- Equation of a circle with centre (a, b) and radius r (given in the formula list).
- Intersection of a line and a circle, and of two circles.
- Tangents and chords. Common chords.

## Core methods
- (x - a)^2 + (y - b)^2 = r^2 has centre (a, b) and radius r.
- Expanded form: x^2 + y^2 + 2gx + 2fy + c = 0. Centre (-g, -f), r^2 = g^2 + f^2 - c. Or complete the square on x and on y.
- Radius to a point of tangency is perpendicular to the tangent: tangent gradient = -1 / (radius gradient).
- Line and circle: substitute the line into the circle to get a quadratic in x. D > 0: two points. D = 0: tangent. D < 0: no intersection.
- Chord: the perpendicular from the centre to a chord bisects the chord. Use right triangles with the radius as the hypotenuse.
- Common chord of two circles: subtract one equation from the other. The result is the line through the two intersection points. Then intersect that line with either circle.
- Circle through three points or with a given diameter: the centre is the midpoint of a diameter. Find the radius as the distance from the centre to one of the points.

## Common traps
- Sign errors when reading the centre: (x + 2)^2 means a = -2.
- Forgetting to take the square root: the right side is r^2.
- Using the wrong gradient for the tangent (must use the negative reciprocal of the radius gradient).
- Leaving out the check that a point lies on the circle before finding its tangent.

## Worked examples (each one checked with sympy when this file was built)
### Centre and radius
Question: Find the centre and radius of x^2 + y^2 - 6x + 4y - 12 = 0.
  1. Group: (x^2 - 6x) + (y^2 + 4y) = 12.
  2. Complete the squares: (x - 3)^2 - 9 + (y + 2)^2 - 4 = 12.
  3. (x - 3)^2 + (y + 2)^2 = 25.
  Answer: Centre (3, -2), radius 5

### Tangent at a point
Question: Find the tangent to that circle at P(7, 1).
  1. Check P: (7 - 3)^2 + (1 + 2)^2 = 16 + 9 = 25. It is on the circle.
  2. Gradient of the radius from (3, -2) to (7, 1) is 3/4.
  3. Tangent gradient = -4/3.
  4. y - 1 = -4/3 (x - 7), so 3y + 4x = 31.
  Answer: 4x + 3y = 31

### Line meets circle
Question: The line y = x + 1 meets x^2 + y^2 = 25 at A and B. Find A, B and the length AB.
  1. x^2 + (x + 1)^2 = 25 gives 2x^2 + 2x - 24 = 0, so x^2 + x - 12 = 0.
  2. (x + 4)(x - 3) = 0. Points: (-4, -3) and (3, 4).
  3. Length = sqrt(7^2 + 7^2) = 7 sqrt(2).
  Answer: A(-4, -3), B(3, 4), AB = 7 sqrt(2)

### Common chord
Question: Find the common chord of x^2 + y^2 = 25 and (x - 6)^2 + y^2 = 25, and its length.
  1. Second equation: x^2 - 12x + 36 + y^2 = 25.
  2. Subtract the first from it: -12x + 36 = 0, so x = 3.
  3. Put x = 3 in the first: y^2 = 16, so y = +-4.
  4. The chord joins (3, 4) and (3, -4), so its length is 8.
  Answer: x = 3; length 8

## Exam technique
- Draw a quick sketch with the centre, the point and the radius marked.
- Say 'tangent, so D = 0' or 'tangent, so perpendicular to radius' to show the method.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
