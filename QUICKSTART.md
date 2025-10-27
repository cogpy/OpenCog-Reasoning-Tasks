# OpenCog Workbench - Quick Start Guide

## Installation

No external dependencies required! The OpenCog Workbench uses only Python standard library.

```bash
# Clone the repository
git clone https://github.com/cogpy/OpenCog-Reasoning-Tasks.git
cd OpenCog-Reasoning-Tasks

# Run the demo
python3 opencog_demo.py
```

## Basic Usage

### 1. Initialize the Workbench

```python
from opencog import OpenCogWorkbench

# Initialize with reasoning tasks
workbench = OpenCogWorkbench(tasks_dir="tasks")

# View statistics
stats = workbench.get_statistics()
print(f"Loaded {stats['tasks']['total']} reasoning tasks")
print(f"Available patterns: {stats['patterns']['total']}")
print(f"Available strategies: {stats['strategies']['total']}")
```

### 2. Explore the Pattern Language

```python
# Get the pattern catalog
catalog = workbench.get_pattern_catalog()

# View patterns by category
for category, patterns in catalog['categories'].items():
    print(f"\n{category}: {len(patterns)} patterns")
    for pattern in patterns[:3]:
        print(f"  - {pattern['name']}")

# Get a specific pattern
pattern = workbench.pattern_library.get_pattern("decomposition_pattern")
print(f"\nPattern: {pattern.name}")
print(f"Context: {pattern.context}")
print(f"Solution: {pattern.solution}")
```

### 3. Solve Reasoning Tasks

```python
# Get task recommendations
task_id = "towers-of-hanoi"
recommendations = workbench.get_task_recommendations(task_id)

print(f"\nRecommended patterns for {task_id}:")
for pattern in recommendations['recommended_patterns'][:3]:
    print(f"  - {pattern['name']}")

print(f"\nRecommended strategies:")
for strategy in recommendations['recommended_strategies'][:3]:
    print(f"  - {strategy['name']} ({strategy['type']})")

# Solve the task
result = workbench.solve_task(task_id, orchestration_mode="collaborative")
print(f"\nTask solved: {result['success']}")
print(f"Patterns used: {result['patterns_used']}")
print(f"Strategy: {result.get('strategy', 'N/A')}")
```

### 4. Use Agent-Zero Directly

```python
from opencog.agents.agent_zero import Task

# Create a task
task = Task(
    id="my_task",
    name="My Reasoning Task",
    description="A complex reasoning challenge",
    modality="Text only",
    tags=["Reasoning", "Problem Solving"]
)

# Let Agent-Zero orchestrate the solution
result = workbench.agent_zero.orchestrate_task(task)

print(f"Analysis: {result['analysis']}")
print(f"Architecture: {result['architecture']}")
print(f"Validation: {result['validation']}")
```

### 5. Multi-Agent Orchestration

```python
# Create a session
session_id = "reasoning_session_001"
agents = list(workbench.agent_zero.agents.keys())
session = workbench.orchestrator.create_session(session_id, agents)

# Prepare a task
task_dict = {
    "id": "logic_puzzle",
    "name": "Complex Logic Puzzle",
    "description": "Multi-step logic puzzle",
    "required_capabilities": ["reasoning", "problem_solving"]
}

# Orchestrate with collaborative strategy
result = workbench.orchestrator.orchestrate_multi_agent_task(
    session_id,
    task_dict,
    strategy="collaborative"
)

print(f"Agents involved: {len(result['agents_involved'])}")
print(f"Strategy: {result['strategy']}")
```

## Orchestration Modes

### Autonomous Mode
Agent-Zero fully controls the entire solution process:
```python
result = workbench.solve_task(task_id, orchestration_mode="autonomous")
```

### Collaborative Mode
Multiple agents work together with coordination:
```python
result = workbench.solve_task(task_id, orchestration_mode="collaborative")
```

### Guided Mode
Get analysis and recommendations for manual execution:
```python
result = workbench.solve_task(task_id, orchestration_mode="guided")
print(result['suggested_patterns'])
print(result['suggested_strategies'])
```

## Working with Patterns

### Add a New Pattern

```python
from opencog.patterns.pattern_library import (
    CognitivePattern, PatternCategory, PatternQuality
)

new_pattern = CognitivePattern(
    id="my_pattern",
    name="My Custom Pattern",
    category=PatternCategory.PROBLEM_SOLVING,
    context="When facing problems that...",
    problem="The problem this solves...",
    forces=[
        "Force 1: ...",
        "Force 2: ...",
        "Force 3: ..."
    ],
    solution="The solution approach is...",
    examples=[
        {
            "task": "Example task",
            "application": "How to apply the pattern"
        }
    ],
    related_patterns=["decomposition_pattern"],
    quality=PatternQuality.EXPERIMENTAL
)

workbench.pattern_library.add_pattern(new_pattern)
```

### Record Pattern Usage

```python
# Record successful use
workbench.pattern_library.record_pattern_use("decomposition_pattern", success=True)

# Pattern evolves with usage
pattern = workbench.pattern_library.get_pattern("decomposition_pattern")
print(f"Use count: {pattern.use_count}")
print(f"Success rate: {pattern.success_rate}")
print(f"Quality: {pattern.quality.value}")
```

## Working with Strategies

### Create a Hybrid Strategy

```python
# Get two strategies
strategy1 = workbench.strategy_repository.get_strategy("decomposition_strategy")
strategy2 = workbench.strategy_repository.get_strategy("pattern_matching_strategy")

# Compose them
hybrid = workbench.strategy_repository.compose_hybrid_strategy(
    [strategy1, strategy2],
    task_context={"complexity": "high"}
)

print(f"Hybrid strategy: {hybrid.name}")
print(f"Combined patterns: {hybrid.applicable_patterns}")
```

### Execute a Strategy

```python
strategy = workbench.strategy_repository.get_strategy("decomposition_strategy")

task_dict = {
    "id": "complex_task",
    "name": "Complex Task",
    "description": "A challenging problem"
}

execution = workbench.strategy_executor.execute_strategy(
    strategy,
    task_dict
)

print(f"Success: {execution['success']}")
print(f"Steps: {len(execution['steps_executed'])}")
```

## Saving and Loading State

```python
# Save workbench state
workbench.save_state("workbench_state")

# This saves:
# - workbench_state/patterns.json
# - workbench_state/strategies.json

# Later, load the state
workbench.pattern_library.load_library("workbench_state/patterns.json")
```

## Advanced Features

### Pattern Relationships

```python
# Get related patterns
related = workbench.pattern_library.get_related_patterns(
    "decomposition_pattern",
    depth=2
)
print(f"Related patterns: {related}")

# Match patterns to a task
patterns = workbench.pattern_library.match_patterns_to_task(
    "Solve this complex multi-step problem",
    ["Problem Solving", "Logic"]
)
print(f"Matched {len(patterns)} patterns")
```

### Agent Performance Tracking

```python
# View agent performance
for agent_id, agent in workbench.agent_zero.agents.items():
    print(f"\n{agent_id}:")
    print(f"  Role: {agent.role.value}")
    print(f"  Metrics: {agent.performance_metrics}")
```

### Task Statistics

```python
# Get task statistics
stats = workbench.get_statistics()

# Tasks by tag
print("\nTasks by tag:")
for tag, count in sorted(stats['tasks']['by_tag'].items(), 
                         key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {tag}: {count}")

# Patterns by quality
print("\nPatterns by quality:")
for quality, count in stats['patterns']['by_quality'].items():
    print(f"  {quality}: {count}")
```

## Tips and Best Practices

1. **Start with recommendations**: Always use `get_task_recommendations()` before solving a task
2. **Use collaborative mode**: For complex tasks, collaborative mode often performs best
3. **Track performance**: Monitor pattern and strategy success rates to identify what works
4. **Evolve patterns**: Add new examples to patterns as you discover new applications
5. **Compose strategies**: Hybrid strategies can combine the strengths of multiple approaches

## Example Complete Workflow

```python
from opencog import OpenCogWorkbench

# 1. Initialize
workbench = OpenCogWorkbench(tasks_dir="tasks")

# 2. Select a task
task_id = "deductive-logic-puzzles"

# 3. Get recommendations
recs = workbench.get_task_recommendations(task_id)
print(f"\nTop pattern: {recs['recommended_patterns'][0]['name']}")
print(f"Top strategy: {recs['recommended_strategies'][0]['name']}")

# 4. Solve the task
result = workbench.solve_task(task_id, orchestration_mode="collaborative")

# 5. Review results
print(f"\nSuccess: {result['success']}")
print(f"Patterns: {result['patterns_used']}")
print(f"Strategy: {result.get('strategy')}")

# 6. Check statistics
stats = workbench.get_statistics()
print(f"\nTotal executions: {stats['performance']['executions']}")
print(f"Avg success rate: {stats['performance']['avg_success_rate']:.2f}")

# 7. Save state for next time
workbench.save_state("my_workbench_state")
```

## Next Steps

- Read [OPENCOG_README.md](OPENCOG_README.md) for detailed documentation
- Run `python3 opencog_demo.py` to see all features in action
- Explore the pattern language library in `opencog/patterns/`
- Create custom patterns and strategies for your specific use cases
- Integrate with your LLM workflows

## Support

For questions or issues, please refer to the documentation or open an issue on GitHub.
