"""
Multi-Agent Orchestration Framework

This module provides the core orchestration system for coordinating multiple
agents working together to solve reasoning tasks.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages agents can exchange"""
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    REQUEST_HELP = "request_help"
    PROVIDE_RESULT = "provide_result"
    QUERY = "query"
    RESPONSE = "response"
    COORDINATION = "coordination"


@dataclass
class Message:
    """Message passed between agents"""
    sender: str
    receiver: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp
        }


class MessageBus:
    """Central message bus for agent communication"""
    
    def __init__(self):
        self.message_queue: List[Message] = []
        self.message_history: List[Message] = []
        self.subscriptions: Dict[str, List[MessageType]] = {}
        
    def subscribe(self, agent_id: str, message_types: List[MessageType]):
        """Subscribe an agent to specific message types"""
        self.subscriptions[agent_id] = message_types
        logger.debug(f"Agent {agent_id} subscribed to {[mt.value for mt in message_types]}")
        
    def publish(self, message: Message):
        """Publish a message to the bus"""
        self.message_queue.append(message)
        self.message_history.append(message)
        logger.debug(f"Message published: {message.sender} -> {message.receiver} ({message.message_type.value})")
        
    def get_messages_for(self, agent_id: str) -> List[Message]:
        """Get all pending messages for an agent"""
        messages = [
            m for m in self.message_queue 
            if m.receiver == agent_id or m.receiver == "broadcast"
        ]
        
        # Remove retrieved messages from queue
        self.message_queue = [
            m for m in self.message_queue 
            if m.receiver != agent_id and m.receiver != "broadcast"
        ]
        
        return messages
        
    def clear(self):
        """Clear the message queue"""
        self.message_queue.clear()
        
    def get_history(self) -> List[Message]:
        """Get message history"""
        return self.message_history.copy()


class TaskQueue:
    """Queue for managing tasks across agents"""
    
    def __init__(self):
        self.pending_tasks: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        
    def add_task(self, task: Dict[str, Any]):
        """Add a task to the queue"""
        self.pending_tasks.append(task)
        logger.info(f"Task added to queue: {task.get('id', 'unknown')}")
        
    def assign_task(self, task_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Assign a pending task to an agent"""
        for task in self.pending_tasks:
            if task["id"] == task_id:
                task["assigned_to"] = agent_id
                self.active_tasks[task_id] = task
                self.pending_tasks.remove(task)
                logger.info(f"Task {task_id} assigned to agent {agent_id}")
                return task
        return None
        
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next pending task"""
        if self.pending_tasks:
            return self.pending_tasks[0]
        return None
        
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """Mark a task as completed"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task["result"] = result
            task["status"] = "completed"
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            logger.info(f"Task {task_id} completed")
            
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task"""
        if task_id in self.completed_tasks:
            return "completed"
        elif task_id in self.active_tasks:
            return "active"
        elif any(t["id"] == task_id for t in self.pending_tasks):
            return "pending"
        return None


class AgentCoordinator:
    """
    Coordinates multiple agents working on tasks
    
    Responsibilities:
    - Task distribution and load balancing
    - Agent capability matching to tasks
    - Conflict resolution
    - Progress monitoring
    - Resource allocation
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.agent_load: Dict[str, int] = {}
        self.message_bus = MessageBus()
        self.task_queue = TaskQueue()
        
    def register_agent(self, agent_id: str, capabilities: List[str]):
        """Register an agent with the coordinator"""
        self.agent_capabilities[agent_id] = capabilities
        self.agent_load[agent_id] = 0
        logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
        
    def find_capable_agents(self, required_capabilities: List[str]) -> List[str]:
        """Find agents capable of handling a task"""
        capable_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if all(req_cap in capabilities for req_cap in required_capabilities):
                capable_agents.append(agent_id)
                
        return capable_agents
        
    def assign_task_to_agent(self, task: Dict[str, Any]) -> Optional[str]:
        """
        Assign a task to the most suitable agent
        
        Uses load balancing and capability matching
        """
        required_caps = task.get("required_capabilities", [])
        capable_agents = self.find_capable_agents(required_caps)
        
        if not capable_agents:
            logger.warning(f"No capable agents found for task {task['id']}")
            return None
            
        # Select agent with lowest current load
        selected_agent = min(capable_agents, key=lambda a: self.agent_load[a])
        
        # Assign task
        self.task_queue.assign_task(task["id"], selected_agent)
        self.agent_load[selected_agent] += 1
        
        # Send task assignment message
        message = Message(
            sender="coordinator",
            receiver=selected_agent,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": task}
        )
        self.message_bus.publish(message)
        
        logger.info(f"Task {task['id']} assigned to {selected_agent}")
        return selected_agent
        
    def handle_task_completion(self, agent_id: str, task_id: str, result: Dict[str, Any]):
        """Handle task completion from an agent"""
        self.task_queue.complete_task(task_id, result)
        self.agent_load[agent_id] = max(0, self.agent_load[agent_id] - 1)
        logger.info(f"Agent {agent_id} completed task {task_id}")
        
    def coordinate_collaboration(self, task: Dict[str, Any], agents: List[str]) -> Dict[str, Any]:
        """
        Coordinate multiple agents working on the same task
        
        Args:
            task: The task to be solved collaboratively
            agents: List of agent IDs to involve
            
        Returns:
            Coordination plan
        """
        plan = {
            "task_id": task["id"],
            "participating_agents": agents,
            "coordination_strategy": "divide_and_conquer",
            "subtasks": [],
            "integration_plan": {}
        }
        
        # Divide task into subtasks
        if "subtasks" in task:
            plan["subtasks"] = task["subtasks"]
        else:
            # Default division by agent count
            plan["subtasks"] = self._default_task_division(task, len(agents))
            
        # Assign subtasks
        for i, (agent_id, subtask) in enumerate(zip(agents, plan["subtasks"])):
            subtask["assigned_to"] = agent_id
            
            # Send coordination message
            message = Message(
                sender="coordinator",
                receiver=agent_id,
                message_type=MessageType.COORDINATION,
                content={
                    "main_task": task["id"],
                    "subtask": subtask,
                    "collaborators": [a for a in agents if a != agent_id]
                }
            )
            self.message_bus.publish(message)
            
        logger.info(f"Coordinated collaboration on task {task['id']} with {len(agents)} agents")
        return plan
        
    def monitor_progress(self) -> Dict[str, Any]:
        """Monitor overall progress of all tasks"""
        return {
            "pending_tasks": len(self.task_queue.pending_tasks),
            "active_tasks": len(self.task_queue.active_tasks),
            "completed_tasks": len(self.task_queue.completed_tasks),
            "agent_loads": self.agent_load.copy(),
            "message_queue_size": len(self.message_bus.message_queue)
        }
        
    def _default_task_division(self, task: Dict[str, Any], num_agents: int) -> List[Dict[str, Any]]:
        """Default task division strategy"""
        # Simple division - in practice would be more sophisticated
        subtasks = []
        for i in range(num_agents):
            subtasks.append({
                "id": f"{task['id']}_subtask_{i}",
                "description": f"Subtask {i+1} of {task.get('name', 'task')}",
                "parent_task": task["id"]
            })
        return subtasks


class Orchestrator:
    """
    Main orchestration system that brings together all components
    
    Integrates:
    - Agent coordination
    - Message passing
    - Task management
    - Pattern application
    - Strategy execution
    """
    
    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    def create_session(self, session_id: str, agents: List[str]) -> Dict[str, Any]:
        """Create a new orchestration session"""
        session = {
            "id": session_id,
            "agents": agents,
            "tasks": [],
            "start_time": __import__('time').time(),
            "status": "active"
        }
        self.active_sessions[session_id] = session
        logger.info(f"Created orchestration session: {session_id}")
        return session
        
    def submit_task(self, session_id: str, task: Dict[str, Any]) -> str:
        """Submit a task to an orchestration session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
            
        # Add task to queue
        self.coordinator.task_queue.add_task(task)
        
        # Assign task to agent
        agent_id = self.coordinator.assign_task_to_agent(task)
        
        # Update session
        self.active_sessions[session_id]["tasks"].append(task["id"])
        
        logger.info(f"Task {task['id']} submitted to session {session_id}")
        return task["id"]
        
    def orchestrate_multi_agent_task(
        self, 
        session_id: str, 
        task: Dict[str, Any], 
        strategy: str = "collaborative"
    ) -> Dict[str, Any]:
        """
        Orchestrate a task across multiple agents
        
        Args:
            session_id: The session ID
            task: The task to orchestrate
            strategy: Orchestration strategy ("collaborative", "competitive", "sequential")
            
        Returns:
            Orchestration result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self.active_sessions[session_id]
        
        result = {
            "session_id": session_id,
            "task_id": task["id"],
            "strategy": strategy,
            "agents_involved": [],
            "execution_trace": [],
            "final_result": None
        }
        
        if strategy == "collaborative":
            # All agents work together on the task
            plan = self.coordinator.coordinate_collaboration(task, session["agents"])
            result["agents_involved"] = session["agents"]
            result["coordination_plan"] = plan
            
        elif strategy == "competitive":
            # Multiple agents work on the same task independently
            for agent_id in session["agents"]:
                self.coordinator.task_queue.add_task({**task, "id": f"{task['id']}_{agent_id}"})
                self.coordinator.assign_task_to_agent(task)
            result["agents_involved"] = session["agents"]
            
        elif strategy == "sequential":
            # Agents work on task in sequence
            result["agents_involved"] = session["agents"]
            result["execution_order"] = session["agents"]
            
        logger.info(f"Orchestrated multi-agent task {task['id']} with strategy: {strategy}")
        return result
        
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an orchestration session"""
        if session_id not in self.active_sessions:
            return None
            
        session = self.active_sessions[session_id]
        
        # Get task statuses
        task_statuses = {}
        for task_id in session["tasks"]:
            status = self.coordinator.task_queue.get_task_status(task_id)
            if status:
                task_statuses[task_id] = status
                
        return {
            "session_id": session_id,
            "status": session["status"],
            "agents": session["agents"],
            "tasks": task_statuses,
            "progress": self.coordinator.monitor_progress()
        }
        
    def close_session(self, session_id: str):
        """Close an orchestration session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["status"] = "closed"
            self.active_sessions[session_id]["end_time"] = __import__('time').time()
            logger.info(f"Closed orchestration session: {session_id}")
