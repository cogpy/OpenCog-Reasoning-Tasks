"""
OpenCog Reasoning Task Integration

This module integrates the OpenCog multi-agent orchestration system with
the existing reasoning tasks, providing a complete workbench for LLM reasoning.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import OpenCog components
from .agents.agent_zero import AgentZero, Agent, Task, AgentRole
from .patterns.pattern_library import PatternLanguageLibrary, CognitivePattern
from .orchestration.multi_agent import Orchestrator
from .strategies.strategy_system import StrategyRepository, StrategyExecutor


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OpenCogWorkbench:
    """
    OpenCog Autonomous Multi-Agent Orchestration Workbench
    
    This is the main interface for the OpenCog system. It integrates:
    - Agent-Zero master builder
    - Pattern language library
    - Multi-agent orchestration
    - Strategy development and execution
    - Reasoning task management
    """
    
    def __init__(self, tasks_dir: str = None, patterns_path: str = None):
        """
        Initialize the OpenCog workbench
        
        Args:
            tasks_dir: Directory containing reasoning tasks (markdown files)
            patterns_path: Path to save/load pattern library
        """
        # Initialize core components
        self.agent_zero = AgentZero()
        self.pattern_library = PatternLanguageLibrary(library_path=patterns_path)
        self.orchestrator = Orchestrator()
        self.strategy_repository = StrategyRepository()
        self.strategy_executor = StrategyExecutor(pattern_library=self.pattern_library)
        
        # Connect components
        self.agent_zero.pattern_library = self.pattern_library
        self.agent_zero.strategy_repository = self.strategy_repository
        
        # Initialize Agent-Zero's core agents
        self.agent_zero.initialize_core_agents()
        
        # Register agents with orchestrator
        for agent_id, agent in self.agent_zero.agents.items():
            self.orchestrator.coordinator.register_agent(agent_id, agent.capabilities)
            
        # Load reasoning tasks if directory provided
        self.tasks: Dict[str, Task] = {}
        if tasks_dir:
            self.load_tasks(tasks_dir)
            
        logger.info("OpenCog Workbench initialized successfully")
        
    def load_tasks(self, tasks_dir: str):
        """
        Load reasoning tasks from directory
        
        Args:
            tasks_dir: Directory containing task markdown files
        """
        tasks_path = Path(tasks_dir)
        if not tasks_path.exists():
            logger.warning(f"Tasks directory not found: {tasks_dir}")
            return
            
        loaded_count = 0
        for task_file in tasks_path.glob("*.md"):
            try:
                task = self._parse_task_file(task_file)
                if task:
                    self.tasks[task.id] = task
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Error loading task {task_file.name}: {e}")
                
        logger.info(f"Loaded {loaded_count} reasoning tasks")
        
    def _parse_task_file(self, file_path: Path) -> Optional[Task]:
        """Parse a task markdown file into a Task object"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Simple parsing - extract key information
        lines = content.split('\n')
        
        name = ""
        description = ""
        modality = ""
        tags = []
        
        for i, line in enumerate(lines):
            if line.startswith('# ') and not name:
                name = line[2:].strip()
            elif line.startswith('## Description:'):
                if i + 1 < len(lines):
                    description = lines[i + 1].strip()
            elif line.startswith('## Modality:'):
                if i + 1 < len(lines):
                    modality = lines[i + 1].strip()
            elif line.startswith('## Tags:'):
                # Collect tags
                j = i + 1
                while j < len(lines) and lines[j].startswith('- '):
                    tags.append(lines[j][2:].strip())
                    j += 1
                    
        if not name:
            return None
            
        task_id = file_path.stem
        
        return Task(
            id=task_id,
            name=name,
            description=description,
            modality=modality,
            tags=tags
        )
        
    def solve_task(self, task_id: str, orchestration_mode: str = "autonomous") -> Dict[str, Any]:
        """
        Solve a reasoning task using the OpenCog system
        
        Args:
            task_id: ID of the task to solve
            orchestration_mode: How to orchestrate the solution
                - "autonomous": Agent-Zero fully autonomous
                - "collaborative": Multi-agent collaboration
                - "guided": User-guided execution
                
        Returns:
            Solution and execution details
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        task = self.tasks[task_id]
        logger.info(f"Starting to solve task: {task.name}")
        
        if orchestration_mode == "autonomous":
            return self._solve_autonomous(task)
        elif orchestration_mode == "collaborative":
            return self._solve_collaborative(task)
        elif orchestration_mode == "guided":
            return self._solve_guided(task)
        else:
            raise ValueError(f"Unknown orchestration mode: {orchestration_mode}")
            
    def _solve_autonomous(self, task: Task) -> Dict[str, Any]:
        """Solve task autonomously using Agent-Zero"""
        logger.info(f"Solving task '{task.name}' autonomously with Agent-Zero")
        
        # Agent-Zero orchestrates the entire solution
        result = self.agent_zero.orchestrate_task(task)
        
        return {
            "mode": "autonomous",
            "task": task.name,
            "orchestration_result": result,
            "patterns_used": result["analysis"].get("required_patterns", []),
            "success": result["validation"]["validation_status"] == "passed"
        }
        
    def _solve_collaborative(self, task: Task) -> Dict[str, Any]:
        """Solve task using multi-agent collaboration"""
        logger.info(f"Solving task '{task.name}' with multi-agent collaboration")
        
        # Create orchestration session
        session_id = f"task_{task.id}_session"
        agent_ids = list(self.agent_zero.agents.keys())
        self.orchestrator.create_session(session_id, agent_ids)
        
        # Match patterns to task
        patterns = self.pattern_library.match_patterns_to_task(
            task.description,
            task.tags
        )
        
        # Find suitable strategies
        pattern_ids = [p.id for p in patterns[:3]]  # Top 3 patterns
        strategies = self.strategy_repository.find_strategies_for_task(
            task.tags,
            pattern_ids
        )
        
        # Orchestrate with selected strategy
        if strategies:
            strategy = strategies[0]
            logger.info(f"Using strategy: {strategy.name}")
            
            # Execute strategy
            execution = self.strategy_executor.execute_strategy(
                strategy,
                task.to_dict() if hasattr(task, 'to_dict') else {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description
                }
            )
            
            # Record results
            self.strategy_repository.record_strategy_use(strategy.id, execution["success"])
            for pattern in patterns[:3]:
                self.pattern_library.record_pattern_use(pattern.id, execution["success"])
                
            result = {
                "mode": "collaborative",
                "task": task.name,
                "session_id": session_id,
                "patterns_used": [p.name for p in patterns[:3]],
                "strategy": strategy.name,
                "execution": execution,
                "success": execution["success"]
            }
        else:
            result = {
                "mode": "collaborative",
                "task": task.name,
                "error": "No suitable strategies found"
            }
            
        return result
        
    def _solve_guided(self, task: Task) -> Dict[str, Any]:
        """Solve task with user guidance"""
        logger.info(f"Solving task '{task.name}' in guided mode")
        
        # Provide analysis and suggestions for user
        analysis = self.agent_zero.analyze_task(task)
        
        patterns = self.pattern_library.match_patterns_to_task(
            task.description,
            task.tags
        )
        
        strategies = self.strategy_repository.find_strategies_for_task(
            task.tags,
            [p.id for p in patterns]
        )
        
        return {
            "mode": "guided",
            "task": task.name,
            "analysis": analysis,
            "suggested_patterns": [p.to_dict() for p in patterns[:5]],
            "suggested_strategies": [s.to_dict() for s in strategies[:5]],
            "message": "Review suggestions and provide guidance for execution"
        }
        
    def get_task_recommendations(self, task_id: str) -> Dict[str, Any]:
        """
        Get recommendations for solving a task
        
        Args:
            task_id: Task to analyze
            
        Returns:
            Recommendations including patterns, strategies, and approaches
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        task = self.tasks[task_id]
        
        # Get pattern recommendations
        patterns = self.pattern_library.match_patterns_to_task(
            task.description,
            task.tags
        )
        
        # Get strategy recommendations
        strategies = self.strategy_repository.find_strategies_for_task(
            task.tags,
            [p.id for p in patterns]
        )
        
        # Get related tasks (tasks with similar tags)
        related_tasks = []
        for other_task in self.tasks.values():
            if other_task.id != task_id:
                common_tags = set(task.tags) & set(other_task.tags)
                if common_tags:
                    related_tasks.append({
                        "task": other_task.name,
                        "common_tags": list(common_tags)
                    })
                    
        return {
            "task": task.name,
            "recommended_patterns": [
                {
                    "name": p.name,
                    "description": p.problem,
                    "quality": p.quality.value
                }
                for p in patterns[:5]
            ],
            "recommended_strategies": [
                {
                    "name": s.name,
                    "type": s.strategy_type.value,
                    "success_rate": s.success_rate
                }
                for s in strategies[:5]
            ],
            "related_tasks": related_tasks[:10]
        }
        
    def get_pattern_catalog(self) -> Dict[str, Any]:
        """
        Get the complete pattern language catalog
        
        Returns:
            Catalog of all patterns organized by category
        """
        from .patterns.pattern_library import PatternCategory
        
        catalog = {
            "total_patterns": len(self.pattern_library.patterns),
            "categories": {}
        }
        
        for category in PatternCategory:
            patterns = self.pattern_library.find_patterns_by_category(category)
            catalog["categories"][category.value] = [
                {
                    "id": p.id,
                    "name": p.name,
                    "quality": p.quality.value,
                    "use_count": p.use_count,
                    "success_rate": p.success_rate
                }
                for p in patterns
            ]
            
        return catalog
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get workbench statistics"""
        return {
            "tasks": {
                "total": len(self.tasks),
                "by_tag": self._count_by_tag()
            },
            "agents": {
                "total": len(self.agent_zero.agents),
                "by_role": self._count_agents_by_role()
            },
            "patterns": {
                "total": len(self.pattern_library.patterns),
                "by_category": self._count_patterns_by_category(),
                "by_quality": self._count_patterns_by_quality()
            },
            "strategies": {
                "total": len(self.strategy_repository.strategies),
                "by_type": self._count_strategies_by_type()
            },
            "performance": {
                "executions": len(self.strategy_executor.execution_history),
                "avg_success_rate": self._calculate_avg_success_rate()
            }
        }
        
    def save_state(self, directory: str):
        """Save workbench state to directory"""
        os.makedirs(directory, exist_ok=True)
        
        # Save pattern library
        pattern_path = os.path.join(directory, "patterns.json")
        self.pattern_library.save_library(pattern_path)
        
        # Save strategies
        strategies_path = os.path.join(directory, "strategies.json")
        with open(strategies_path, 'w') as f:
            json.dump(
                {sid: s.to_dict() for sid, s in self.strategy_repository.strategies.items()},
                f,
                indent=2
            )
            
        logger.info(f"Saved workbench state to {directory}")
        
    # Helper methods
    
    def _count_by_tag(self) -> Dict[str, int]:
        """Count tasks by tag"""
        tag_counts = {}
        for task in self.tasks.values():
            for tag in task.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
        
    def _count_agents_by_role(self) -> Dict[str, int]:
        """Count agents by role"""
        role_counts = {}
        for agent in self.agent_zero.agents.values():
            role = agent.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
        return role_counts
        
    def _count_patterns_by_category(self) -> Dict[str, int]:
        """Count patterns by category"""
        from .patterns.pattern_library import PatternCategory
        
        category_counts = {}
        for category in PatternCategory:
            count = len(self.pattern_library.find_patterns_by_category(category))
            category_counts[category.value] = count
        return category_counts
        
    def _count_patterns_by_quality(self) -> Dict[str, int]:
        """Count patterns by quality"""
        from .patterns.pattern_library import PatternQuality
        
        quality_counts = {}
        for quality in PatternQuality:
            count = len(self.pattern_library.find_patterns_by_quality(quality))
            quality_counts[quality.value] = count
        return quality_counts
        
    def _count_strategies_by_type(self) -> Dict[str, int]:
        """Count strategies by type"""
        type_counts = {}
        for strategy in self.strategy_repository.strategies.values():
            stype = strategy.strategy_type.value
            type_counts[stype] = type_counts.get(stype, 0) + 1
        return type_counts
        
    def _calculate_avg_success_rate(self) -> float:
        """Calculate average success rate across all executions"""
        if not self.strategy_executor.execution_history:
            return 0.0
        successes = sum(1 for e in self.strategy_executor.execution_history if e["success"])
        return successes / len(self.strategy_executor.execution_history)
