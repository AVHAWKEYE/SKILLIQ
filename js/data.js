// ========== SKILLS CONFIG ==========
const SKILLS = [
  { id: 'math', name: 'Mathematics', icon: '🧮', desc: 'Arithmetic, algebra, geometry', badgeClass: 'skill-math', color: '#378ADD' },
  { id: 'logic', name: 'Logical Reasoning', icon: '🧠', desc: 'Patterns, deduction, syllogisms', badgeClass: 'skill-logic', color: '#7F77DD' },
  { id: 'aptitude', name: 'Aptitude', icon: '⚡', desc: 'Speed, quantitative, data interpretation', badgeClass: 'skill-aptitude', color: '#BA7517' },
  { id: 'problem', name: 'Problem Solving', icon: '🔧', desc: 'Strategy, critical thinking, puzzles', badgeClass: 'skill-problem', color: '#1D9E75' }
];

// ========== QUESTION BANK ==========
const QUESTIONS = {
  math: [
    { q: 'If 3x + 7 = 22, what is the value of x?', opts: ['3', '5', '6', '4'], ans: 1, diff: 'easy', exp: '3x = 22 - 7 = 15, so x = 15 ÷ 3 = 5.' },
    { q: 'What is 15% of 240?', opts: ['36', '30', '38', '32'], ans: 0, diff: 'easy', exp: '15% of 240 = 0.15 × 240 = 36.' },
    { q: 'A circle has radius 7. What is its area (π ≈ 3.14)?', opts: ['153.86', '44', '43.96', '154'], ans: 0, diff: 'med', exp: 'Area = π × r² = 3.14 × 49 = 153.86.' },
    { q: 'Find the slope of the line passing through (2, 3) and (6, 11).', opts: ['2', '3', '4', '1.5'], ans: 0, diff: 'med', exp: 'Slope = (11-3)/(6-2) = 8/4 = 2.' },
    { q: 'What is the value of log₁₀(1000)?', opts: ['10', '100', '3', '30'], ans: 2, diff: 'hard', exp: 'log₁₀(1000) = log₁₀(10³) = 3.' }
  ],
  logic: [
    { q: 'All cats are animals. All animals need food. Therefore:', opts: ['All animals are cats', 'All cats need food', 'Some food is animals', 'None of the above'], ans: 1, diff: 'easy', exp: 'This follows by the transitive property of syllogisms.' },
    { q: 'Complete the sequence: 2, 4, 8, 16, ___', opts: ['24', '32', '28', '30'], ans: 1, diff: 'easy', exp: 'Each term is doubled: 16 × 2 = 32.' },
    { q: 'If MANGO is coded as NBOIP, what is APPLE coded as?', opts: ['BQQMF', 'CRRNG', 'BRRNG', 'BQQNG'], ans: 0, diff: 'med', exp: 'Each letter is shifted +1: A→B, P→Q, P→Q, L→M, E→F = BQQMF.' },
    { q: 'There are 5 houses in a row. The green house is immediately to the left of the white house. Which positions can the green house be in?', opts: ['5', '1, 2, 3 or 4', '1', '2, 3 or 4'], ans: 3, diff: 'hard', exp: 'Green must have white to its right, so green can be in positions 1–4 (not 5).' },
    { q: 'If A > B and B > C, then which is true?', opts: ['C > A', 'A > C', 'B > A', 'C > B'], ans: 1, diff: 'easy', exp: 'By transitivity: A > B > C, therefore A > C.' }
  ],
  aptitude: [
    { q: 'A train travels 120 km in 2 hours. What is its speed in km/h?', opts: ['60', '50', '70', '80'], ans: 0, diff: 'easy', exp: 'Speed = Distance ÷ Time = 120 ÷ 2 = 60 km/h.' },
    { q: 'If a shopkeeper sells an item for ₹600 at 20% profit, what was the cost price?', opts: ['₹480', '₹500', '₹450', '₹520'], ans: 1, diff: 'med', exp: 'CP = SP ÷ (1 + profit%) = 600 ÷ 1.2 = ₹500.' },
    { q: 'Pipes A and B can fill a tank in 6 and 12 hours. How long do they take together?', opts: ['3 hrs', '4 hrs', '5 hrs', '4.5 hrs'], ans: 1, diff: 'med', exp: 'Combined rate = 1/6 + 1/12 = 3/12 = 1/4 → 4 hours.' },
    { q: "A man's salary increased by 10% then decreased by 10%. Net change?", opts: ['0%', '1% increase', '-1%', '2% decrease'], ans: 2, diff: 'hard', exp: '1.1 × 0.9 = 0.99, so net is −1% (a 1% decrease).' },
    { q: 'The average of 5 numbers is 20. If one number is removed, the average becomes 18. What number was removed?', opts: ['26', '28', '30', '32'], ans: 1, diff: 'med', exp: 'Sum = 100. New sum = 72. Removed = 100 - 72 = 28.' }
  ],
  problem: [
    { q: 'You have two buckets: 3L and 5L. How do you measure exactly 4 litres?', opts: ['Fill 5L, pour into 3L, empty 3L, pour remaining, fill 5L, pour into 3L', 'Just fill 5L twice', 'Fill 3L twice', 'Not possible'], ans: 0, diff: 'hard', exp: 'Fill 5L → pour into 3L (2L left in 5L) → empty 3L → pour 2L → fill 5L → pour 1L into 3L = 4L.' },
    { q: 'A fox, a chicken and grain must cross a river. You can only carry one at a time. What do you carry first?', opts: ['Grain', 'Fox', 'Chicken', 'Any order works'], ans: 2, diff: 'med', exp: 'The chicken must go first — the fox and grain are safe together, but fox eats chicken and chicken eats grain.' },
    { q: 'How many squares are in a 4×4 grid?', opts: ['16', '20', '30', '14'], ans: 2, diff: 'hard', exp: 'Count all sizes: 1×1=16, 2×2=9, 3×3=4, 4×4=1. Total = 30.' },
    { q: 'A clock shows 3:15. What is the angle between the hands?', opts: ['0°', '7.5°', '15°', '22.5°'], ans: 1, diff: 'med', exp: 'At 3:15, minute hand is at 90°. Hour hand is at 97.5°. Difference = 7.5°.' },
    { q: 'In a race, if you overtake the person in 2nd place, what place are you in?', opts: ['1st', '2nd', '3rd', 'Depends'], ans: 1, diff: 'easy', exp: 'You overtook the person in 2nd — so you take their place, which is 2nd.' }
  ]
};
