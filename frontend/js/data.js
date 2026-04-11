// ========== SKILLS CONFIG ==========
const SKILLS = [
  { id: 'math', name: 'DSA Foundations', icon: '🧩', desc: 'Arrays, complexity, recursion, trees', badgeClass: 'skill-math', color: '#378ADD' },
  { id: 'logic', name: 'Algorithmic Reasoning', icon: '🧠', desc: 'Tracing, optimization, edge cases', badgeClass: 'skill-logic', color: '#7F77DD' },
  { id: 'aptitude', name: 'CS Fundamentals', icon: '💾', desc: 'DBMS, OS, networks, OOP basics', badgeClass: 'skill-aptitude', color: '#BA7517' },
  { id: 'problem', name: 'Debugging & Engineering', icon: '🛠️', desc: 'Testing, debugging, practical coding', badgeClass: 'skill-problem', color: '#1D9E75' }
];

// ========== QUESTION BANK (10 questions per skill) ==========
const QUESTIONS = {
  math: [
    { q: 'What is the time complexity of binary search on a sorted array?', opts: ['O(n)', 'O(log n)', 'O(n log n)', 'O(1)'], ans: 1, diff: 'easy', exp: 'Binary search halves the search space each step, so complexity is O(log n).' },
    { q: 'Which data structure is best for implementing LRU cache lookup/update in O(1)?', opts: ['Array + stack', 'HashMap + Doubly Linked List', 'Queue only', 'Binary Search Tree'], ans: 1, diff: 'med', exp: 'HashMap gives O(1) access and doubly linked list supports O(1) move/remove.' },
    { q: 'Which traversal gives sorted order for a Binary Search Tree?', opts: ['Preorder', 'Inorder', 'Postorder', 'Level order'], ans: 1, diff: 'easy', exp: 'Inorder traversal of BST visits keys in non-decreasing order.' },
    { q: 'What is the worst-case complexity of quicksort?', opts: ['O(n)', 'O(n log n)', 'O(log n)', 'O(n^2)'], ans: 3, diff: 'med', exp: 'Worst case occurs with highly unbalanced partitions, giving O(n^2).' },
    { q: 'For recursion to work correctly, which is mandatory?', opts: ['A loop', 'A base case', 'A hash map', 'A queue'], ans: 1, diff: 'hard', exp: 'Without a base case, recursion does not terminate.' },
    { q: 'What is the space complexity of mergesort?', opts: ['O(1)', 'O(log n)', 'O(n)', 'O(n^2)'], ans: 2, diff: 'med', exp: 'Mergesort requires O(n) auxiliary space for the merge step.' },
    { q: 'Which data structure uses LIFO order?', opts: ['Queue', 'Stack', 'Deque', 'Priority Queue'], ans: 1, diff: 'easy', exp: 'Stack is a Last-In-First-Out (LIFO) structure.' },
    { q: 'How many edges does a spanning tree of n nodes have?', opts: ['n', 'n-1', 'n+1', '2n'], ans: 1, diff: 'med', exp: 'A spanning tree with n nodes has exactly n-1 edges.' },
    { q: 'What is the time complexity of inserting into a min-heap?', opts: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], ans: 1, diff: 'med', exp: 'Heap insertion requires sifting up which takes O(log n).' },
    { q: 'Which algorithm is used for topological sorting?', opts: ['BFS only', 'DFS with finish time / Kahns BFS', 'Dijkstra', "Prim's"], ans: 1, diff: 'hard', exp: "DFS with reverse finishing order (or Kahn's BFS) gives topological order." }
  ],
  logic: [
    { q: 'If an algorithm has two nested loops over n elements each, typical complexity is:', opts: ['O(log n)', 'O(n)', 'O(n^2)', 'O(2^n)'], ans: 2, diff: 'easy', exp: 'Two full loops over n usually result in O(n^2) operations.' },
    { q: 'Which strategy guarantees optimal solution for weighted shortest path with non-negative edges?', opts: ['DFS', 'BFS', 'Dijkstra', 'Union-Find'], ans: 2, diff: 'med', exp: 'Dijkstra is correct for non-negative edge weights.' },
    { q: 'What is the primary purpose of dynamic programming?', opts: ['Randomization', 'Store overlapping subproblem results', 'Avoid recursion always', 'Reduce input size'], ans: 1, diff: 'easy', exp: 'DP caches repeated subproblem results to avoid recomputation.' },
    { q: 'You have sorted logs and need first occurrence of value. Best approach?', opts: ['Linear scan', 'Binary search variant', 'Hash all values', 'Stack simulation'], ans: 1, diff: 'med', exp: 'A modified binary search can find first occurrence in O(log n).' },
    { q: 'Which scenario indicates a greedy algorithm may fail?', opts: ['Optimal substructure exists', 'Local choice blocks future optimum', 'Data is sorted', 'Graph is connected'], ans: 1, diff: 'hard', exp: 'Greedy fails when local optimum does not lead to global optimum.' },
    { q: 'What algorithmic paradigm does Fibonacci memoization use?', opts: ['Greedy', 'Divide and Conquer', 'Dynamic Programming', 'Backtracking'], ans: 2, diff: 'easy', exp: 'Memoizing Fibonacci subproblems is a classic top-down DP example.' },
    { q: 'In a graph with V vertices and E edges, BFS time complexity is:', opts: ['O(V)', 'O(E)', 'O(V + E)', 'O(V x E)'], ans: 2, diff: 'med', exp: 'BFS visits each vertex and edge once, giving O(V + E).' },
    { q: 'Which problem is solved by the sliding window technique?', opts: ['Finding shortest path', 'Max sum subarray of size k', 'Cycle detection', 'Matrix multiplication'], ans: 1, diff: 'med', exp: 'Sliding window efficiently solves fixed/variable window subarray problems.' },
    { q: 'The edit distance problem is best solved with:', opts: ['Greedy', 'Binary search', '2D dynamic programming', 'Recursion without memoization'], ans: 2, diff: 'hard', exp: 'Edit distance (Levenshtein) requires a 2D DP table over both strings.' },
    { q: 'Which invariant must a two-pointer technique maintain to work correctly?', opts: ['Both pointers at same index', 'Monotonic property of the search window', 'Array must be unsorted', 'Pointers must never meet'], ans: 1, diff: 'hard', exp: 'Two pointers work when the window has a monotonic property to exploit.' }
  ],
  aptitude: [
    { q: 'Which SQL command removes all rows but keeps table structure?', opts: ['DROP TABLE', 'DELETE TABLE', 'TRUNCATE TABLE', 'REMOVE'], ans: 2, diff: 'easy', exp: 'TRUNCATE removes rows while preserving schema.' },
    { q: 'What does ACID property ensure in DBMS?', opts: ['Only speed', 'Reliable transactions', 'Data compression', 'Network security'], ans: 1, diff: 'easy', exp: 'ACID ensures transaction correctness and reliability.' },
    { q: 'Which OS concept allows multiple processes to share CPU effectively?', opts: ['Caching', 'Scheduling', 'Indexing', 'Virtualization only'], ans: 1, diff: 'med', exp: 'CPU scheduling decides process execution order and fairness.' },
    { q: 'Which layer handles routing in the OSI model?', opts: ['Transport', 'Session', 'Network', 'Data Link'], ans: 2, diff: 'med', exp: 'Routing is handled by the Network layer (Layer 3).' },
    { q: 'What does encapsulation mean in OOP?', opts: ['Multiple inheritance', 'Binding data and methods with controlled access', 'Only function overloading', 'Runtime polymorphism'], ans: 1, diff: 'hard', exp: 'Encapsulation combines data and behavior while restricting direct access.' },
    { q: 'Which normal form eliminates transitive dependencies?', opts: ['1NF', '2NF', '3NF', 'BCNF'], ans: 2, diff: 'med', exp: '3NF removes transitive functional dependencies from non-key attributes.' },
    { q: 'A deadlock requires which four conditions?', opts: ['CPU + RAM + IO + Network', 'Mutual exclusion, Hold and Wait, No preemption, Circular wait', 'Process + Thread + Fork + Join', 'Starvation + Livelock + Aging + Preemption'], ans: 1, diff: 'hard', exp: "Coffman's four conditions: mutual exclusion, hold and wait, no preemption, circular wait." },
    { q: 'What is the key difference between TCP and UDP?', opts: ['TCP is faster, UDP is reliable', 'TCP is reliable and ordered, UDP is faster but unreliable', 'Both are identical', 'UDP uses handshake, TCP does not'], ans: 1, diff: 'easy', exp: 'TCP provides reliability with overhead; UDP trades reliability for speed.' },
    { q: 'Which concept describes an object taking many forms in OOP?', opts: ['Abstraction', 'Encapsulation', 'Polymorphism', 'Cohesion'], ans: 2, diff: 'easy', exp: 'Polymorphism lets objects of different classes be treated uniformly.' },
    { q: 'In a B-tree of order m, each internal node has at most:', opts: ['m children', 'm-1 children', '2m children', 'm+1 children'], ans: 0, diff: 'hard', exp: 'A B-tree of order m allows up to m children per internal node.' }
  ],
  problem: [
    { q: 'A bug appears only in production. What is the best first step?', opts: ['Rewrite module', 'Add targeted logs and reproduce issue', 'Rollback database schema immediately', 'Ignore until users complain more'], ans: 1, diff: 'easy', exp: 'Observability and reproducibility are crucial before applying fixes.' },
    { q: 'A test fails intermittently due to timing. Best fix strategy?', opts: ['Increase random sleep', 'Make assertions deterministic and mock time/external calls', 'Remove the test', 'Run test only locally'], ans: 1, diff: 'med', exp: 'Flaky tests are fixed by removing nondeterminism and isolating dependencies.' },
    { q: 'Which Git workflow is safest before refactoring critical logic?', opts: ['Direct commit to main', 'Create feature branch with small commits and tests', 'Edit production server directly', 'Disable CI checks'], ans: 1, diff: 'easy', exp: 'Feature branches plus tests reduce risk and improve rollback options.' },
    { q: 'If API latency doubled after a release, what should you do first?', opts: ['Scale hardware blindly', 'Measure endpoint timings and compare traces', 'Rewrite frontend', 'Drop indexes'], ans: 1, diff: 'med', exp: 'Profiling and traces identify actual bottlenecks before optimization.' },
    { q: 'What is the best way to prevent regressions in a bug-prone module?', opts: ['Rely on manual testing only', 'Add unit + integration tests around failure paths', 'Reduce comments', 'Increase timeout limits'], ans: 1, diff: 'hard', exp: 'Automated test coverage on critical paths catches regressions early.' },
    { q: 'Code review finds a function that does 5 things. Correct fix?', opts: ['Add more comments', 'Refactor into single-responsibility functions', 'Increase function size', 'Ignore it'], ans: 1, diff: 'med', exp: 'Single Responsibility Principle: each function should do one thing well.' },
    { q: 'Which testing type validates the full system end-to-end?', opts: ['Unit test', 'Integration test', 'End-to-end test', 'Smoke test'], ans: 2, diff: 'easy', exp: 'E2E tests simulate real user journeys across the full system stack.' },
    { q: 'Memory leaks are appearing. First diagnostic step?', opts: ['Increase RAM', 'Profile heap allocations and find uncleaned references', 'Restart application daily', 'Reduce log verbosity'], ans: 1, diff: 'med', exp: 'Heap profiling identifies which objects are accumulating and why.' },
    { q: 'When should you write a test BEFORE writing code?', opts: ['Never, tests come after', 'In Test-Driven Development (TDD)', 'Only for frontend code', 'Only for database code'], ans: 1, diff: 'easy', exp: 'TDD writes failing tests first, then implements code to pass them.' },
    { q: "A colleague's code works but is unreadable. Best PR review response?", opts: ['Approve silently', 'Reject without comment', 'Request readable names and comments for complex logic', 'Rewrite their code without asking'], ans: 2, diff: 'hard', exp: 'Constructive reviews request specific, actionable improvements respectfully.' }
  ]
};

// ========== MOCK INTERVIEW TOPICS ==========
const MOCK_INTERVIEW_TOPICS = [
  { id: 'dsa_basics', label: 'DSA Basics', icon: '🧩' },
  { id: 'system_design', label: 'System Design', icon: '🏗️' },
  { id: 'dbms_os', label: 'DBMS & OS', icon: '💾' },
  { id: 'hr_behavioral', label: 'HR / Behavioral', icon: '🤝' },
  { id: 'gate_prep', label: 'GATE Prep', icon: '🎓' },
];

// ========== ACHIEVEMENT DEFINITIONS ==========
const ACHIEVEMENTS = [
  { id: 'first_assessment', icon: '🏆', label: 'First Assessment', desc: 'Complete your first assessment', condition: s => s.assessmentCount >= 1 },
  { id: 'score_80', icon: '⭐', label: 'High Scorer', desc: 'Score 80 or above', condition: s => s.bestScore >= 80 },
  { id: 'score_90', icon: '🔥', label: 'Elite Score', desc: 'Score 90 or above', condition: s => s.bestScore >= 90 },
  { id: 'all_skills', icon: '🎯', label: 'Full Stack', desc: 'Take assessment with all 4 skills', condition: s => s.allSkillsDone },
  { id: 'streak_3', icon: '📅', label: '3-Day Streak', desc: 'Assess 3 days in a row', condition: s => s.streak >= 3 },
  { id: 'streak_7', icon: '🔮', label: 'Week Warrior', desc: 'Assess 7 days in a row', condition: s => s.streak >= 7 },
  { id: 'career_analyst', icon: '🌍', label: 'Career Analyst', desc: 'Analyze all 3 career paths', condition: s => s.careerPathsAnalyzed >= 3 },
  { id: 'gate_analyzed', icon: '🎓', label: 'GATE Explorer', desc: 'Run a GATE skill gap analysis', condition: s => (s.careerPathsAnalyzedSet||[]).includes('gate') },
  { id: 'all_paths_done', icon: '🌟', label: 'Triple Threat', desc: 'Analyze all 3 career paths (GATE, Govt, Abroad)', condition: s => s.careerPathsAnalyzed >= 3 },
];

// ========== LOCAL STORAGE HELPERS ==========
const Store = {
  KEY: 'skilliq_progress',
  get() {
    try { return JSON.parse(localStorage.getItem(this.KEY)) || this.defaults(); } catch(e) { return this.defaults(); }
  },
  save(data) {
    try { localStorage.setItem(this.KEY, JSON.stringify(data)); } catch(e) {}
  },
  defaults() {
    return {
      assessmentCount: 0, bestScore: 0, assessmentHistory: [],
      streak: 0, lastAssessmentDate: null, allSkillsDone: false,
      careerPathsAnalyzed: 0, careerPathsAnalyzedSet: [],
      careerAnalysesDone: 0, unlockedAchievements: [], weeklyScores: [],
    };
  },
  recordAssessment(result, skillIds) {
    const data = this.get();
    data.assessmentCount++;
    if (result.overallScore > data.bestScore) data.bestScore = result.overallScore;
    if (skillIds.length === 4) data.allSkillsDone = true;
    const today = new Date().toDateString();
    if (data.lastAssessmentDate !== today) {
      const yesterday = new Date(Date.now() - 86400000).toDateString();
      data.streak = data.lastAssessmentDate === yesterday ? data.streak + 1 : 1;
      data.lastAssessmentDate = today;
    }
    data.weeklyScores.push({ date: today, score: result.overallScore });
    if (data.weeklyScores.length > 7) data.weeklyScores = data.weeklyScores.slice(-7);
    data.assessmentHistory.unshift({
      date: new Date().toLocaleString(), score: result.overallScore, skills: skillIds,
      accuracy: result.totalAns ? Math.round(result.totalCorrect / result.totalAns * 100) : 0,
    });
    if (data.assessmentHistory.length > 10) data.assessmentHistory = data.assessmentHistory.slice(0, 10);
    this.save(data);
    return this.checkNewAchievements(data);
  },
  recordCareerAnalysis(goal) {
    const data = this.get();
    if (!data.careerPathsAnalyzedSet) data.careerPathsAnalyzedSet = [];
    if (!data.careerPathsAnalyzedSet.includes(goal)) {
      data.careerPathsAnalyzedSet.push(goal);
      data.careerPathsAnalyzed = data.careerPathsAnalyzedSet.length;
    }
    data.careerAnalysesDone = (data.careerAnalysesDone || 0) + 1;
    // Track streak via analysis
    const today = new Date().toDateString();
    if (data.lastAssessmentDate !== today) {
      const yesterday = new Date(Date.now() - 86400000).toDateString();
      data.streak = data.lastAssessmentDate === yesterday ? data.streak + 1 : 1;
      data.lastAssessmentDate = today;
    }
    data.assessmentCount = (data.assessmentCount || 0) + 1;
    data.weeklyScores = data.weeklyScores || [];
    data.weeklyScores.push({ date: today, score: 0 });
    if (data.weeklyScores.length > 7) data.weeklyScores = data.weeklyScores.slice(-7);
    this.save(data);
    return this.checkNewAchievements(data);
  },
  recordMockInterview() {
    const data = this.get();
    data.mockInterviewsDone = (data.mockInterviewsDone || 0) + 1;
    this.save(data);
    return this.checkNewAchievements(data);
  },
  checkNewAchievements(data) {
    const newlyUnlocked = [];
    ACHIEVEMENTS.forEach(ach => {
      if (!data.unlockedAchievements.includes(ach.id) && ach.condition(data)) {
        data.unlockedAchievements.push(ach.id);
        newlyUnlocked.push(ach);
      }
    });
    if (newlyUnlocked.length) this.save(data);
    return newlyUnlocked;
  }
};
