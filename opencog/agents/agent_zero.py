"""
Agent-Zero: Master Builder for Cognitive Architectures

This module implements the Agent-Zero orchestrator, which serves as the "master builder"
for constructing and managing cognitive architectures to solve reasoning challenges.
Agent-Zero coordinates multiple specialized agents, applies cognitive patterns, and
evolves strategies based on task requirements.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Defines the roles agents can take in the cognitive architecture"""
    ANALYZER = "analyzer"  # Analyzes tasks and requirements
    STRATEGIST = "strategist"  # Develops problem-solving strategies
    EXECUTOR = "executor"  # Executes reasoning tasks
    VALIDATOR = "validator"  # Validates solutions
    LEARNER = "learner"  # Learns from results and updates patterns


@dataclass
class Agent:
    """Represents a specialized agent in the cognitive architecture"""
    id: str
    role: AgentRole
    capabilities: List[str]
    state: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "id": self.id,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "state": self.state,
            "performance_metrics": self.performance_metrics
        }


@dataclass
class Task:
    """Represents a reasoning task"""
    id: str
    name: str
    description: str
    modality: str
    tags: List[str]
    examples: List[Dict[str, Any]] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)


class AgentZero:
    """
    Agent-Zero: The Master Builder
    
    Agent-Zero orchestrates cognitive architectures by:
    1. Analyzing incoming reasoning tasks
    2. Selecting and coordinating appropriate cognitive patterns
    3. Deploying specialized agents with specific roles
    4. Managing inter-agent communication and collaboration
    5. Learning from outcomes to improve future performance
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.pattern_library = None  # Will be set by pattern library
        self.strategy_repository = None  # Will be set by strategy system
        self.performance_history: List[Dict[str, Any]] = []
        
    def initialize_core_agents(self):
        """Initialize the core set of cognitive agents"""
        core_agents = [
            Agent(
                id="analyzer_01",
                role=AgentRole.ANALYZER,
                capabilities=["task_decomposition", "requirement_analysis", "pattern_matching"]
            ),
            Agent(
                id="strategist_01",
                role=AgentRole.STRATEGIST,
                capabilities=["strategy_design", "cognitive_pattern_selection", "optimization"]
            ),
            Agent(
                id="executor_01",
                role=AgentRole.EXECUTOR,
                capabilities=["reasoning", "problem_solving", "computation"]
            ),
            Agent(
                id="validator_01",
                role=AgentRole.VALIDATOR,
                capabilities=["solution_validation", "correctness_checking", "quality_assessment"]
            ),
            Agent(
                id="learner_01",
                role=AgentRole.LEARNER,
                capabilities=["pattern_learning", "performance_analysis", "adaptation"]
            )
        ]
        
        for agent in core_agents:
            self.register_agent(agent)
            
        logger.info(f"Initialized {len(core_agents)} core agents")
        
    def register_agent(self, agent: Agent):
        """Register a new agent in the system"""
        self.agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.id} with role: {agent.role.value}")
        
    def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        Analyze a reasoning task to determine required cognitive patterns and agents
        
        Args:
            task: The reasoning task to analyze
            
        Returns:
            Analysis results including required patterns and agent allocation
        """
        analyzer = self._get_agent_by_role(AgentRole.ANALYZER)
        
        # Determine complexity and requirements
        analysis = {
            "task_id": task.id,
            "task_name": task.name,
            "complexity_factors": {
                "tag_count": len(task.tags),
                "example_count": len(task.examples),
                "modality": task.modality
            },
            "required_patterns": self._identify_required_patterns(task),
            "suggested_agents": self._suggest_agent_allocation(task),
            "estimated_difficulty": self._estimate_difficulty(task)
        }
        
        logger.info(f"Task analysis complete for: {task.name}")
        return analysis
        
    def build_cognitive_architecture(self, task: Task, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a cognitive architecture tailored for the specific task
        
        Args:
            task: The reasoning task
            analysis: Analysis results from analyze_task
            
        Returns:
            Architecture specification
        """
        strategist = self._get_agent_by_role(AgentRole.STRATEGIST)
        
        architecture = {
            "task_id": task.id,
            "agents": [],
            "patterns": analysis["required_patterns"],
            "workflow": self._design_workflow(task, analysis),
            "communication_channels": self._setup_communication(analysis["suggested_agents"]),
            "success_criteria": self._define_success_criteria(task)
        }
        
        # Allocate agents
        for agent_spec in analysis["suggested_agents"]:
            agent = self._allocate_agent(agent_spec)
            architecture["agents"].append(agent.to_dict())
            
        logger.info(f"Cognitive architecture built for task: {task.name}")
        return architecture
        
    def execute_with_architecture(self, task: Task, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using the constructed cognitive architecture
        
        Args:
            task: The reasoning task
            architecture: The cognitive architecture specification
            
        Returns:
            Execution results
        """
        executor = self._get_agent_by_role(AgentRole.EXECUTOR)
        
        results = {
            "task_id": task.id,
            "status": "in_progress",
            "steps": [],
            "solutions": []
        }
        
        # Execute workflow
        for step in architecture["workflow"]:
            step_result = self._execute_step(step, task, architecture)
            results["steps"].append(step_result)
            
        results["status"] = "completed"
        logger.info(f"Task execution completed: {task.name}")
        return results
        
    def validate_results(self, task: Task, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate execution results
        
        Args:
            task: The original task
            results: Execution results
            
        Returns:
            Validation report
        """
        validator = self._get_agent_by_role(AgentRole.VALIDATOR)
        
        validation = {
            "task_id": task.id,
            "validation_status": "passed",
            "quality_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        # Validate against success criteria
        # This would include checking solution correctness, completeness, etc.
        validation["quality_score"] = self._calculate_quality_score(results)
        
        logger.info(f"Validation completed for task: {task.name}")
        return validation
        
    def learn_from_execution(self, task: Task, results: Dict[str, Any], validation: Dict[str, Any]):
        """
        Learn from task execution to improve future performance
        
        Args:
            task: The executed task
            results: Execution results
            validation: Validation results
        """
        learner = self._get_agent_by_role(AgentRole.LEARNER)
        
        # Record performance
        performance_record = {
            "task_id": task.id,
            "task_name": task.name,
            "quality_score": validation["quality_score"],
            "execution_time": len(results["steps"]),
            "patterns_used": results.get("patterns_used", [])
        }
        
        self.performance_history.append(performance_record)
        
        # Update agent performance metrics
        for agent_id in [a["id"] for a in results.get("agents_involved", [])]:
            if agent_id in self.agents:
                self._update_agent_metrics(agent_id, performance_record)
                
        logger.info(f"Learning completed for task: {task.name}")
        
    def orchestrate_task(self, task: Task) -> Dict[str, Any]:
        """
        Main orchestration method - analyzes, builds architecture, executes, validates, and learns
        
        Args:
            task: The reasoning task to orchestrate
            
        Returns:
            Complete orchestration results
        """
        logger.info(f"Starting orchestration for task: {task.name}")
        
        # Step 1: Analyze the task
        analysis = self.analyze_task(task)
        
        # Step 2: Build cognitive architecture
        architecture = self.build_cognitive_architecture(task, analysis)
        
        # Step 3: Execute with the architecture
        results = self.execute_with_architecture(task, architecture)
        
        # Step 4: Validate results
        validation = self.validate_results(task, results)
        
        # Step 5: Learn from execution
        self.learn_from_execution(task, results, validation)
        
        orchestration_result = {
            "task": task.name,
            "analysis": analysis,
            "architecture": architecture,
            "results": results,
            "validation": validation
        }
        
        logger.info(f"Orchestration completed for task: {task.name}")
        return orchestration_result
        
    # Helper methods
    
    def _get_agent_by_role(self, role: AgentRole) -> Optional[Agent]:
        """Get an agent by role"""
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None
        
    def _identify_required_patterns(self, task: Task) -> List[str]:
        """Identify cognitive patterns required for the task"""
        # This would use the pattern library to match task requirements to patterns
        patterns = []
        
        # Map task tags to patterns
        tag_to_pattern = {
            "Problem Solving": "decomposition_pattern",
            "Recursion": "recursive_thinking_pattern",
            "Pattern Recognition": "pattern_matching_pattern",
            "Logic": "logical_reasoning_pattern",
            "Mathematical": "mathematical_reasoning_pattern"
        }
        
        for tag in task.tags:
            if tag in tag_to_pattern:
                patterns.append(tag_to_pattern[tag])
                
        return patterns if patterns else ["general_reasoning_pattern"]
        
    def _suggest_agent_allocation(self, task: Task) -> List[Dict[str, Any]]:
        """Suggest agent allocation for the task"""
        # All tasks need these core agents
        return [
            {"role": AgentRole.ANALYZER.value, "count": 1},
            {"role": AgentRole.EXECUTOR.value, "count": 1},
            {"role": AgentRole.VALIDATOR.value, "count": 1}
        ]
        
    def _estimate_difficulty(self, task: Task) -> str:
        """Estimate task difficulty"""
        complexity = len(task.tags) + len(task.examples) * 0.5
        if complexity < 5:
            return "easy"
        elif complexity < 10:
            return "medium"
        else:
            return "hard"
            
    def _design_workflow(self, task: Task, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Design the execution workflow"""
        workflow = [
            {"step": 1, "action": "decompose_task", "agent_role": "analyzer"},
            {"step": 2, "action": "apply_patterns", "agent_role": "strategist"},
            {"step": 3, "action": "execute_reasoning", "agent_role": "executor"},
            {"step": 4, "action": "validate_solution", "agent_role": "validator"}
        ]
        return workflow
        
    def _setup_communication(self, agent_specs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Setup communication channels between agents"""
        channels = {
            "analyzer_to_strategist": ["task_analysis", "requirements"],
            "strategist_to_executor": ["strategy", "patterns"],
            "executor_to_validator": ["solution", "reasoning_trace"],
            "validator_to_learner": ["validation_results", "quality_metrics"]
        }
        return channels
        
    def _define_success_criteria(self, task: Task) -> Dict[str, Any]:
        """Define success criteria for the task"""
        return {
            "correctness": "solution matches expected output",
            "completeness": "all task requirements addressed",
            "quality": "solution quality score > 0.7"
        }
        
    def _allocate_agent(self, agent_spec: Dict[str, Any]) -> Agent:
        """Allocate an agent based on specification"""
        role = AgentRole(agent_spec["role"])
        return self._get_agent_by_role(role)
        
    def _execute_step(self, step: Dict[str, Any], task: Task, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        return {
            "step": step["step"],
            "action": step["action"],
            "status": "completed",
            "output": f"Step {step['step']} completed"
        }
        
    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculate quality score for results"""
        # Simplified scoring - in real implementation would be more sophisticated
        if results["status"] == "completed":
            return 0.85
        return 0.0
        
    def _update_agent_metrics(self, agent_id: str, performance: Dict[str, Any]):
        """Update performance metrics for an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if "task_count" not in agent.performance_metrics:
                agent.performance_metrics["task_count"] = 0
                agent.performance_metrics["avg_quality"] = 0.0
                
            agent.performance_metrics["task_count"] += 1
            current_avg = agent.performance_metrics["avg_quality"]
            count = agent.performance_metrics["task_count"]
            agent.performance_metrics["avg_quality"] = (
                (current_avg * (count - 1) + performance["quality_score"]) / count
            )
