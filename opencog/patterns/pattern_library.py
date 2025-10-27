"""
AGI Cognitive Architecture Pattern Language

Inspired by Christopher Alexander's "A Pattern Language", this module implements
a living library of cognitive patterns for artificial general intelligence.

Each pattern describes a recurring problem in reasoning and cognition, and provides
a proven solution that can be adapted and applied to new situations.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    """Categories of cognitive patterns"""
    REASONING = "reasoning"
    PROBLEM_SOLVING = "problem_solving"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    METACOGNITION = "metacognition"
    MEMORY = "memory"
    PERCEPTION = "perception"


class PatternQuality(Enum):
    """Quality levels for patterns based on validation and use"""
    EXPERIMENTAL = "experimental"  # New, not yet validated
    PROVEN = "proven"  # Validated through use
    MATURE = "mature"  # Extensively used and refined
    FOUNDATIONAL = "foundational"  # Core pattern used by many others


@dataclass
class CognitivePattern:
    """
    Represents a cognitive pattern in the pattern language.
    
    Based on Alexander's pattern structure:
    - Name: A descriptive name for the pattern
    - Context: When/where this pattern applies
    - Problem: The recurring problem this pattern solves
    - Forces: The conflicting considerations that must be balanced
    - Solution: The proven solution approach
    - Examples: Concrete examples of the pattern in use
    - Related: Connections to other patterns
    """
    
    id: str
    name: str
    category: PatternCategory
    context: str
    problem: str
    forces: List[str]
    solution: str
    examples: List[Dict[str, Any]] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    quality: PatternQuality = PatternQuality.EXPERIMENTAL
    use_count: int = 0
    success_rate: float = 0.0
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "context": self.context,
            "problem": self.problem,
            "forces": self.forces,
            "solution": self.solution,
            "examples": self.examples,
            "related_patterns": self.related_patterns,
            "quality": self.quality.value,
            "use_count": self.use_count,
            "success_rate": self.success_rate,
            "created_date": self.created_date,
            "last_updated": self.last_updated
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitivePattern':
        """Create pattern from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            category=PatternCategory(data["category"]),
            context=data["context"],
            problem=data["problem"],
            forces=data["forces"],
            solution=data["solution"],
            examples=data.get("examples", []),
            related_patterns=data.get("related_patterns", []),
            quality=PatternQuality(data.get("quality", "experimental")),
            use_count=data.get("use_count", 0),
            success_rate=data.get("success_rate", 0.0),
            created_date=data.get("created_date", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat())
        )


class PatternLanguageLibrary:
    """
    The living library of cognitive patterns for AGI.
    
    This library:
    - Stores and organizes cognitive patterns
    - Helps select appropriate patterns for tasks
    - Tracks pattern usage and effectiveness
    - Evolves patterns based on experience
    - Supports pattern composition and inheritance
    """
    
    def __init__(self, library_path: Optional[str] = None):
        self.patterns: Dict[str, CognitivePattern] = {}
        self.library_path = library_path
        self.pattern_graph: Dict[str, List[str]] = {}  # Pattern relationships
        
        # Initialize with foundational patterns
        self._initialize_foundational_patterns()
        
    def _initialize_foundational_patterns(self):
        """Initialize the core set of foundational cognitive patterns"""
        
        foundational_patterns = [
            CognitivePattern(
                id="decomposition_pattern",
                name="Problem Decomposition",
                category=PatternCategory.PROBLEM_SOLVING,
                context="When facing a complex problem that cannot be solved directly",
                problem="Complex problems are overwhelming and difficult to solve as a whole",
                forces=[
                    "Need to maintain understanding of the whole while working on parts",
                    "Parts must be meaningful and solvable independently",
                    "Solutions to parts must integrate into a coherent whole"
                ],
                solution="Break the problem into smaller, manageable sub-problems. Solve each sub-problem independently, then integrate the solutions. Use hierarchical decomposition for very complex problems.",
                examples=[
                    {
                        "task": "Towers of Hanoi",
                        "application": "Decompose into moving n-1 disks, moving largest disk, then moving n-1 disks again"
                    }
                ],
                related_patterns=["recursive_thinking_pattern", "hierarchical_planning_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="recursive_thinking_pattern",
                name="Recursive Thinking",
                category=PatternCategory.REASONING,
                context="When a problem can be expressed in terms of smaller instances of itself",
                problem="Some problems have self-similar structure at different scales",
                forces=[
                    "Need a base case to prevent infinite recursion",
                    "Each recursive call must make progress toward the base case",
                    "Must manage the cognitive load of nested recursive calls"
                ],
                solution="Express the problem in terms of smaller instances of the same problem. Define clear base cases. Ensure each recursive step makes progress toward a base case.",
                examples=[
                    {
                        "task": "Mathematical induction",
                        "application": "Prove for base case, then prove that if true for n, true for n+1"
                    }
                ],
                related_patterns=["decomposition_pattern", "pattern_matching_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="pattern_matching_pattern",
                name="Pattern Recognition and Matching",
                category=PatternCategory.PERCEPTION,
                context="When encountering new situations that may be similar to known situations",
                problem="New problems often resemble previously solved problems, but recognition is not automatic",
                forces=[
                    "Need to identify essential similarities while ignoring superficial differences",
                    "Must avoid false pattern matches (seeing patterns that aren't there)",
                    "Must be able to abstract patterns from concrete examples"
                ],
                solution="Maintain a library of known patterns. Extract key features from new situations. Compare against known patterns using similarity metrics. Adapt matched patterns to the new context.",
                examples=[
                    {
                        "task": "Analogical reasoning",
                        "application": "Recognize that A:B :: C:? has same relationship structure as known examples"
                    }
                ],
                related_patterns=["abstraction_pattern", "analogy_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="logical_reasoning_pattern",
                name="Logical Inference",
                category=PatternCategory.REASONING,
                context="When conclusions must be derived from premises using logical rules",
                problem="Need to derive valid conclusions from given information",
                forces=[
                    "Must ensure logical validity (conclusions follow from premises)",
                    "Must distinguish between valid and sound arguments",
                    "Must handle uncertainty and incomplete information"
                ],
                solution="Apply logical rules systematically (modus ponens, modus tollens, etc.). Build proof chains from premises to conclusion. Check for logical fallacies.",
                examples=[
                    {
                        "task": "Syllogistic reasoning",
                        "application": "From 'All A are B' and 'All B are C', derive 'All A are C'"
                    }
                ],
                related_patterns=["deductive_reasoning_pattern", "truth_table_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="abstraction_pattern",
                name="Abstraction and Generalization",
                category=PatternCategory.LEARNING,
                context="When specific instances contain generalizable principles",
                problem="Learning from specific examples without extracting general principles limits transfer",
                forces=[
                    "Need to identify which features are essential vs. incidental",
                    "Must find the right level of abstraction (not too specific, not too general)",
                    "Must validate abstractions against new examples"
                ],
                solution="Identify commonalities across examples. Abstract away incidental details. Form general rules or principles. Test abstractions on new cases.",
                examples=[
                    {
                        "task": "Learning arithmetic",
                        "application": "Abstract from 2+3=5, 5+7=12, etc. to general addition principles"
                    }
                ],
                related_patterns=["pattern_matching_pattern", "inductive_reasoning_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="working_backward_pattern",
                name="Working Backward from Goal",
                category=PatternCategory.PROBLEM_SOLVING,
                context="When the goal state is clearer than the path from the current state",
                problem="Forward search from current state may be intractable or unclear",
                forces=[
                    "Must ensure backward steps are reversible/achievable",
                    "Must eventually connect backward chain to current state",
                    "May need to combine with forward search"
                ],
                solution="Start from the desired goal. Work backward to identify prerequisites. Continue until reaching the current state or a known achievable state.",
                examples=[
                    {
                        "task": "Mathematical proofs",
                        "application": "Start with what you want to prove, work backward to known theorems"
                    }
                ],
                related_patterns=["means_ends_analysis_pattern", "goal_decomposition_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="metacognitive_monitoring_pattern",
                name="Metacognitive Monitoring",
                category=PatternCategory.METACOGNITION,
                context="During problem solving and reasoning processes",
                problem="Without monitoring, errors and ineffective strategies may go undetected",
                forces=[
                    "Monitoring has cognitive cost that must be balanced with benefits",
                    "Must know what to monitor and when",
                    "Must be able to act on monitoring results"
                ],
                solution="Periodically assess progress toward goals. Check for errors and inconsistencies. Evaluate effectiveness of current strategy. Adjust approach based on monitoring results.",
                examples=[
                    {
                        "task": "Complex problem solving",
                        "application": "Regularly ask 'Am I making progress?', 'Is this approach working?', 'Should I try something else?'"
                    }
                ],
                related_patterns=["strategy_selection_pattern", "error_detection_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="analogy_pattern",
                name="Analogical Transfer",
                category=PatternCategory.REASONING,
                context="When a new problem resembles a previously solved problem in structure",
                problem="Solutions to known problems can often be adapted to new problems, but transfer is not automatic",
                forces=[
                    "Must identify structural similarity despite surface differences",
                    "Must adapt solution to fit new context",
                    "Must validate that analogy holds in the new domain"
                ],
                solution="Identify source problem with similar structure. Map elements from source to target domain. Adapt solution strategy to new context. Verify that adapted solution works.",
                examples=[
                    {
                        "task": "Solving new physics problems",
                        "application": "Recognize that new problem has same mathematical structure as solved problem"
                    }
                ],
                related_patterns=["pattern_matching_pattern", "transfer_learning_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="constraint_satisfaction_pattern",
                name="Constraint Satisfaction",
                category=PatternCategory.PROBLEM_SOLVING,
                context="When solutions must satisfy multiple constraints simultaneously",
                problem="Finding solutions that satisfy all constraints can be challenging",
                forces=[
                    "Constraints may conflict or interact in complex ways",
                    "Search space may be large",
                    "Some constraints may be hard vs. soft"
                ],
                solution="Identify all constraints. Use constraint propagation to reduce search space. Apply systematic search (backtracking, forward checking). Prioritize constraints appropriately.",
                examples=[
                    {
                        "task": "Logic puzzles",
                        "application": "Each clue is a constraint; find assignment that satisfies all clues"
                    }
                ],
                related_patterns=["systematic_search_pattern", "pruning_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            ),
            
            CognitivePattern(
                id="causal_reasoning_pattern",
                name="Causal Reasoning",
                category=PatternCategory.REASONING,
                context="When understanding or predicting cause-effect relationships",
                problem="Correlation does not imply causation; true causal relationships must be identified",
                forces=[
                    "Must distinguish correlation from causation",
                    "Must account for confounding variables",
                    "Must understand causal mechanisms, not just associations"
                ],
                solution="Build causal models with directional relationships. Test interventions to verify causation. Account for common causes and confounders. Use counterfactual reasoning.",
                examples=[
                    {
                        "task": "Scientific reasoning",
                        "application": "Design experiments to test causal hypotheses, control for confounds"
                    }
                ],
                related_patterns=["hypothesis_testing_pattern", "counterfactual_pattern"],
                quality=PatternQuality.FOUNDATIONAL
            )
        ]
        
        for pattern in foundational_patterns:
            self.add_pattern(pattern)
            
        logger.info(f"Initialized {len(foundational_patterns)} foundational patterns")
        
    def add_pattern(self, pattern: CognitivePattern):
        """Add a pattern to the library"""
        self.patterns[pattern.id] = pattern
        
        # Update pattern graph
        for related_id in pattern.related_patterns:
            if pattern.id not in self.pattern_graph:
                self.pattern_graph[pattern.id] = []
            if related_id not in self.pattern_graph[pattern.id]:
                self.pattern_graph[pattern.id].append(related_id)
                
        logger.info(f"Added pattern: {pattern.name}")
        
    def get_pattern(self, pattern_id: str) -> Optional[CognitivePattern]:
        """Retrieve a pattern by ID"""
        return self.patterns.get(pattern_id)
        
    def find_patterns_by_category(self, category: PatternCategory) -> List[CognitivePattern]:
        """Find all patterns in a category"""
        return [p for p in self.patterns.values() if p.category == category]
        
    def find_patterns_by_quality(self, quality: PatternQuality) -> List[CognitivePattern]:
        """Find all patterns of a given quality level"""
        return [p for p in self.patterns.values() if p.quality == quality]
        
    def match_patterns_to_task(self, task_description: str, task_tags: List[str]) -> List[CognitivePattern]:
        """
        Find patterns that are relevant to a given task
        
        Args:
            task_description: Description of the task
            task_tags: Tags associated with the task
            
        Returns:
            List of relevant patterns, ranked by relevance
        """
        relevant_patterns = []
        
        # Simple keyword matching - in production would use more sophisticated NLP
        keywords = set(task_description.lower().split() + [tag.lower() for tag in task_tags])
        
        for pattern in self.patterns.values():
            # Check if pattern context, problem, or solution mentions task keywords
            pattern_text = (
                pattern.context + " " + 
                pattern.problem + " " + 
                pattern.solution + " " +
                pattern.name
            ).lower()
            
            relevance_score = sum(1 for keyword in keywords if keyword in pattern_text)
            
            if relevance_score > 0:
                relevant_patterns.append((pattern, relevance_score))
                
        # Sort by relevance score and quality
        relevant_patterns.sort(
            key=lambda x: (x[1], x[0].use_count, x[0].success_rate),
            reverse=True
        )
        
        return [p[0] for p in relevant_patterns]
        
    def get_related_patterns(self, pattern_id: str, depth: int = 1) -> List[str]:
        """
        Get related patterns up to a certain depth
        
        Args:
            pattern_id: Starting pattern ID
            depth: How many levels of relationships to traverse
            
        Returns:
            List of related pattern IDs
        """
        if depth <= 0 or pattern_id not in self.pattern_graph:
            return []
            
        related = set(self.pattern_graph.get(pattern_id, []))
        
        if depth > 1:
            for related_id in list(related):
                related.update(self.get_related_patterns(related_id, depth - 1))
                
        return list(related)
        
    def record_pattern_use(self, pattern_id: str, success: bool):
        """
        Record usage of a pattern and its outcome
        
        Args:
            pattern_id: ID of the pattern that was used
            success: Whether the pattern application was successful
        """
        if pattern_id not in self.patterns:
            return
            
        pattern = self.patterns[pattern_id]
        pattern.use_count += 1
        
        # Update success rate using exponential moving average
        alpha = 0.1  # Learning rate
        pattern.success_rate = (
            alpha * (1.0 if success else 0.0) + 
            (1 - alpha) * pattern.success_rate
        )
        
        # Update quality based on use count and success rate
        if pattern.use_count > 100 and pattern.success_rate > 0.9:
            pattern.quality = PatternQuality.FOUNDATIONAL
        elif pattern.use_count > 50 and pattern.success_rate > 0.8:
            pattern.quality = PatternQuality.MATURE
        elif pattern.use_count > 10 and pattern.success_rate > 0.7:
            pattern.quality = PatternQuality.PROVEN
            
        pattern.last_updated = datetime.now().isoformat()
        
        logger.info(f"Recorded use of pattern {pattern.name}: success={success}, new success_rate={pattern.success_rate:.2f}")
        
    def compose_patterns(self, pattern_ids: List[str]) -> Dict[str, Any]:
        """
        Compose multiple patterns into a coherent strategy
        
        Args:
            pattern_ids: List of pattern IDs to compose
            
        Returns:
            Composed strategy specification
        """
        patterns = [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]
        
        strategy = {
            "composed_patterns": [p.name for p in patterns],
            "execution_order": self._determine_execution_order(patterns),
            "integration_points": self._find_integration_points(patterns),
            "combined_forces": self._combine_forces(patterns)
        }
        
        return strategy
        
    def evolve_pattern(self, pattern_id: str, new_example: Dict[str, Any]):
        """
        Evolve a pattern based on new usage example
        
        Args:
            pattern_id: Pattern to evolve
            new_example: New example to incorporate
        """
        if pattern_id not in self.patterns:
            return
            
        pattern = self.patterns[pattern_id]
        pattern.examples.append(new_example)
        pattern.last_updated = datetime.now().isoformat()
        
        logger.info(f"Evolved pattern {pattern.name} with new example")
        
    def save_library(self, path: Optional[str] = None):
        """Save the pattern library to disk"""
        save_path = path or self.library_path
        if not save_path:
            logger.warning("No save path specified")
            return
            
        library_data = {
            "patterns": {pid: p.to_dict() for pid, p in self.patterns.items()},
            "pattern_graph": self.pattern_graph
        }
        
        with open(save_path, 'w') as f:
            json.dump(library_data, f, indent=2)
            
        logger.info(f"Saved pattern library to {save_path}")
        
    def load_library(self, path: str):
        """Load pattern library from disk"""
        with open(path, 'r') as f:
            library_data = json.load(f)
            
        self.patterns = {
            pid: CognitivePattern.from_dict(pdata) 
            for pid, pdata in library_data["patterns"].items()
        }
        self.pattern_graph = library_data["pattern_graph"]
        
        logger.info(f"Loaded {len(self.patterns)} patterns from {path}")
        
    # Helper methods
    
    def _determine_execution_order(self, patterns: List[CognitivePattern]) -> List[str]:
        """Determine optimal order for applying patterns"""
        # Topological sort based on pattern dependencies
        # Simplified version - just return pattern names in order
        return [p.name for p in patterns]
        
    def _find_integration_points(self, patterns: List[CognitivePattern]) -> List[str]:
        """Find where patterns need to be integrated"""
        integration_points = []
        
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i+1:]:
                if p2.id in p1.related_patterns or p1.id in p2.related_patterns:
                    integration_points.append(f"{p1.name} <-> {p2.name}")
                    
        return integration_points
        
    def _combine_forces(self, patterns: List[CognitivePattern]) -> List[str]:
        """Combine forces from multiple patterns"""
        all_forces = []
        for pattern in patterns:
            all_forces.extend(pattern.forces)
        return list(set(all_forces))  # Remove duplicates
