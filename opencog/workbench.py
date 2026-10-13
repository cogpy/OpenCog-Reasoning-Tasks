"""
OpenCog Reasoning Task Integration

This module integrates the OpenCog multi-agent orchestration system with
the existing reasoning tasks, providing a complete workbench for LLM reasoning.
"""

import os
import json
import logging
import hashlib
from uuid import uuid4
from copy import deepcopy
from dataclasses import replace
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import OpenCog components
from .agents.agent_zero import AgentZero, Agent, Task, AgentRole
from .patterns.pattern_library import PatternLanguageLibrary, CognitivePattern
from .orchestration.multi_agent import Orchestrator
from .strategies.strategy_system import StrategyRepository, StrategyExecutor
from .catalog import parse_task_file, load_catalog, check_json_consistency
from .curriculum import CURRICULUM, CurriculumScheduler
from .reasoning import ReasoningBackend


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
    
    def __init__(self, tasks_dir: str = None, patterns_path: str = None, backend=None):
        """
        Initialize the OpenCog workbench
        
        Args:
            tasks_dir: Directory containing reasoning tasks (markdown files)
            patterns_path: Path to save/load pattern library
            backend: Optional executor/evaluator implementing the ReasoningBackend interface
        """
        # Initialize core components
        self.backend = backend if backend is not None else ReasoningBackend()
        self.agent_zero = AgentZero(backend=self.backend)
        self.pattern_library = PatternLanguageLibrary(library_path=patterns_path)
        self.orchestrator = Orchestrator()
        self.strategy_repository = StrategyRepository()
        self.strategy_executor = StrategyExecutor(
            pattern_library=self.pattern_library, backend=self.backend
        )
        self.scheduler = CurriculumScheduler(
            available_capabilities=self.backend.available_capabilities,
            supported_tasks=self.backend.supported_tasks
        )
        self.catalog_report = {}
        
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
        definitions, self.catalog_report = load_catalog(Path(tasks_dir))
        for definition in definitions:
            task = self._task_from_definition(definition)
            self.tasks[task.id] = task
        json_directory = Path(tasks_dir).parent / "tasks-json"
        if json_directory.is_dir():
            self.catalog_report["json_consistency"] = check_json_consistency(
                Path(tasks_dir), json_directory
            )
        logger.info("Loaded %s reasoning tasks", len(definitions))
        
    def _parse_task_file(self, file_path: Path) -> Optional[Task]:
        """Parse a task markdown file into a Task object"""
        return self._task_from_definition(parse_task_file(file_path))

    def _task_from_definition(self, definition: Dict[str, Any]) -> Task:
        metadata = deepcopy(CURRICULUM.get(definition["id"], {}))
        return Task(
            id=definition["id"],
            name=definition["name"],
            description=definition["description"],
            modality=definition["modality"],
            tags=definition["tags"],
            examples=definition["examples"],
            required_capabilities=metadata.get("required_capabilities", []),
            curriculum=metadata,
            source=str(definition.get("source", "")),
            raw_content=definition.get("raw_content", ""),
            catalog_metadata=definition.get("metadata", {}),
            catalog_warnings=definition.get("warnings", []),
            audit_issues=definition.get("audit_issues", [])
        )
        
    def solve_task(
        self, task_id: str, orchestration_mode: str = "autonomous",
        instance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        if orchestration_mode not in {"autonomous", "collaborative", "guided"}:
            raise ValueError(f"Unknown orchestration mode: {orchestration_mode}")
        if instance is not None:
            try:
                self._instance_id(instance)
            except (TypeError, ValueError) as error:
                raise ValueError("instance must contain finite JSON-serializable data") from error
            
        task = replace(self.tasks[task_id], instance=deepcopy(instance))
        logger.info(f"Starting to solve task: {task.name}")
        
        if orchestration_mode == "autonomous":
            result = self._solve_autonomous(task)
        elif orchestration_mode == "collaborative":
            result = self._solve_collaborative(task)
        elif orchestration_mode == "guided":
            return self._solve_guided(task)
        else:
            raise ValueError(f"Unknown orchestration mode: {orchestration_mode}")
        validation = result.get("validation", {})
        if validation.get("evaluated") and task_id in CURRICULUM:
            self.scheduler.record_attempt(
                task_id, self._instance_id(instance), validation, split="practice"
            )
        return result
            
    def _solve_autonomous(self, task: Task) -> Dict[str, Any]:
        """Solve task autonomously using Agent-Zero"""
        logger.info(f"Solving task '{task.name}' autonomously with Agent-Zero")
        
        # Agent-Zero orchestrates the entire solution
        result = self.agent_zero.orchestrate_task(task)
        
        return {
            "mode": "autonomous",
            "task": task.name,
            "orchestration_result": result,
            "status": result["results"]["status"],
            "answer": result["results"].get("answer"),
            "validation": result["validation"],
            "evidence": result["results"].get("evidence", []),
            "confidence": result["results"].get("confidence"),
            "resource_usage": result["results"].get("resource_usage", {}),
            "errors": result["results"].get("errors", []),
            "patterns_used": result["results"].get("patterns_used", []),
            "success": result["validation"]["validation_status"] == "passed"
        }
        
    def _solve_collaborative(self, task: Task) -> Dict[str, Any]:
        """Solve task using multi-agent collaboration"""
        logger.info(f"Solving task '{task.name}' with multi-agent collaboration")
        
        # Create orchestration session
        session_id = f"task_{task.id}_{uuid4().hex}"
        agent_ids = list(self.agent_zero.agents.keys())
        self.orchestrator.create_session(session_id, agent_ids)
        
        stages = [
            ("analyzer_01", "analysis", lambda context: self.agent_zero.analyze_task(task)),
            ("strategist_01", "architecture", lambda context:
             self.agent_zero.build_cognitive_architecture(task, context["analysis"])),
            ("executor_01", "execution", lambda context:
             self.agent_zero.execute_with_architecture(task, context["architecture"])),
            ("validator_01", "validation", lambda context:
             self.agent_zero.validate_results(task, context["execution"])),
            ("learner_01", "learning", lambda context:
             self.agent_zero.learn_from_execution(task, context["execution"], context["validation"]))
        ]
        try:
            session_task = task.to_dict()
            session_task["id"] = session_id
            session_task["family_id"] = task.id
            pipeline = self.orchestrator.run_pipeline(session_id, session_task, stages)
        finally:
            self.orchestrator.close_session(session_id)
        context = pipeline["context"]
        execution = context["execution"]
        validation = context["validation"]
        return {
            "mode": "collaborative", "task": task.name, "session_id": session_id,
            "execution": execution, "execution_trace": pipeline["execution_trace"],
            "status": execution["status"], "answer": execution.get("answer"),
            "validation": validation, "success": validation.get("success", False),
            "patterns_used": execution.get("patterns_used", []),
            "evidence": execution.get("evidence", []),
            "confidence": execution.get("confidence"),
            "resource_usage": execution.get("resource_usage", {}),
            "errors": execution.get("errors", [])
        }
        
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
            "status": "guided",
            "success": False,
            "evaluated": False,
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
            "curriculum": task.curriculum,
            "readiness": self.scheduler.readiness(task_id) if task_id in CURRICULUM else {
                "ready": False, "reason": "Task has no reviewed curriculum metadata"
            },
            "mastery": self.scheduler.mastery(task_id) if task_id in CURRICULUM else {},
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
                "by_tag": self._count_by_tag(),
                "catalog_report": self.catalog_report
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
                "executions": len(self.agent_zero.performance_history) + sum(
                    bool(execution.get("validation", {}).get("evaluated"))
                    for execution in self.strategy_executor.execution_history
                ),
                "avg_success_rate": self._calculate_avg_success_rate()
            }
        }

    @staticmethod
    def _instance_id(instance: Dict[str, Any]) -> str:
        encoded = json.dumps(instance, sort_keys=True, allow_nan=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get_curriculum(self) -> List[Dict[str, Any]]:
        """Return ranked metadata, backend readiness, and measured mastery."""
        return [
            dict(task_id=task_id, **deepcopy(metadata),
                 readiness=self.scheduler.readiness(task_id),
                 mastery=self.scheduler.mastery(task_id))
            for task_id, metadata in sorted(
                CURRICULUM.items(), key=lambda entry: (
                    entry[1]["rank"], entry[1].get("order", 0), entry[0]
                )
            ) if task_id in self.tasks
        ]

    def recommend_next_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("limit must be a nonnegative integer")
        return [
            item for item in self.scheduler.recommend(limit=len(CURRICULUM))
            if item["task_id"] in self.tasks
        ][:limit]

    def evaluate_instance(
        self, task_id: str, instance: Dict[str, Any], answer: Any, *,
        split: str = "practice", transfer: bool = False
    ) -> Dict[str, Any]:
        """Independently evaluate an answer; caller-declared splits are not certified benchmarks."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        instance_id = self._instance_id(instance)
        validation = self.backend.validate(task_id, instance, answer)
        if validation.get("evaluated") and task_id in CURRICULUM:
            self.scheduler.record_attempt(
                task_id, instance_id, validation,
                split=split, transfer=transfer
            )
        return validation
        
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
            
        self.scheduler.save(Path(directory) / "mastery.json")
        with open(Path(directory) / "execution_history.json", "w", encoding="utf-8") as f:
            json.dump({
                "agent_zero": self.agent_zero.performance_history,
                "strategy_executor": self.strategy_executor.execution_history
            }, f, indent=2)
        logger.info(f"Saved workbench state to {directory}")

    def load_state(self, directory: str):
        """Restore saved evidence without enabling unavailable reasoning backends."""
        directory = Path(directory)
        self.scheduler.load(directory / "mastery.json")
        self.pattern_library.load_library(str(directory / "patterns.json"))
        from .strategies.strategy_system import Strategy, StrategyType
        with open(directory / "strategies.json", encoding="utf-8") as f:
            strategies = json.load(f)
        restored = {}
        for strategy_id, data in strategies.items():
            data["strategy_type"] = StrategyType(data["strategy_type"])
            restored[strategy_id] = Strategy(**data)
        self.strategy_repository.strategies = restored
        with open(directory / "execution_history.json", encoding="utf-8") as f:
            history = json.load(f)
        self.agent_zero.performance_history = history["agent_zero"]
        self.strategy_executor.execution_history = history["strategy_executor"]
        
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
        records = self.agent_zero.performance_history + [
            execution for execution in self.strategy_executor.execution_history
            if execution.get("validation", {}).get("evaluated")
        ]
        if not records:
            return 0.0
        successes = sum(bool(record["success"]) for record in records)
        return successes / len(records)
