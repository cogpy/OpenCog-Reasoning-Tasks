![image](https://github.com/user-attachments/assets/2527a05e-afbc-4145-9daa-96f0229600f6)

[![Netlify Status](https://api.netlify.com/api/v1/badges/03dad91c-2330-4213-8cfc-db14c113da16/deploy-status)](https://app.netlify.com/sites/openreasoningtasks/deploys)

Welcome to the **LLM Reasoning Task Collection** repository! This project is an open collaboration to create a comprehensive master list of reasoning tasks that can teach, elicit, or show reasoning samples to large language models (LLMs) for training purposes.

## Contents

- [Open Reasoning Tasks: LLM Reasoning Tasks Collection](#open-reasoning-tasks-llm-reasoning-tasks-collection)
  - [Contents](#contents)
  - [Introduction](#introduction)
  - [Contributing](#contributing)
  - [License](#license)
  - [Citation](#citation)

## Introduction

The goal of this repository is to gather a diverse set of reasoning tasks designed to improve the reasoning capabilities of LLMs. Contributors are encouraged to submit tasks, provide examples, and optionally include diagrams or workflows to illustrate how the tasks function.

## Resources

### [Master Reasoning Tasks List](https://github.com/NousResearch/Open-Reasoning-Tasks/blob/main/tasks.md)
You can access the [main tasks list table by clicking here (or open tasks.md file in the top level directory)](https://github.com/NousResearch/Open-Reasoning-Tasks/blob/main/tasks.md)
<img width="871" alt="image" src="https://github.com/user-attachments/assets/4a644bb7-1e3f-4e37-b302-0ab14ccd11a3">

### [Web Based Directory](https://reasoning.nousresearch.com)
You can access the full [table of reasoning tasks from our quarto based website by clicking here.](https://reasoning.nousresearch.com)
<img width="973" alt="image" src="https://github.com/user-attachments/assets/0399415b-b475-4ad8-ae5a-629f9140de15">

### AI Reasoning Papers Master List
Coming Soon

### AI Reasoning Formats & Systems
Coming Soon

### AI Reasoning Training and Evaluation Datasets
Coming Soon

## OpenCog Multi-Agent Orchestration Workbench

This repository now includes the **OpenCog Multi-Agent Orchestration Workbench**, a sophisticated framework for autonomous multi-agent orchestration of LLM reasoning tasks.

### Key Features

- **Agent-Zero Master Builder**: Coordinates cognitive architectures to develop sophisticated strategies for all reasoning challenges
- **Pattern Language Library**: A "living library" inspired by Christopher Alexander's "A Pattern Language" but specifically designed for AGI cognitive architectures
- **Multi-Agent Orchestration**: Sophisticated coordination of specialized agents with different roles (analyzer, strategist, executor, validator, learner)
- **Strategy Development**: Adaptive strategy creation and refinement for reasoning challenges

### Quick Start

```python
from opencog import OpenCogWorkbench

# Initialize the workbench with reasoning tasks
workbench = OpenCogWorkbench(tasks_dir="tasks")

# Solve a task autonomously with Agent-Zero
result = workbench.solve_task("towers-of-hanoi", orchestration_mode="autonomous")
print(result)

# Get recommendations for a task
recommendations = workbench.get_task_recommendations("deductive-logic-puzzles")
print(recommendations)
```

### Run the Demo

```bash
python opencog_demo.py
```

### Documentation

See [OPENCOG_README.md](OPENCOG_README.md) for complete documentation of the OpenCog Multi-Agent Orchestration Workbench.

### Core Components

1. **Agent-Zero** - Master builder that analyzes tasks, builds cognitive architectures, and coordinates agents
2. **Pattern Library** - 10 foundational cognitive patterns for reasoning and problem-solving
3. **Multi-Agent System** - Orchestration framework with message passing and task distribution
4. **Strategy Repository** - 7 core strategies that can be composed and adapted

## Contributing

We welcome contributions from everyone! To contribute, please see our [Contribution Guide](CONTRIBUTING.md).

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

## Citation

```bibtex
@misc{nousresearch2024,
  title = {Open Reasoning Tasks: LLM Reasoning Tasks Collection},
  author = {Nous Research},
  url = {https://github.com/NousResearch/Open-Reasoning-Tasks},
  year = {2024},
}
```
