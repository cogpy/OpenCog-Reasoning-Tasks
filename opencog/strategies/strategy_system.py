"""
Strategy Development and Management System

This module implements sophisticated strategy development for reasoning challenges,
integrating cognitive patterns with task-specific approaches.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of reasoning strategies"""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    HEURISTIC = "heuristic"
    SYSTEMATIC = "systematic"
    CREATIVE = "creative"
    HYBRID = "hybrid"


@dataclass
class Strategy:
    """Represents a problem-solving strategy"""
    id: str
    name: str
    strategy_type: StrategyType
    description: str
    applicable_patterns: List[str]
    steps: List[Dict[str, Any]]
    preconditions: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    use_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "strategy_type": self.strategy_type.value,
            "description": self.description,
            "applicable_patterns": self.applicable_patterns,
            "steps": self.steps,
            "preconditions": self.preconditions,
            "success_rate": self.success_rate,
            "use_count": self.use_count
        }


class StrategyRepository:
    """
    Repository of problem-solving strategies
    
    Maintains a collection of proven strategies for different types of
    reasoning challenges, learns from experience, and generates new strategies.
    """
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self._initialize_core_strategies()
        
    def _initialize_core_strategies(self):
        """Initialize core reasoning strategies"""
        
        core_strategies = [
            Strategy(
                id="decomposition_strategy",
                name="Decomposition Strategy",
                strategy_type=StrategyType.SYSTEMATIC,
                description="Break down complex problems into manageable sub-problems",
                applicable_patterns=["decomposition_pattern", "hierarchical_planning_pattern"],
                steps=[
                    {"step": 1, "action": "identify_problem_structure", "description": "Analyze the problem to identify natural divisions"},
                    {"step": 2, "action": "decompose", "description": "Break problem into independent sub-problems"},
                    {"step": 3, "action": "solve_subproblems", "description": "Solve each sub-problem independently"},
                    {"step": 4, "action": "integrate", "description": "Combine sub-solutions into complete solution"}
                ],
                preconditions=["problem_is_decomposable", "subproblems_are_independent"]
            ),
            
            Strategy(
                id="pattern_matching_strategy",
                name="Pattern Matching Strategy",
                strategy_type=StrategyType.ANALOGICAL,
                description="Identify similar problems and adapt known solutions",
                applicable_patterns=["pattern_matching_pattern", "analogy_pattern"],
                steps=[
                    {"step": 1, "action": "extract_features", "description": "Extract key features of the current problem"},
                    {"step": 2, "action": "search_similar", "description": "Search for similar problems in knowledge base"},
                    {"step": 3, "action": "map_solution", "description": "Map solution from similar problem to current problem"},
                    {"step": 4, "action": "adapt", "description": "Adapt the mapped solution to fit current context"}
                ],
                preconditions=["similar_problems_exist", "solution_is_transferable"]
            ),
            
            Strategy(
                id="constraint_propagation_strategy",
                name="Constraint Propagation Strategy",
                strategy_type=StrategyType.SYSTEMATIC,
                description="Use constraints to narrow solution space systematically",
                applicable_patterns=["constraint_satisfaction_pattern"],
                steps=[
                    {"step": 1, "action": "identify_constraints", "description": "List all constraints"},
                    {"step": 2, "action": "propagate", "description": "Apply constraint propagation to reduce possibilities"},
                    {"step": 3, "action": "search", "description": "Search remaining space systematically"},
                    {"step": 4, "action": "verify", "description": "Verify solution satisfies all constraints"}
                ],
                preconditions=["problem_has_constraints", "constraints_can_propagate"]
            ),
            
            Strategy(
                id="working_backward_strategy",
                name="Working Backward Strategy",
                strategy_type=StrategyType.HEURISTIC,
                description="Start from goal and work backward to find solution path",
                applicable_patterns=["working_backward_pattern", "means_ends_analysis_pattern"],
                steps=[
                    {"step": 1, "action": "define_goal", "description": "Clearly define the goal state"},
                    {"step": 2, "action": "identify_prerequisites", "description": "Identify what would lead to the goal"},
                    {"step": 3, "action": "recurse", "description": "Recursively work backward from prerequisites"},
                    {"step": 4, "action": "reverse_path", "description": "Reverse the backward chain to get solution"}
                ],
                preconditions=["goal_is_clear", "backward_steps_are_deterministic"]
            ),
            
            Strategy(
                id="hypothesis_testing_strategy",
                name="Hypothesis Testing Strategy",
                strategy_type=StrategyType.ABDUCTIVE,
                description="Generate hypotheses and test them systematically",
                applicable_patterns=["hypothesis_testing_pattern", "causal_reasoning_pattern"],
                steps=[
                    {"step": 1, "action": "generate_hypotheses", "description": "Generate plausible hypotheses"},
                    {"step": 2, "action": "design_tests", "description": "Design tests to discriminate between hypotheses"},
                    {"step": 3, "action": "execute_tests", "description": "Execute the tests"},
                    {"step": 4, "action": "evaluate", "description": "Evaluate hypotheses based on test results"}
                ],
                preconditions=["hypotheses_can_be_generated", "tests_are_feasible"]
            ),
            
            Strategy(
                id="recursive_refinement_strategy",
                name="Recursive Refinement Strategy",
                strategy_type=StrategyType.SYSTEMATIC,
                description="Recursively refine solution through multiple iterations",
                applicable_patterns=["recursive_thinking_pattern", "metacognitive_monitoring_pattern"],
                steps=[
                    {"step": 1, "action": "initial_solution", "description": "Generate initial rough solution"},
                    {"step": 2, "action": "evaluate", "description": "Evaluate solution quality"},
                    {"step": 3, "action": "identify_improvements", "description": "Identify areas for improvement"},
                    {"step": 4, "action": "refine", "description": "Refine solution, then recurse if needed"}
                ],
                preconditions=["iterative_improvement_possible", "quality_metrics_available"]
            ),
            
            Strategy(
                id="creative_exploration_strategy",
                name="Creative Exploration Strategy",
                strategy_type=StrategyType.CREATIVE,
                description="Explore unconventional approaches to find novel solutions",
                applicable_patterns=["divergent_thinking_pattern", "lateral_thinking_pattern"],
                steps=[
                    {"step": 1, "action": "brainstorm", "description": "Generate diverse ideas without filtering"},
                    {"step": 2, "action": "combine", "description": "Combine ideas in novel ways"},
                    {"step": 3, "action": "evaluate_novelty", "description": "Assess novelty and feasibility"},
                    {"step": 4, "action": "refine_promising", "description": "Refine most promising novel approaches"}
                ],
                preconditions=["conventional_approaches_insufficient", "creativity_is_valued"]
            )
        ]
        
        for strategy in core_strategies:
            self.add_strategy(strategy)
            
        logger.info(f"Initialized {len(core_strategies)} core strategies")
        
    def add_strategy(self, strategy: Strategy):
        """Add a strategy to the repository"""
        self.strategies[strategy.id] = strategy
        logger.info(f"Added strategy: {strategy.name}")
        
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get a strategy by ID"""
        return self.strategies.get(strategy_id)
        
    def find_strategies_for_task(
        self, 
        task_tags: List[str], 
        available_patterns: List[str]
    ) -> List[Strategy]:
        """
        Find strategies suitable for a task
        
        Args:
            task_tags: Tags describing the task
            available_patterns: Cognitive patterns available for use
            
        Returns:
            List of suitable strategies, ranked by relevance
        """
        suitable_strategies = []
        
        for strategy in self.strategies.values():
            # Check if any of the strategy's patterns are available
            pattern_match = any(
                pattern in available_patterns 
                for pattern in strategy.applicable_patterns
            )
            
            if pattern_match:
                # Calculate relevance score
                relevance = self._calculate_relevance(strategy, task_tags, available_patterns)
                suitable_strategies.append((strategy, relevance))
                
        # Sort by relevance and success rate
        suitable_strategies.sort(
            key=lambda x: (x[1], x[0].success_rate, x[0].use_count),
            reverse=True
        )
        
        return [s[0] for s in suitable_strategies]
        
    def compose_hybrid_strategy(
        self, 
        strategies: List[Strategy],
        task_context: Dict[str, Any]
    ) -> Strategy:
        """
        Compose a hybrid strategy from multiple strategies
        
        Args:
            strategies: List of strategies to compose
            task_context: Context about the task
            
        Returns:
            New hybrid strategy
        """
        hybrid_id = f"hybrid_{'_'.join([s.id for s in strategies[:2]])}"
        
        # Combine steps from all strategies
        combined_steps = []
        step_num = 1
        for strategy in strategies:
            for step in strategy.steps:
                combined_steps.append({
                    **step,
                    "step": step_num,
                    "source_strategy": strategy.name
                })
                step_num += 1
                
        # Combine applicable patterns
        all_patterns = []
        for strategy in strategies:
            all_patterns.extend(strategy.applicable_patterns)
        all_patterns = list(set(all_patterns))  # Remove duplicates
        
        # Combine preconditions
        all_preconditions = []
        for strategy in strategies:
            all_preconditions.extend(strategy.preconditions)
        all_preconditions = list(set(all_preconditions))
        
        hybrid = Strategy(
            id=hybrid_id,
            name=f"Hybrid: {' + '.join([s.name for s in strategies])}",
            strategy_type=StrategyType.HYBRID,
            description=f"Hybrid strategy combining: {', '.join([s.name for s in strategies])}",
            applicable_patterns=all_patterns,
            steps=combined_steps,
            preconditions=all_preconditions
        )
        
        # Add to repository
        self.add_strategy(hybrid)
        
        logger.info(f"Created hybrid strategy: {hybrid.name}")
        return hybrid
        
    def record_strategy_use(self, strategy_id: str, success: bool):
        """Record usage and outcome of a strategy"""
        if strategy_id not in self.strategies:
            return
            
        strategy = self.strategies[strategy_id]
        strategy.use_count += 1
        
        # Update success rate with exponential moving average
        alpha = 0.1
        strategy.success_rate = (
            alpha * (1.0 if success else 0.0) +
            (1 - alpha) * strategy.success_rate
        )
        
        logger.info(f"Recorded strategy use: {strategy.name}, success={success}")
        
    def _calculate_relevance(
        self, 
        strategy: Strategy, 
        task_tags: List[str],
        available_patterns: List[str]
    ) -> float:
        """Calculate relevance score for a strategy"""
        score = 0.0
        
        # Pattern match score
        pattern_matches = sum(
            1 for p in strategy.applicable_patterns 
            if p in available_patterns
        )
        score += pattern_matches * 2.0
        
        # Success rate contribution
        score += strategy.success_rate * 1.0
        
        # Use count contribution (prefer proven strategies)
        score += min(strategy.use_count / 100.0, 1.0) * 0.5
        
        return score


class StrategyExecutor:
    """
    Executes strategies on reasoning tasks
    
    Takes a strategy and applies it step-by-step to solve a task.
    """
    
    def __init__(self, pattern_library=None):
        self.pattern_library = pattern_library
        self.execution_history: List[Dict[str, Any]] = []
        
    def execute_strategy(
        self, 
        strategy: Strategy, 
        task: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a strategy on a task
        
        Args:
            strategy: The strategy to execute
            task: The task to solve
            context: Additional context information
            
        Returns:
            Execution results
        """
        context = context or {}
        
        execution = {
            "strategy": strategy.name,
            "task": task.get("name", task.get("id")),
            "steps_executed": [],
            "intermediate_results": [],
            "final_result": None,
            "success": False
        }
        
        logger.info(f"Executing strategy '{strategy.name}' on task '{task.get('name')}'")
        
        # Execute each step
        for step in strategy.steps:
            step_result = self._execute_step(step, task, context, execution)
            execution["steps_executed"].append(step)
            execution["intermediate_results"].append(step_result)
            
            # Update context with step result
            context[f"step_{step['step']}_result"] = step_result
            
        # Determine final result and success
        execution["final_result"] = execution["intermediate_results"][-1] if execution["intermediate_results"] else None
        execution["success"] = self._evaluate_success(execution, task)
        
        # Record execution
        self.execution_history.append(execution)
        
        logger.info(f"Strategy execution completed. Success: {execution['success']}")
        return execution
        
    def _execute_step(
        self, 
        step: Dict[str, Any], 
        task: Dict[str, Any],
        context: Dict[str, Any],
        execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single strategy step"""
        
        step_result = {
            "step_number": step["step"],
            "action": step["action"],
            "description": step.get("description", ""),
            "output": None,
            "status": "completed"
        }
        
        # In a full implementation, this would actually execute the step
        # For now, we'll simulate execution
        step_result["output"] = f"Executed {step['action']}"
        
        logger.debug(f"Executed step {step['step']}: {step['action']}")
        return step_result
        
    def _evaluate_success(self, execution: Dict[str, Any], task: Dict[str, Any]) -> bool:
        """Evaluate whether strategy execution was successful"""
        # Simplified success evaluation
        # In practice, would compare results against task requirements
        return len(execution["steps_executed"]) > 0 and all(
            result.get("status") == "completed" 
            for result in execution["intermediate_results"]
        )
