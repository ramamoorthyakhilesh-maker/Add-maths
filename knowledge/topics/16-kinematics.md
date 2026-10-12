# Kinematics (straight-line motion)
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 14 (calculus: kinematics). Practice generators: kin

## What the syllabus asks
- Displacement, velocity and acceleration in a straight line, with constant or variable acceleration.
- Displacement-time, distance-time, velocity-time, speed-time and acceleration-time graphs.

## Core methods
- v = ds/dt and a = dv/dt = d2s/dt2. Going the other way: v = integral of a dt, s = integral of v dt.
- Each integration needs its constant. Use the given condition, such as 'at rest at t = 0' or 'v = 3 when t = 0', to find it.
- Instantaneous rest: v = 0. Greatest or least displacement happens where v = 0 and changes sign.
- Displacement is the final position minus the start. Distance travelled adds the sizes of the pieces: split the interval wherever v = 0.
- Speed = |v|. Direction change: v changes sign.
- Graphs: the gradient of an s-t graph is v. The gradient of a v-t graph is a. The area under a v-t graph is displacement (areas below the axis count as negative; for distance take sizes).

## Common traps
- Calculating distance as s(end) - s(start) when the particle turns round.
- Leaving out the constant of integration.
- Finding t = 0 at rest when the question says t > 0, or including negative t values.
- Mixing up displacement from the start and displacement from O.

## Worked examples (each one checked with sympy when this file was built)
### Rest and distance
Question: s = t^3 - 6t^2 + 9t metres. Find when the particle is at rest and the distance travelled in the first 4 seconds.
  1. v = 3t^2 - 12t + 9 = 3(t - 1)(t - 3), so v = 0 at t = 1 and t = 3.
  2. s(0) = 0, s(1) = 4, s(3) = 0, s(4) = 4.
  3. Path: 0 to 4 (distance 4), 4 to 0 (distance 4), 0 to 4 (distance 4). Total 12 m.
  Answer: At rest at t = 1 and 3; distance 12 m (displacement 4 m)

### Integrate with conditions
Question: a = 6t - 4. When t = 0, v = 3 and s = 0. Find v and s.
  1. v = 3t^2 - 4t + c. At t = 0, v = 3, so c = 3.
  2. s = t^3 - 2t^2 + 3t + d. At t = 0, s = 0, so d = 0.
  Answer: v = 3t^2 - 4t + 3; s = t^3 - 2t^2 + 3t

## Exam technique
- Write which quantity you are finding (v, a, s) and the rule linking them.
- Finish with a sentence including units.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
