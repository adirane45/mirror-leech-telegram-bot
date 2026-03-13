"""
API Gateway Router for request routing and load balancing
"""

import asyncio
import random
from datetime import UTC, datetime
from typing import Any, Callable, Dict, List, Optional

from .api_gateway_models import ApiGatewayListener, ApiRequest, ApiResponse, CircuitState, RouteConfig


class ApiGatewayRouter:
    """
    Routes requests to appropriate nodes

    Responsible for:
    - Route configuration and registration
    - Node management
    - Request routing logic
    - Load balancing decisions
    """

    def __init__(self) -> None:
        self.routes: Dict[str, RouteConfig] = {}
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.listeners: List[ApiGatewayListener] = []
        self.enabled = False
        self.node_id = ""

    async def register_route(self, route: RouteConfig) -> bool:
        """Register a route"""
        if not self.enabled:
            return False
        try:
            self.routes[route.path] = route
            return True
        except Exception:
            return False

    async def register_node(self, node_id: str, meta: Optional[Dict[str, Any]] = None) -> bool:
        """Register target node"""
        if not self.enabled:
            return False
        try:
            self.nodes[node_id] = meta or {
                "registered_at": datetime.now(UTC).isoformat()
            }
            return True
        except Exception:
            return False

    async def get_route(self, path: str) -> Optional[RouteConfig]:
        """Get a registered route (exact or longest prefix match)"""
        if not self.routes:
            return None
        if path in self.routes:
            return self.routes[path]

        matched = None
        for route_path, route in self.routes.items():
            if path.startswith(route_path):
                if matched is None or len(route_path) > len(matched.path):
                    matched = route
        return matched

    async def select_node(
        self,
        route: RouteConfig,
        circuit_states: Optional[Dict[str, CircuitState]] = None,
    ) -> Optional[str]:
        """Select target node for route"""
        if not self.enabled:
            return None

        if route.target_node:
            return route.target_node if route.target_node in self.nodes else None

        if not self.nodes:
            return None

        available = list(self.nodes.keys())
        if circuit_states:
            available = [
                node_id
                for node_id in available
                if circuit_states.get(node_id) != CircuitState.OPEN
            ]

        if not available:
            return None

        return random.choice(available)

    async def route_request(
        self,
        request: ApiRequest,
        target_node: str,
        get_circuit_state_fn: Optional[Callable[[str], Optional[CircuitState]]] = None,
    ) -> ApiResponse:
        """Process request routing"""
        try:
            for listener in self.listeners:
                await listener.on_request_routed(request, target_node)
            response = await self._process_request(request, target_node)
            return response
        except Exception as e:
            return ApiResponse(
                request_id=request.request_id,
                status_code=500,
                body=f"Routing error: {str(e)}",
            )

    async def _process_request(self, request: ApiRequest, target_node: str) -> ApiResponse:
        """Process request (simulated)"""
        await asyncio.sleep(0.01)
        return ApiResponse(
            request_id=request.request_id,
            status_code=200,
            body={"message": "Success", "node": target_node},
        )

    def set_enabled(self, enabled: bool) -> None:
        """Set router enabled state"""
        self.enabled = enabled

    def set_node_info(self, node_id: str) -> None:
        """Set local node info"""
        self.node_id = node_id

    def add_listener(self, listener: ApiGatewayListener) -> None:
        """Add router listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def get_all_routes(self) -> Dict[str, RouteConfig]:
        """Get all registered routes"""
        return self.routes.copy()

    def get_all_nodes(self) -> List[str]:
        """Get all registered nodes"""
        return list(self.nodes.keys())
