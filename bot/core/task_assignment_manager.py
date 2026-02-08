"""
Task Assignment Manager for load balancing and node management

Implements:
- Task-to-node assignment
- Load balancing strategies
- Node selection and health tracking
- Assignment tracking
"""

import random
from typing import Dict, List, Optional, Set

from .task_models import (
    Task,
    TaskAssignment,
    TaskDependency,
    TaskState,
)


class TaskAssignmentManager:
    """
    Manages task assignments to nodes
    
    Responsible for:
    - Node selection and load balancing
    - Task assignment tracking
    - Load balancing strategy implementation
    - Dependency validation
    """
    
    def __init__(self):
        self.assignments: Dict[str, TaskAssignment] = {}
        self.peers: Set[str] = set()
        self.node_id = ""
        self.load_balance_strategy = "least_loaded"
        self.tasks: Dict[str, Task] = {}
    
    async def select_target_node(self, task: Task) -> Optional[str]:
        """Select best node for task"""
        if not self.peers:
            return self.node_id
        
        try:
            if self.load_balance_strategy == "least_loaded":
                # Select node with lowest utilization
                best_node = self.node_id
                min_util = 0.5
                
                for peer in self.peers:
                    # In real implementation, query peer for utilization
                    util = 0.3
                    if util < min_util:
                        min_util = util
                        best_node = peer
                
                return best_node
            
            else:  # round_robin, random, etc.
                nodes = [self.node_id] + list(self.peers)
                return random.choice(nodes)
        except Exception:
            return self.node_id
    
    async def assign_task(self, task: Task, node_id: str) -> bool:
        """Assign task to node"""
        try:
            task.state = TaskState.ASSIGNED
            task.assigned_node = node_id
            
            assignment = TaskAssignment(
                task_id=task.task_id,
                node_id=node_id
            )
            self.assignments[assignment.assignment_id] = assignment
            
            return True
        except Exception:
            return False
    
    async def check_dependencies(self, task: Task) -> bool:
        """Check if all task dependencies are satisfied"""
        for dep in task.dependencies:
            if dep.task_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep.task_id]
            if dep.must_complete_before:
                if dep_task.state != TaskState.COMPLETED:
                    return False
        
        return True
    
    def set_node_info(self, node_id: str, peers: Set[str]) -> None:
        """Set local node and peer information"""
        self.node_id = node_id
        self.peers = peers
    
    def set_task_reference(self, tasks: Dict[str, Task]) -> None:
        """Set reference to tasks dict"""
        self.tasks = tasks
    
    def set_load_balance_strategy(self, strategy: str) -> None:
        """Set load balancing strategy"""
        if strategy in ["least_loaded", "round_robin", "random"]:
            self.load_balance_strategy = strategy
    
    def register_peer(self, peer_id: str) -> bool:
        """Register peer node"""
        try:
            self.peers.add(peer_id)
            return True
        except Exception:
            return False
    
    def get_assignment(self, assignment_id: str) -> Optional[TaskAssignment]:
        """Get assignment by ID"""
        return self.assignments.get(assignment_id)
    
    def get_task_assignment(self, task_id: str) -> Optional[TaskAssignment]:
        """Get assignment for task"""
        for assignment in self.assignments.values():
            if assignment.task_id == task_id:
                return assignment
        return None
