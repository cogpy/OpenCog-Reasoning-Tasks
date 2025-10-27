# OpenCog Multi-Agent Orchestration Workbench

## Overview

The OpenCog Multi-Agent Orchestration Workbench is a sophisticated framework for autonomous multi-agent orchestration of LLM reasoning tasks. It implements:

- **Agent-Zero**: A master builder that coordinates cognitive architectures
- **Pattern Language Library**: A living library inspired by Christopher Alexander's "A Pattern Language" but specifically designed for AGI cognitive architectures
- **Multi-Agent Orchestration**: Sophisticated coordination of multiple specialized agents
- **Strategy Development**: Adaptive strategy creation and refinement for reasoning challenges

## Architecture

### Components

1. **Agent-Zero (Master Builder)**
   - Analyzes reasoning tasks and requirements
   - Builds cognitive architectures tailored to specific tasks
   - Coordinates specialized agents with different roles
   - Learns from execution outcomes to improve performance

2. **Pattern Language Library**
   - Foundational cognitive patterns for reasoning and problem-solving
   - Pattern composition and inheritance
   - Evolution based on usage and outcomes
   - Quality levels: Experimental → Proven → Mature → Foundational

3. **Multi-Agent Orchestration**
   - Agent coordination and task distribution
   - Message-based communication
   - Load balancing
   - Multiple orchestration strategies (collaborative, competitive, sequential)

4. **Strategy Repository**
   - Collection of proven problem-solving strategies
   - Strategy composition and adaptation
   - Performance tracking and learning
   - Hybrid strategy generation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/cogpy/OpenCog-Reasoning-Tasks.git
cd OpenCog-Reasoning-Tasks

# No additional dependencies required - uses Python standard library
```

### Basic Usage

```python
from opencog import OpenCogWorkbench

# Initialize the workbench
workbench = OpenCogWorkbench(tasks_dir="tasks")

# Get statistics
stats = workbench.get_statistics()
print(stats)

# Solve a task autonomously
result = workbench.solve_task("towers-of-hanoi", orchestration_mode="autonomous")
print(result)
```

### Running the Demo

```bash
python opencog_demo.py
```

## Core Concepts

### Agent-Zero: The Master Builder

Agent-Zero orchestrates the entire cognitive architecture:

1. **Analysis Phase**: Analyzes the task to understand requirements and complexity
2. **Architecture Building**: Constructs a cognitive architecture with appropriate patterns and agents
3. **Execution**: Coordinates agents to solve the task
4. **Validation**: Validates the solution quality
5. **Learning**: Updates patterns and strategies based on outcomes

### Pattern Language for AGI

Inspired by Christopher Alexander's architectural patterns, our pattern language provides reusable cognitive patterns:

**Pattern Structure:**
- **Name**: Descriptive name for the pattern
- **Context**: When/where this pattern applies
- **Problem**: The recurring problem this pattern solves
- **Forces**: Conflicting considerations that must be balanced
- **Solution**: The proven solution approach
- **Examples**: Concrete examples of pattern usage
- **Related**: Connections to other patterns

**Foundational Patterns:**
- Problem Decomposition
- Recursive Thinking
- Pattern Recognition and Matching
- Logical Inference
- Abstraction and Generalization
- Working Backward from Goal
- Metacognitive Monitoring
- Analogical Transfer
- Constraint Satisfaction
- Causal Reasoning

### Multi-Agent Orchestration Modes

1. **Autonomous Mode**: Agent-Zero fully controls the process
2. **Collaborative Mode**: Multiple agents work together with coordination
3. **Guided Mode**: Provides analysis and recommendations for user guidance

### Strategy Types

- **Deductive**: Reasoning from general to specific
- **Inductive**: Reasoning from specific to general
- **Abductive**: Inference to best explanation
- **Analogical**: Transfer from similar problems
- **Heuristic**: Rule-of-thumb approaches
- **Systematic**: Methodical, exhaustive approaches
- **Creative**: Novel, unconventional approaches
- **Hybrid**: Composition of multiple strategies

## API Reference

### OpenCogWorkbench

Main interface for the system.

```python
workbench = OpenCogWorkbench(tasks_dir=None, patterns_path=None)
```

**Methods:**
- `load_tasks(tasks_dir)`: Load reasoning tasks from directory
- `solve_task(task_id, orchestration_mode)`: Solve a task
- `get_task_recommendations(task_id)`: Get recommendations for a task
- `get_pattern_catalog()`: Get the pattern language catalog
- `get_statistics()`: Get workbench statistics
- `save_state(directory)`: Save workbench state

### AgentZero

The master builder orchestrator.

```python
agent_zero = AgentZero()
agent_zero.initialize_core_agents()
```

**Methods:**
- `analyze_task(task)`: Analyze a reasoning task
- `build_cognitive_architecture(task, analysis)`: Build architecture for task
- `orchestrate_task(task)`: Full orchestration of a task
- `register_agent(agent)`: Register a new agent

### PatternLanguageLibrary

Living library of cognitive patterns.

```python
library = PatternLanguageLibrary(library_path=None)
```

**Methods:**
- `add_pattern(pattern)`: Add a new pattern
- `get_pattern(pattern_id)`: Retrieve a pattern
- `match_patterns_to_task(description, tags)`: Find relevant patterns
- `record_pattern_use(pattern_id, success)`: Record pattern usage
- `evolve_pattern(pattern_id, new_example)`: Evolve pattern with new example
- `save_library(path)`: Save pattern library
- `load_library(path)`: Load pattern library

### Orchestrator

Multi-agent orchestration system.

```python
orchestrator = Orchestrator()
```

**Methods:**
- `create_session(session_id, agents)`: Create orchestration session
- `submit_task(session_id, task)`: Submit task to session
- `orchestrate_multi_agent_task(session_id, task, strategy)`: Orchestrate task
- `get_session_status(session_id)`: Get session status

### StrategyRepository

Repository of problem-solving strategies.

```python
repository = StrategyRepository()
```

**Methods:**
- `add_strategy(strategy)`: Add a strategy
- `get_strategy(strategy_id)`: Get a strategy
- `find_strategies_for_task(tags, patterns)`: Find suitable strategies
- `compose_hybrid_strategy(strategies, context)`: Create hybrid strategy
- `record_strategy_use(strategy_id, success)`: Record strategy usage

## Examples

### Example 1: Solving a Logic Puzzle

```python
from opencog import OpenCogWorkbench

workbench = OpenCogWorkbench(tasks_dir="tasks")

# Get recommendations first
recommendations = workbench.get_task_recommendations("deductive-logic-puzzles")
print("Recommended patterns:", recommendations['recommended_patterns'])
print("Recommended strategies:", recommendations['recommended_strategies'])

# Solve the task
result = workbench.solve_task(
    "deductive-logic-puzzles",
    orchestration_mode="collaborative"
)

print("Success:", result['success'])
print("Patterns used:", result['patterns_used'])
print("Strategy:", result['strategy'])
```

### Example 2: Creating a New Pattern

```python
from opencog.patterns.pattern_library import CognitivePattern, PatternCategory, PatternQuality

new_pattern = CognitivePattern(
    id="my_custom_pattern",
    name="My Custom Pattern",
    category=PatternCategory.PROBLEM_SOLVING,
    context="When facing a specific type of problem...",
    problem="The problem this pattern solves...",
    forces=["Force 1", "Force 2", "Force 3"],
    solution="The solution approach...",
    examples=[{"task": "Example task", "application": "How pattern applies"}],
    quality=PatternQuality.EXPERIMENTAL
)

workbench.pattern_library.add_pattern(new_pattern)
```

### Example 3: Multi-Agent Collaboration

```python
from opencog.agents.agent_zero import Task

# Create a complex task
task = Task(
    id="complex_reasoning",
    name="Complex Multi-Step Reasoning",
    description="A task requiring multiple reasoning steps",
    modality="Text only",
    tags=["Reasoning", "Multi-Step", "Logic"]
)

# Create orchestration session
session_id = "my_session"
agents = list(workbench.agent_zero.agents.keys())
workbench.orchestrator.create_session(session_id, agents)

# Orchestrate with collaborative strategy
task_dict = {
    "id": task.id,
    "name": task.name,
    "description": task.description,
    "required_capabilities": ["reasoning", "problem_solving"]
}

result = workbench.orchestrator.orchestrate_multi_agent_task(
    session_id,
    task_dict,
    strategy="collaborative"
)

print(result)
```

## Pattern Language Catalog

The system includes these foundational cognitive patterns:

1. **Problem Decomposition** - Break complex problems into manageable parts
2. **Recursive Thinking** - Apply problem-solving recursively
3. **Pattern Recognition** - Identify and match patterns
4. **Logical Inference** - Apply logical rules systematically
5. **Abstraction** - Extract general principles from specifics
6. **Working Backward** - Start from goal and work backward
7. **Metacognitive Monitoring** - Monitor and adjust approach
8. **Analogical Transfer** - Apply solutions from similar problems
9. **Constraint Satisfaction** - Satisfy multiple constraints
10. **Causal Reasoning** - Understand cause-effect relationships

Each pattern includes detailed context, problem description, forces, solution, examples, and relationships to other patterns.

## Contributing

To add new patterns, strategies, or agents:

1. Create the pattern/strategy/agent following the existing structure
2. Add it to the appropriate repository
3. Test it with example tasks
4. Document usage examples

## Future Enhancements

- Integration with actual LLMs for execution
- Distributed multi-agent systems across multiple nodes
- Advanced pattern mining from task solutions
- Automated strategy synthesis
- Visual pattern language browser
- Real-time collaboration between human and AI agents

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Citation

```bibtex
@software{opencog_workbench2024,
  title = {OpenCog Multi-Agent Orchestration Workbench},
  author = {OpenCog Reasoning Tasks Contributors},
  url = {https://github.com/cogpy/OpenCog-Reasoning-Tasks},
  year = {2024},
  note = {A pattern language and multi-agent system for AGI cognitive architectures}
}
```
