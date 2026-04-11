// ========== SKILLS CONFIG ==========
const SKILLS = [
  { id: 'math', name: 'DSA Foundations', icon: '🧩', desc: 'Arrays, complexity, recursion, trees', badgeClass: 'skill-math', color: '#378ADD' },
  { id: 'logic', name: 'Algorithmic Reasoning', icon: '🧠', desc: 'Tracing, optimization, edge cases', badgeClass: 'skill-logic', color: '#7F77DD' },
  { id: 'aptitude', name: 'CS Fundamentals', icon: '💾', desc: 'DBMS, OS, networks, OOP basics', badgeClass: 'skill-aptitude', color: '#BA7517' },
  { id: 'problem', name: 'Debugging & Engineering', icon: '🛠️', desc: 'Testing, debugging, practical coding', badgeClass: 'skill-problem', color: '#1D9E75' }
];

// ========== QUESTION BANK ==========
const QUESTIONS = {
  math: [
    { q: 'What is the time complexity of binary search on a sorted array?', opts: ['O(n)', 'O(log n)', 'O(n log n)', 'O(1)'], ans: 1, diff: 'easy', exp: 'Binary search halves the search space each step, so complexity is O(log n).' },
    { q: 'Which data structure is best for implementing LRU cache lookup/update in O(1)?', opts: ['Array + stack', 'HashMap + Doubly Linked List', 'Queue only', 'Binary Search Tree'], ans: 1, diff: 'med', exp: 'HashMap gives O(1) access and doubly linked list supports O(1) move/remove.' },
    { q: 'Which traversal gives sorted order for a Binary Search Tree?', opts: ['Preorder', 'Inorder', 'Postorder', 'Level order'], ans: 1, diff: 'easy', exp: 'Inorder traversal of BST visits keys in non-decreasing order.' },
    { q: 'What is the worst-case complexity of quicksort?', opts: ['O(n)', 'O(n log n)', 'O(log n)', 'O(n^2)'], ans: 3, diff: 'med', exp: 'Worst case occurs with highly unbalanced partitions, giving O(n^2).' },
    { q: 'For recursion to work correctly, which is mandatory?', opts: ['A loop', 'A base case', 'A hash map', 'A queue'], ans: 1, diff: 'hard', exp: 'Without a base case, recursion does not terminate.' }
  ],
  logic: [
    { q: 'If an algorithm has two nested loops over n elements each, typical complexity is:', opts: ['O(log n)', 'O(n)', 'O(n^2)', 'O(2^n)'], ans: 2, diff: 'easy', exp: 'Two full loops over n usually result in O(n^2) operations.' },
    { q: 'Which strategy guarantees optimal solution for weighted shortest path with non-negative edges?', opts: ['DFS', 'BFS', 'Dijkstra', 'Union-Find'], ans: 2, diff: 'med', exp: 'Dijkstra is correct for non-negative edge weights.' },
    { q: 'What is the primary purpose of dynamic programming?', opts: ['Randomization', 'Store overlapping subproblem results', 'Avoid recursion always', 'Reduce input size'], ans: 1, diff: 'easy', exp: 'DP caches repeated subproblem results to avoid recomputation.' },
    { q: 'You have sorted logs and need first occurrence of value. Best approach?', opts: ['Linear scan', 'Binary search variant', 'Hash all values', 'Stack simulation'], ans: 1, diff: 'med', exp: 'A modified binary search can find first occurrence in O(log n).' },
    { q: 'Which scenario indicates a greedy algorithm may fail?', opts: ['Optimal substructure exists', 'Local choice blocks future optimum', 'Data is sorted', 'Graph is connected'], ans: 1, diff: 'hard', exp: 'Greedy fails when local optimum does not lead to global optimum.' }
  ],
  aptitude: [
    { q: 'Which SQL command is used to remove all rows but keep table structure?', opts: ['DROP TABLE', 'DELETE TABLE', 'TRUNCATE TABLE', 'REMOVE'], ans: 2, diff: 'easy', exp: 'TRUNCATE removes rows while preserving schema.' },
    { q: 'What does ACID property ensure in DBMS?', opts: ['Only speed', 'Reliable transactions', 'Data compression', 'Network security'], ans: 1, diff: 'easy', exp: 'ACID ensures transaction correctness and reliability.' },
    { q: 'Which OS concept allows multiple processes to share CPU effectively?', opts: ['Caching', 'Scheduling', 'Indexing', 'Virtualization only'], ans: 1, diff: 'med', exp: 'CPU scheduling decides process execution order and fairness.' },
    { q: 'Which layer handles routing in the OSI model?', opts: ['Transport', 'Session', 'Network', 'Data Link'], ans: 2, diff: 'med', exp: 'Routing is handled by the Network layer (Layer 3).' },
    { q: 'What does encapsulation mean in OOP?', opts: ['Multiple inheritance', 'Binding data and methods with controlled access', 'Only function overloading', 'Runtime polymorphism'], ans: 1, diff: 'hard', exp: 'Encapsulation combines data and behavior while restricting direct access.' }
  ],
  problem: [
    { q: 'A bug appears only in production. What is the best first step?', opts: ['Rewrite module', 'Add targeted logs and reproduce issue', 'Rollback database schema immediately', 'Ignore until users complain more'], ans: 1, diff: 'easy', exp: 'Observability and reproducibility are crucial before applying fixes.' },
    { q: 'A test fails intermittently due to timing. Best fix strategy?', opts: ['Increase random sleep', 'Make assertions deterministic and mock time/external calls', 'Remove the test', 'Run test only locally'], ans: 1, diff: 'med', exp: 'Flaky tests are fixed by removing nondeterminism and isolating dependencies.' },
    { q: 'Which Git workflow is safest before refactoring critical logic?', opts: ['Direct commit to main', 'Create feature branch with small commits and tests', 'Edit production server directly', 'Disable CI checks'], ans: 1, diff: 'easy', exp: 'Feature branches plus tests reduce risk and improve rollback options.' },
    { q: 'If API latency doubled after a release, what should you do first?', opts: ['Scale hardware blindly', 'Measure endpoint timings and compare traces', 'Rewrite frontend', 'Drop indexes'], ans: 1, diff: 'med', exp: 'Profiling and traces identify actual bottlenecks before optimization.' },
    { q: 'What is the best way to prevent regressions in a bug-prone module?', opts: ['Rely on manual testing only', 'Add unit + integration tests around failure paths', 'Reduce comments', 'Increase timeout limits'], ans: 1, diff: 'hard', exp: 'Automated test coverage on critical paths catches regressions early.' }
  ]
};
