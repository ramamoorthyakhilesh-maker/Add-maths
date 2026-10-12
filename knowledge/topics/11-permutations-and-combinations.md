# Permutations and combinations
Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.
Syllabus topic: 11. Practice generators: perm

## What the syllabus asks
- n!, nPr and nCr.
- Arrangement and selection problems, with and without restrictions.

## Core methods
- Order matters: arrangement (permutation). nPr = n!/(n - r)!. Order does not matter: selection (combination). nCr = n!/(r!(n - r)!). nCr = nC(n - r).
- n people in a row: n! arrangements. r from n in order: nPr. A team of r from n: nCr.
- Two people together: treat them as one block, arrange the block with the others, then multiply by 2 for the order inside the block.
- Two people NOT together: total arrangements - arrangements together.
- 'At least' problems: add the cases, or take the complement (total - the cases that are not allowed).
- Digits with conditions: fill the restricted position first (for an even number, choose the last digit first).

## Common traps
- Using nCr when order matters, or the reverse. Ask: would swapping two items give a different outcome?
- Counting cases twice.
- Forgetting that digits cannot start with 0 in a number.
- Forgetting to multiply the independent choices.

## Worked examples (each one checked with sympy when this file was built)
### Selection
Question: Choose 5 books from 8.
  1. Order does not matter: 8C5 = 8!/(5! 3!) = 56.
  Answer: 56

### Even numbers
Question: How many four-digit numbers can be made from the digits 1 to 7, with no repeats, that are even?
  1. Last digit even: 2, 4 or 6, so 3 choices.
  2. The other three places from the remaining 6 digits in order: 6 x 5 x 4 = 120.
  3. Total = 3 x 120 = 360.
  Answer: 360

### At least two women
Question: A committee of 4 is chosen from 6 men and 4 women. It must have at least 2 women. How many committees?
  1. Total with no restriction: 10C4 = 210.
  2. No women: 6C4 = 15. Exactly one woman: 4 x 6C3 = 80.
  3. 210 - 15 - 80 = 115. Check by cases: 2 women 6C2 x 4C2 = 90, 3 women 4C3 x 6 = 24, 4 women 1. 90 + 24 + 1 = 115.
  Answer: 115

### Together and apart
Question: Six people stand in a row. Two particular people must (a) be together, (b) not be together.
  1. (a) Block: 5! x 2 = 240.
  2. (b) Total 6! = 720, so 720 - 240 = 480.
  Answer: (a) 240 (b) 480

## Exam technique
- Say in a phrase whether it is a permutation or a combination, and why.
- Show the calculation in factorials or nPr/nCr form before the number.

## Teaching order
1. Ask a diagnostic question or ask what the student already knows.
2. Teach the idea with a worked example on a different question (use one above, change the numbers).
3. Hint ladder on a generator question: nudge, method name, partial step, worked similar example.
4. After a correct answer give three follow-ups (easy, medium, exam-level) from the generator.
