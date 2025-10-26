#!/usr/bin/env python3
"""
OpenCog Workbench Demo

This script demonstrates the capabilities of the OpenCog Multi-Agent
Orchestration Workbench for solving reasoning tasks.
"""

import os
import sys
import json
import logging

# Add opencog to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opencog import OpenCogWorkbench


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demo_workbench_initialization():
    """Demonstrate workbench initialization"""
    print("\n" + "="*80)
    print("DEMO 1: OpenCog Workbench Initialization")
    print("="*80 + "\n")
    
    # Initialize workbench
    tasks_dir = os.path.join(os.path.dirname(__file__), "tasks")
    workbench = OpenCogWorkbench(tasks_dir=tasks_dir)
    
    # Show statistics
    stats = workbench.get_statistics()
    print("Workbench Statistics:")
    print(json.dumps(stats, indent=2))
    
    return workbench


def demo_pattern_library(workbench):
    """Demonstrate the pattern language library"""
    print("\n" + "="*80)
    print("DEMO 2: AGI Cognitive Architecture Pattern Language")
    print("="*80 + "\n")
    
    # Get pattern catalog
    catalog = workbench.get_pattern_catalog()
    
    print(f"Total Patterns: {catalog['total_patterns']}\n")
    
    print("Patterns by Category:")
    for category, patterns in catalog['categories'].items():
        if patterns:
            print(f"\n{category.upper()} ({len(patterns)} patterns):")
            for pattern in patterns[:3]:  # Show first 3 in each category
                print(f"  - {pattern['name']} (Quality: {pattern['quality']}, Uses: {pattern['use_count']})")
                
    # Show a detailed pattern
    print("\n" + "-"*80)
    print("Example Pattern: Problem Decomposition")
    print("-"*80)
    
    pattern = workbench.pattern_library.get_pattern("decomposition_pattern")
    if pattern:
        print(f"Name: {pattern.name}")
        print(f"Category: {pattern.category.value}")
        print(f"Context: {pattern.context}")
        print(f"Problem: {pattern.problem}")
        print(f"\nSolution: {pattern.solution}")
        print(f"\nForces to balance:")
        for force in pattern.forces:
            print(f"  - {force}")
        print(f"\nRelated patterns: {', '.join(pattern.related_patterns)}")


def demo_agent_zero(workbench):
    """Demonstrate Agent-Zero master builder"""
    print("\n" + "="*80)
    print("DEMO 3: Agent-Zero Master Builder")
    print("="*80 + "\n")
    
    # Show Agent-Zero's agents
    print("Agent-Zero's Cognitive Agents:")
    for agent_id, agent in workbench.agent_zero.agents.items():
        print(f"\n{agent_id}:")
        print(f"  Role: {agent.role.value}")
        print(f"  Capabilities: {', '.join(agent.capabilities)}")
        
    # Analyze a task
    if workbench.tasks:
        task = list(workbench.tasks.values())[0]
        print(f"\n{'-'*80}")
        print(f"Task Analysis Example: {task.name}")
        print(f"{'-'*80}")
        
        analysis = workbench.agent_zero.analyze_task(task)
        print(json.dumps(analysis, indent=2))


def demo_task_solving(workbench):
    """Demonstrate solving reasoning tasks"""
    print("\n" + "="*80)
    print("DEMO 4: Autonomous Task Solving")
    print("="*80 + "\n")
    
    if not workbench.tasks:
        print("No tasks loaded. Please ensure tasks are in the 'tasks' directory.")
        return
        
    # Get a sample task
    task = list(workbench.tasks.values())[0]
    
    print(f"Solving task: {task.name}")
    print(f"Description: {task.description}")
    print(f"Tags: {', '.join(task.tags)}\n")
    
    # Get recommendations first
    print("Getting recommendations...")
    recommendations = workbench.get_task_recommendations(task.id)
    
    print("\nRecommended Patterns:")
    for pattern in recommendations['recommended_patterns'][:3]:
        print(f"  - {pattern['name']} (Quality: {pattern['quality']})")
        
    print("\nRecommended Strategies:")
    for strategy in recommendations['recommended_strategies'][:3]:
        print(f"  - {strategy['name']} (Type: {strategy['type']}, Success Rate: {strategy['success_rate']:.2f})")
        
    # Solve in collaborative mode
    print(f"\n{'-'*80}")
    print("Solving task in COLLABORATIVE mode...")
    print(f"{'-'*80}\n")
    
    result = workbench.solve_task(task.id, orchestration_mode="collaborative")
    
    print("Solution Result:")
    print(f"  Success: {result.get('success', 'Unknown')}")
    print(f"  Patterns Used: {', '.join(result.get('patterns_used', []))}")
    if 'strategy' in result:
        print(f"  Strategy: {result['strategy']}")


def demo_multi_agent_orchestration(workbench):
    """Demonstrate multi-agent orchestration"""
    print("\n" + "="*80)
    print("DEMO 5: Multi-Agent Orchestration")
    print("="*80 + "\n")
    
    # Create a sample task for orchestration
    from opencog.agents.agent_zero import Task
    
    sample_task = Task(
        id="demo_logic_puzzle",
        name="Logic Puzzle Solving",
        description="Solve a complex logic puzzle requiring multiple reasoning steps",
        modality="Text only",
        tags=["Logic", "Problem Solving", "Deduction"]
    )
    
    # Create orchestration session
    session_id = "demo_session_001"
    agent_ids = list(workbench.agent_zero.agents.keys())
    
    session = workbench.orchestrator.create_session(session_id, agent_ids)
    
    print(f"Created orchestration session: {session_id}")
    print(f"Participating agents: {', '.join(agent_ids)}\n")
    
    # Prepare task for orchestration
    task_dict = {
        "id": sample_task.id,
        "name": sample_task.name,
        "description": sample_task.description,
        "required_capabilities": ["reasoning", "problem_solving"]
    }
    
    # Orchestrate with collaborative strategy
    print("Orchestrating task with COLLABORATIVE strategy...")
    result = workbench.orchestrator.orchestrate_multi_agent_task(
        session_id,
        task_dict,
        strategy="collaborative"
    )
    
    print(f"\nOrchestration Result:")
    print(f"  Strategy: {result['strategy']}")
    print(f"  Agents Involved: {len(result['agents_involved'])}")
    
    # Check session status
    status = workbench.orchestrator.get_session_status(session_id)
    if status:
        print(f"\nSession Status:")
        print(json.dumps(status, indent=2))


def demo_pattern_evolution(workbench):
    """Demonstrate pattern evolution and learning"""
    print("\n" + "="*80)
    print("DEMO 6: Pattern Evolution and Learning")
    print("="*80 + "\n")
    
    # Record some pattern uses
    pattern = workbench.pattern_library.get_pattern("decomposition_pattern")
    
    if pattern:
        print(f"Pattern: {pattern.name}")
        print(f"Initial state:")
        print(f"  Use count: {pattern.use_count}")
        print(f"  Success rate: {pattern.success_rate:.2f}")
        print(f"  Quality: {pattern.quality.value}")
        
        # Simulate pattern uses
        print("\nSimulating pattern uses...")
        for i in range(10):
            success = i % 4 != 0  # 75% success rate
            workbench.pattern_library.record_pattern_use(pattern.id, success)
            
        print(f"\nAfter 10 uses:")
        print(f"  Use count: {pattern.use_count}")
        print(f"  Success rate: {pattern.success_rate:.2f}")
        print(f"  Quality: {pattern.quality.value}")
        
        # Add a new example
        new_example = {
            "task": "Complex system analysis",
            "application": "Decomposed system into components, analyzed each, then integrated findings"
        }
        workbench.pattern_library.evolve_pattern(pattern.id, new_example)
        print(f"\nAdded new example to pattern. Total examples: {len(pattern.examples)}")


def main():
    """Run all demos"""
    setup_logging()
    
    print("\n" + "="*80)
    print(" "*20 + "OpenCog Workbench Demo")
    print("="*80)
    print("\nDemonstrating the OpenCog Multi-Agent Orchestration Workbench")
    print("for solving LLM reasoning tasks with Agent-Zero and Pattern Language.\n")
    
    try:
        # Initialize workbench
        workbench = demo_workbench_initialization()
        
        # Run demos
        demo_pattern_library(workbench)
        demo_agent_zero(workbench)
        demo_multi_agent_orchestration(workbench)
        demo_pattern_evolution(workbench)
        
        # Only demo task solving if tasks are loaded
        if workbench.tasks:
            demo_task_solving(workbench)
        else:
            print("\n" + "="*80)
            print("DEMO 4: Skipped (no tasks loaded)")
            print("="*80)
            print("\nTo see task solving demo, ensure reasoning tasks are in the 'tasks' directory.")
        
        print("\n" + "="*80)
        print(" "*25 + "Demo Complete!")
        print("="*80)
        print("\nThe OpenCog Workbench is ready for autonomous multi-agent")
        print("orchestration of reasoning tasks with sophisticated cognitive")
        print("architectures and evolving pattern languages.")
        print("\n")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
