<div class="markdown-body container__DcUsa8" data-copilot-markdown="true" style="--MarkdownRenderer_streaming-fade-duration: 750ms;"><h1>Implementation plan: dependency-aware task mastery</h1>
<h2>1. Findings from the codebase</h2>
<p><strong>The repository is a task catalog plus an orchestration prototype—not yet a system that demonstrates task mastery.</strong></p>
<ul>
<li node="[object Object]">The task directory contains <strong>95 task definitions</strong>. The documented count of 94 is consistent with the workbench skipping Multiturn LaTeX Generation: that file uses a different title format.</li>
<li node="[object Object]"><code node="[object Object]">OpenCogWorkbench</code> loads task metadata, selects patterns and strategies, and exposes autonomous, collaborative, and guided modes.</li>
<li node="[object Object]">Agent-Zero defines five roles: analyzer, strategist, executor, validator, and learner.</li>
<li node="[object Object]">The pattern library contains ten cognitive patterns; the strategy repository contains seven strategy templates.</li>
<li node="[object Object]"><strong>Execution is simulated.</strong> Agent-Zero returns step-completion messages; the strategy executor explicitly simulates its actions.</li>
<li node="[object Object]"><strong>Success is not correctness.</strong> Agent-Zero initializes validation as passed and assigns completed runs a fixed quality score. Strategy success checks step completion.</li>
<li node="[object Object]">Difficulty currently depends on tag and example counts, not actual reasoning complexity.</li>
<li node="[object Object]">No native AtomSpace, Atomese, PLN, URE, ECAN, or MOSES integration appears in the inspected Python implementation.</li>
</ul>
<h3>Important implementation gaps</h3>
<table><thead><tr><th>Gap</th><th>Consequence for mastery planning</th></tr></thead><tbody><tr><td>Workbench parser reads only the line immediately following section headings</td><td>Blank lines or multiline sections can lose metadata.</td></tr><tr><td>Examples are not loaded into <code node="[object Object]">Task.examples</code></td><td>Existing demonstrations cannot support evaluation through the workbench.</td></tr><tr><td>Difficulty uses metadata counts</td><td>More examples can incorrectly make a task appear harder.</td></tr><tr><td>Pattern selection uses keyword matching</td><td>Recommendations do not establish prerequisite skills or executable capabilities.</td></tr><tr><td>Several referenced pattern IDs are not initialized patterns</td><td>Some architecture and strategy requirements cannot be resolved reliably.</td></tr><tr><td>Collaborative mode creates a session but executes the strategy directly</td><td>It does not yet demonstrate collaborative solving.</td></tr><tr><td>State saving covers patterns and strategies</td><td>Learner mastery, prerequisite progress, and benchmark results are not persisted.</td></tr></tbody></table>
<p><strong>Evidence:</strong> <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/opencog/workbench.py" target="_blank" rel="noopener noreferrer">workbench</a>, <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/opencog/agents/agent_zero.py" target="_blank" rel="noopener noreferrer">Agent-Zero</a>, <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/opencog/strategies/strategy_system.py" target="_blank" rel="noopener noreferrer">strategy system</a>, <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/opencog/patterns/pattern_library.py" target="_blank" rel="noopener noreferrer">pattern library</a>.</p>
<h2>2. What “optimal” should mean</h2>
<p>Use a <strong>prerequisite-constrained curriculum</strong>, rather than a single alphabetical or difficulty-only ordering.</p>
<p>Optimize for:</p>
<ol>
<li node="[object Object]">Reliable, independently measurable correctness.</li>
<li node="[object Object]">Skills that unlock the largest number of subsequent tasks.</li>
<li node="[object Object]">Reuse of already implemented reasoning subsystems.</li>
<li node="[object Object]">Minimal introduction of new subsystem complexity.</li>
<li node="[object Object]">Demonstrated generalization, not memorization of catalog examples.</li>
</ol>
<p>Rank difficulty using:</p>
<ul>
<li node="[object Object]">Reasoning depth and branching.</li>
<li node="[object Object]">Representation complexity.</li>
<li node="[object Object]">Ambiguity and missing information.</li>
<li node="[object Object]">Required domain knowledge.</li>
<li node="[object Object]">Belief nesting or conversational state.</li>
<li node="[object Object]">Difficulty of independently verifying an answer.</li>
</ul>
<p>Maintain two separate assessments:</p>
<ul>
<li node="[object Object]"><strong>Task difficulty:</strong> how hard representative instances are.</li>
<li node="[object Object]"><strong>Implementation readiness:</strong> whether the required capabilities and validators exist.</li>
</ul>
<p>The ranking below is an initial engineering hypothesis. Recalibrate it using benchmark results; task families contain instances of widely varying difficulty.</p>
<h2>3. OpenCog subsystem roadmap</h2>
<p>The local package named <code node="[object Object]">opencog</code> should not be confused with an installed native OpenCog stack.</p>
<table><thead><tr><th>Capability</th><th>Existing local foundation</th><th>Proposed implementation or integration</th></tr></thead><tbody><tr><td>Knowledge representation</td><td><code node="[object Object]">Task</code>, agent state, pattern dictionaries</td><td>AtomSpace/Atomese adapter for entities, relations, evidence, rules, and scoped contexts.</td></tr><tr><td>Deterministic inference</td><td>Logical-inference pattern</td><td>Boolean evaluator and rule execution; URE integration where appropriate.</td></tr><tr><td>Uncertain inference</td><td>Hypothesis-testing strategy</td><td>PLN integration or another calibrated probabilistic backend.</td></tr><tr><td>Planning and constraints</td><td>Decomposition, constraint, backward, recursive strategies</td><td>Executable search, constraint propagation, transition models, and plan verification.</td></tr><tr><td>Induction and analogy</td><td>Pattern-recognition and analogical patterns</td><td>Structural matching, candidate-rule generation, and transfer validation. MOSES is optional for suitable program-learning experiments.</td></tr><tr><td>Language understanding</td><td>Descriptions and keyword matching</td><td>Parsing and semantic grounding adapter; optional Link Grammar integration.</td></tr><tr><td>Temporal and spatial reasoning</td><td>Task descriptions only</td><td>Explicit temporal relations, coordinate models, transformations, and grounded computations.</td></tr><tr><td>Theory of mind</td><td>Agent state dictionaries</td><td>Agent-indexed knowledge and belief contexts with observation-sensitive updates.</td></tr><tr><td>Evaluation and learning</td><td>Validator/learner roles and success counters</td><td>Independent validators, calibration, mastery estimates, retention checks, and durable evidence.</td></tr><tr><td>Coordination</td><td>Message bus, queues, sessions</td><td>Actual agent handlers, dependency-aware execution, result aggregation, and bounded retries.</td></tr></tbody></table>
<p><strong>Do not require every native subsystem for every task.</strong> AtomSpace and rule execution are useful early foundations; PLN becomes valuable for uncertainty. ECAN is optional for later attention/resource allocation, not a prerequisite for basic correctness.</p>
<p>Native integration also needs a packaging decision: the repository’s own <code node="[object Object]">opencog</code> package may conflict with native Python bindings. Resolve import ownership before adopting those bindings.</p>
<h2>4. Ranked mastery sequence</h2>
<p><strong>Difficulty:</strong> D1 foundational; D2 elementary composition; D3 intermediate; D4 advanced contextual reasoning; D5 research-level or difficult-to-verify synthesis.</p>
<p>Each row is a mastery block. Tasks are listed in a recommended within-block order. This covers all <strong>95 catalog definitions</strong>.</p>
<p>Subsystem labels below describe capabilities to implement; they are not claims that those capabilities already exist.</p>
<table><thead><tr><th style="text-align: right;">Rank</th><th style="text-align: center;">Difficulty</th><th>Task mastery block, in recommended order</th><th>Required capabilities</th></tr></thead><tbody><tr><td style="text-align: right;">1</td><td style="text-align: center;">D1–2</td><td>Truth Table Completion → Syllogism Reasoning → Identifying Logical Inconsistencies → Constructing Valid Arguments</td><td>Boolean evaluation; knowledge representation; deterministic rules; proof checking.</td></tr><tr><td style="text-align: right;">2</td><td style="text-align: center;">D1–2</td><td>Identifying Relationships → Categorizing Information into Hierarchies → Completing Analogies → Evaluating Analogies for Accuracy</td><td>Typed relations; taxonomy queries; structural matching.</td></tr><tr><td style="text-align: right;">3</td><td style="text-align: center;">D2</td><td>Sequencing Events → Understanding Time-Based Relationships → Interpreting and Creating Timelines → Understanding Time Zones and Global Time Differences → Identifying Anachronisms</td><td>Temporal ordering; grounded date/time computation; historical evidence.</td></tr><tr><td style="text-align: right;">4</td><td style="text-align: center;">D2–3</td><td>Mathematical Word Problems → Equation Derivation → Solving Word Problems with Multiple Variables → Calculating Probabilities</td><td>Semantic-to-mathematical grounding; arithmetic/algebra; units; probability computation.</td></tr><tr><td style="text-align: right;">5</td><td style="text-align: center;">D2–3</td><td>Recognizing Patterns in Sequences → Deducing Rules from Examples → Pattern Recognition in Spatial Arrangements</td><td>Candidate-rule generation; structural matching; held-out rule testing.</td></tr><tr><td style="text-align: right;">6</td><td style="text-align: center;">D3</td><td>Deductive Logic Puzzles → Proof Verification → Critiquing Argument Structures → Identifying Logical Fallacies → Identifying Unstated Assumptions</td><td>Constraint solving; inference traces; counterexamples; argument representation.</td></tr><tr><td style="text-align: right;">7</td><td style="text-align: center;">D3</td><td>Stack-Based Reasoning → Towers of Hanoi → Reverse Engineering Processes → Deconstructing Complex Systems</td><td>Dependency planning; recursion; state transitions; backward search; decomposition.</td></tr><tr><td style="text-align: right;">8</td><td style="text-align: center;">D3</td><td>Describing Spatial Relationships → Mental Rotation Tasks → Spatial Problem-Solving</td><td>Spatial representation; coordinate transformations; geometric constraints.</td></tr><tr><td style="text-align: right;">9</td><td style="text-align: center;">D3</td><td>Analogy Creation → Analogical Problem Solving</td><td>Cross-domain structural mapping; adaptation; transfer verification.</td></tr><tr><td style="text-align: right;">10</td><td style="text-align: center;">D3–4</td><td>Parsing Complex Sentences → Interpreting Ambiguous Statements → Deciphering Ambiguous Instructions → Deconstructing Metaphors → Solving Riddles and Word Puzzles</td><td>Language grounding; multiple interpretations; clarification; semantic constraints.</td></tr><tr><td style="text-align: right;">11</td><td style="text-align: center;">D3–4</td><td>Distinguishing Fact from Opinion → Evaluating Source Credibility → Reconciling Conflicting Information → Identifying Hallucination-Prone Questions</td><td>Evidence provenance; source assessment; contradiction handling; calibrated abstention.</td></tr><tr><td style="text-align: right;">12</td><td style="text-align: center;">D3–4</td><td>Interpreting Statistical Data → Fermi Estimation → Estimating Duration → Inference Drawing from Incomplete Data → Assessing Risk and Uncertainty</td><td>Statistical computation; decomposition; uncertainty propagation; calibrated inference.</td></tr><tr><td style="text-align: right;">13</td><td style="text-align: center;">D4</td><td>Identifying Cause and Effect Relationships → Causal Chain Analysis → Distinguishing Correlation from Causation → Hypothesis Formation → Evaluating Competing Theories</td><td>Explicit causal models; evidence-sensitive hypothesis comparison; probabilistic inference.</td></tr><tr><td style="text-align: right;">14</td><td style="text-align: center;">D4</td><td>Predicting Outcomes Based on Scenarios → Counterfactual Analysis → Determining Alternative Outcomes → Analyzing Historical Counterfactuals</td><td>Scenario isolation; causal intervention semantics; temporal models; uncertainty.</td></tr><tr><td style="text-align: right;">15</td><td style="text-align: center;">D4</td><td>Analyzing Decision Trees → Analyzing Decision-Making Processes → Risk Assessment in Decision-Making → Prioritizing Conflicting Goals</td><td>Outcome probabilities; utility models; constrained planning; explicit trade-offs.</td></tr><tr><td style="text-align: right;">16</td><td style="text-align: center;">D4</td><td>Recognizing Patterns in Behavior → Trait Attribution in Behavioral Scenarios → Deducing Motives from Actions → Inferring Motivations from Actions → Inferring Emotional States</td><td>Behavioral evidence; alternative hypotheses; contextual inference; uncertainty.</td></tr><tr><td style="text-align: right;">17</td><td style="text-align: center;">D4</td><td>First-Order Ignorance → First-Order False Belief → Perspective-Taking in Social Scenarios → Critical Factor Identification in Theory of Mind</td><td>Agent-specific belief contexts; observation/access tracking; perspective-conditioned predictions.</td></tr><tr><td style="text-align: right;">18</td><td style="text-align: center;">D4–5</td><td>Second-Order False Belief → Higher Order False Belief</td><td>Nested belief contexts; bounded recursive inference; belief-update traces.</td></tr><tr><td style="text-align: right;">19</td><td style="text-align: center;">D4–5</td><td>Recognizing Emotional Subtext → Detecting Sarcasm and Irony → Interpreting Body Language Cues → Interpreting Nonverbal Communication → Analyzing Cultural Differences → Analyzing Rhetorical Strategies</td><td>Pragmatic language grounding; contextual knowledge; theory of mind; cultural uncertainty.</td></tr><tr><td style="text-align: right;">20</td><td style="text-align: center;">D4–5</td><td>Bias Detection → Identifying Cognitive Biases → Identifying Implicit Biases in Language → Bias Mitigation</td><td>Bias taxonomy; evidence auditing; argument analysis; unsupported-claim prevention.</td></tr><tr><td style="text-align: right;">21</td><td style="text-align: center;">D4–5</td><td>Narrative Gap Filling → Lateral Thinking Puzzles → Generating Creative Solutions</td><td>Abduction; candidate generation; coherence and feasibility checks; novelty assessment.</td></tr><tr><td style="text-align: right;">22</td><td style="text-align: center;">D5</td><td>Interpreting Legal Language and Precedents</td><td>Language grounding; jurisdiction/time-scoped evidence; defeasible rules; precedent comparison; expert validation.</td></tr><tr><td style="text-align: right;">23</td><td style="text-align: center;">D5</td><td>Trend Analysis and Forecasting → Predicting Market Trends → Forecasting Technological Impacts → Evaluating Policy Implications → Moral Reasoning in Everyday Situations → Ethical Dilemma Resolution</td><td>Temporal forecasting; causal uncertainty; domain evidence; stakeholder/value models; rubric evaluation.</td></tr><tr><td style="text-align: right;">24</td><td style="text-align: center;">D5</td><td>Unraveling Paradoxes → Curry’s Paradox</td><td>Explicit logical foundations; self-reference analysis; proof auditing; alternative semantic frameworks.</td></tr><tr><td style="text-align: right;">25</td><td style="text-align: center;">D4–5</td><td>Multiturn LaTeX Generation</td><td>Persistent conversation/document state; constraint tracking; generation; sandboxed compilation; rendered-layout validation.</td></tr></tbody></table>
<h3>Prerequisite rules that override the table</h3>
<ul>
<li node="[object Object]"><strong>Logic → constraints → planning → decision-making.</strong></li>
<li node="[object Object]"><strong>Relations → pattern induction → analogy → creative transfer.</strong></li>
<li node="[object Object]"><strong>Probability + evidence handling → causal inference → counterfactuals → forecasting.</strong></li>
<li node="[object Object]"><strong>Temporal updates + scoped beliefs → first-order → second-order → higher-order theory of mind.</strong></li>
<li node="[object Object]"><strong>Language grounding + evidence handling → pragmatics, bias analysis, and legal interpretation.</strong></li>
<li node="[object Object]"><strong>Decision-making + causal reasoning + perspective-taking → policy and ethical synthesis.</strong></li>
</ul>
<p>Independent branches can advance in parallel. LaTeX is a separate artifact-generation branch: its final position reflects distinct tooling and validation needs, not a prerequisite on paradox mastery.</p>
<h2>5. Implementation stages</h2>
<h3>Stage A — Make the catalog trustworthy</h3>
<p><strong>Primary extension point:</strong> <code node="[object Object]">OpenCogWorkbench</code> task loading.</p>
<ul>
<li node="[object Object]">Establish canonical task IDs from filenames.</li>
<li node="[object Object]">Preserve complete descriptions, modalities, tags, and example conversations.</li>
<li node="[object Object]">Support or explicitly normalize the nonstandard LaTeX definition.</li>
<li node="[object Object]">Report malformed or skipped definitions rather than silently excluding them.</li>
<li node="[object Object]">Add curriculum metadata: prerequisite skills, difficulty rationale, subsystem requirements, evaluator type, and benchmark version.</li>
<li node="[object Object]">Check consistency between Markdown and generated JSON; avoid maintaining conflicting metadata copies.</li>
<li node="[object Object]">Audit examples before promoting them to ground truth.</li>
</ul>
<p><strong>Acceptance gate:</strong> all 95 definitions are accounted for, with explicit validation results and no unexplained omissions.</p>
<h3>Stage B — Establish honest execution and evaluation</h3>
<p><strong>Primary extension points:</strong> Agent-Zero and <code node="[object Object]">StrategyExecutor</code>.</p>
<ul>
<li node="[object Object]">Distinguish task families from concrete task instances.</li>
<li node="[object Object]">Define a common execution result containing the answer/artifact, supporting evidence, confidence, resource usage, and errors.</li>
<li node="[object Object]">Replace simulated actions incrementally with executable handlers.</li>
<li node="[object Object]">Distinguish completed execution, correct answer, unsupported capability, and failed validation.</li>
<li node="[object Object]">Introduce independent evaluator dispatch.</li>
<li node="[object Object]">Ensure only evaluated outcomes update pattern, strategy, or mastery statistics.</li>
<li node="[object Object]">Keep guided mode useful without presenting recommendations as completed solutions.</li>
</ul>
<p><strong>Acceptance gate:</strong> incorrect answers fail even when every workflow step completes.</p>
<h3>Stage C — Deliver the deterministic foundation</h3>
<p>Implement blocks 1–8, starting with truth tables and bounded syllogisms.</p>
<ul>
<li node="[object Object]">Build representation and rule-execution foundations.</li>
<li node="[object Object]">Add arithmetic, temporal, constraint, planning, and spatial handlers as their branches become ready.</li>
<li node="[object Object]">Use independently verifiable outputs rather than free-form explanations alone.</li>
<li node="[object Object]">Give plans replayable state transitions and proofs checkable steps.</li>
<li node="[object Object]">Verify Hanoi legality, final state, and minimum move counts for applicable instances.</li>
<li node="[object Object]">Treat ambiguous spatial and temporal inputs as underdetermined when necessary.</li>
</ul>
<p><strong>Acceptance gate:</strong> strong held-out performance, correct rejection of invalid inputs, and successful generalization to larger or recombined instances.</p>
<h3>Stage D — Implement curriculum scheduling and mastery state</h3>
<p><strong>Primary extension points:</strong> workbench recommendations and Agent-Zero analysis.</p>
<ul>
<li node="[object Object]">Replace metadata-count difficulty with reviewed capability-based estimates.</li>
<li node="[object Object]">Represent prerequisites as a directed acyclic graph; validate unknown references and cycles.</li>
<li node="[object Object]">Select only tasks whose prerequisite skills and required backends are ready.</li>
<li node="[object Object]">Prioritize ready tasks by learning need, downstream benefit, verification reliability, and incremental subsystem cost.</li>
<li node="[object Object]">Include spaced review and targeted remediation.</li>
<li node="[object Object]">Persist per-skill mastery, attempts, benchmark versions, evaluator evidence, and uncertainty.</li>
<li node="[object Object]">Keep curriculum dependencies separate from the pattern library’s related-pattern graph.</li>
</ul>
<p><strong>Acceptance gate:</strong> scheduling is reproducible, explainable, prerequisite-safe, and resumable after restart.</p>
<h3>Stage E — Add language, uncertainty, and causal reasoning</h3>
<p>Implement blocks 9–15.</p>
<ul>
<li node="[object Object]">Ground language into explicit representations before inference.</li>
<li node="[object Object]">Add provenance, clarification, and abstention.</li>
<li node="[object Object]">Integrate calibrated probabilistic reasoning where needed.</li>
<li node="[object Object]">Represent causal assumptions and interventions explicitly; do not equate conditional inference with causation.</li>
<li node="[object Object]">Separate competing hypotheses and counterfactual worlds.</li>
<li node="[object Object]">Validate decisions against declared probabilities, constraints, and objectives.</li>
</ul>
<p><strong>Acceptance gate:</strong> evidence-backed answers outperform simple baselines, uncertainty is calibrated, and insufficient information produces appropriate clarification or abstention.</p>
<h3>Stage F — Add social reasoning and synthesis</h3>
<p>Implement blocks 16–24.</p>
<ul>
<li node="[object Object]">Model each agent’s observations, knowledge, beliefs, and goals separately from world truth.</li>
<li node="[object Object]">Increase belief-nesting depth only after shallower levels pass.</li>
<li node="[object Object]">Evaluate social interpretations as hypotheses rather than certain psychological facts.</li>
<li node="[object Object]">Add rubrics for creativity, cultural interpretation, ethics, and policy.</li>
<li node="[object Object]">Scope legal claims by jurisdiction and date.</li>
<li node="[object Object]">Require explicit logical assumptions for paradox analysis.</li>
</ul>
<p><strong>Acceptance gate:</strong> performance survives paraphrases, distractors, perspective changes, and conflicting evidence; open-ended quality is confirmed through independent rubric assessment.</p>
<h3>Stage G — Complete artifact generation and real orchestration</h3>
<p>Implement block 25 and strengthen coordination where it demonstrably helps.</p>
<ul>
<li node="[object Object]">Preserve conversation history and versioned document state.</li>
<li node="[object Object]">Validate requested content, formatting, compilation, and rendered layout.</li>
<li node="[object Object]">Sandbox generated LaTeX with restricted filesystem/process access and resource limits.</li>
<li node="[object Object]">Connect orchestration sessions to actual agent handlers and final-result aggregation.</li>
<li node="[object Object]">Enforce budgets, timeouts, and bounded retries.</li>
<li node="[object Object]">Compare multi-agent results with single-agent baselines before making collaboration the default.</li>
</ul>
<p><strong>Acceptance gate:</strong> document edits preserve earlier constraints, artifacts validate safely, and collaboration provides measurable quality or efficiency gains.</p>
<h2>6. Mastery measurement</h2>
<p>Do not use the current success counters as evidence of mastery.</p>
<p>Use:</p>
<ul>
<li node="[object Object]"><strong>Formal tasks:</strong> exact outputs, proof checks, constraint satisfaction, and replayable plans.</li>
<li node="[object Object]"><strong>Numerical tasks:</strong> independent computation, units, and declared tolerances.</li>
<li node="[object Object]"><strong>Uncertain tasks:</strong> accuracy plus calibration, evidence quality, and appropriate abstention.</li>
<li node="[object Object]"><strong>Social/open-ended tasks:</strong> multiple acceptable answers, explicit rubrics, and independent review.</li>
<li node="[object Object]"><strong>Artifact tasks:</strong> compilation, content checks, layout checks, and cross-turn consistency.</li>
</ul>
<p>Suggested initial promotion policy:</p>
<ul>
<li node="[object Object]">At least 95% held-out correctness for deterministic families.</li>
<li node="[object Object]">A separately calibrated threshold for probabilistic or rubric-scored families.</li>
<li node="[object Object]">Successful transfer to unseen structures, not merely unseen wording.</li>
<li node="[object Object]">A later retention check.</li>
<li node="[object Object]">No promotion when benchmark coverage is insufficient.</li>
</ul>
<p>These are proposed policy defaults, not measured repository performance.</p>
<h3>Dataset issues to address before benchmarking</h3>
<ul>
<li node="[object Object]">The mental-rotation cube example does not specify which symbol is opposite the star.</li>
<li node="[object Object]">The time-zone examples omit dates needed to resolve seasonal offsets.</li>
<li node="[object Object]">Bias-mitigation examples sometimes introduce personal histories absent from the input.</li>
</ul>
<p>Evidence: <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/tasks/mental-rotation-tasks.md" target="_blank" rel="noopener noreferrer">mental rotation</a>, <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/tasks/understanding-time-zones-and-global-time-differences.md" target="_blank" rel="noopener noreferrer">time zones</a>, <a href="/home/runner/work/OpenCog-Reasoning-Tasks/OpenCog-Reasoning-Tasks/tasks/bias-mitigation.md" target="_blank" rel="noopener noreferrer">bias mitigation</a>.</p>
<p>The repository’s npm test command is a placeholder, and no Python test files were found. Implementation therefore needs a real evaluation suite; demo completion alone is not a mastery gate.</p>
<h2>Recommended first deliverable</h2>
<p><strong>A correctly loaded catalog, truthful execution statuses, independent validators for truth tables and syllogisms, and a persisted prerequisite-aware scheduler.</strong></p>
<p>That creates a measurable foundation for expanding through the curriculum without mistaking orchestration activity for reasoning competence.</p></div>
