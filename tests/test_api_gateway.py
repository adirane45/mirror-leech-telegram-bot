"""
Test suite for API Gateway
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from bot.core.api_gateway import (
    ApiGateway, ApiRequest, ApiResponse, RouteConfig, RateLimitConfig,
    CircuitBreakerConfig, GatewayMetrics, ApiGatewayListener,
    RequestMethod, CircuitState
)


class MockGatewayListener(ApiGatewayListener):
    """Test listener implementation"""
    
    def __init__(self):
        self.requests_received = []
        self.requests_routed = []
        self.responses_sent = []
        self.rate_limits_exceeded = []
    
    async def on_request_received(self, request: ApiRequest) -> None:
        self.requests_received.append(request.request_id)
    
    async def on_request_routed(self, request: ApiRequest, target_node: str) -> None:
        self.requests_routed.append((request.request_id, target_node))
    
    async def on_response_sent(self, response: ApiResponse) -> None:
        self.responses_sent.append(response.request_id)
    
    async def on_rate_limit_exceeded(self, client_id: str) -> None:
        self.rate_limits_exceeded.append(client_id)


@pytest.fixture
def api_gateway():
    """Get API gateway instance"""
    gateway = ApiGateway.get_instance()
    # Reset state
    gateway.enabled = False
    gateway.node_id = ""
    gateway.routes.clear()
    gateway.nodes.clear()
    gateway.request_history.clear()
    gateway.circuit_states.clear()
    gateway.circuit_failures.clear()
    gateway.circuit_successes.clear()
    gateway.listeners.clear()
    gateway.auth_tokens.clear()
    gateway.metrics = GatewayMetrics()
    gateway.default_rate_limit = RateLimitConfig()
    gateway.default_circuit_breaker = CircuitBreakerConfig()
    
    yield gateway
    
    # Cleanup
    try:
        asyncio.run(gateway.stop())
    except:
        pass
    gateway.enabled = False


class TestApiGatewayBasic:
    """Test basic gateway functionality"""
    
    @pytest.mark.asyncio
    async def test_singleton_instance(self, api_gateway):
        """Test singleton pattern"""
        g1 = ApiGateway.get_instance()
        g2 = ApiGateway.get_instance()
        assert g1 is g2
    
    @pytest.mark.asyncio
    async def test_start_stop(self, api_gateway):
        """Test start and stop"""
        gateway = api_gateway
        assert not gateway.enabled
        
        assert await gateway.start("gateway1")
        assert gateway.enabled
        assert gateway.node_id == "gateway1"
        
        assert await gateway.stop()
        assert not gateway.enabled
    
    @pytest.mark.asyncio
    async def test_is_enabled(self, api_gateway):
        """Test is_enabled check"""
        gateway = api_gateway
        assert not await gateway.is_enabled()
        
        await gateway.start()
        assert await gateway.is_enabled()


class TestRouting:
    """Test request routing"""
    
    @pytest.mark.asyncio
    async def test_register_route(self, api_gateway):
        """Test registering route"""
        gateway = api_gateway
        await gateway.start()
        
        route = RouteConfig(path="/api/test")
        assert await gateway.register_route(route)
        assert "/api/test" in gateway.routes
    
    @pytest.mark.asyncio
    async def test_register_node(self, api_gateway):
        """Test registering node"""
        gateway = api_gateway
        await gateway.start()
        
        assert await gateway.register_node("node1")
        assert "node1" in gateway.nodes
        assert gateway.circuit_states["node1"] == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_route_simple_request(self, api_gateway):
        """Test routing simple request"""
        gateway = api_gateway
        await gateway.start()
        
        # Register route and node
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Route request
        request = ApiRequest(method=RequestMethod.GET, path="/test")
        response = await gateway.route_request(request)
        
        assert response.status_code == 200
        assert gateway.metrics.total_requests == 1
        assert gateway.metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_route_not_found(self, api_gateway):
        """Test routing to non-existent route"""
        gateway = api_gateway
        await gateway.start()
        
        request = ApiRequest(path="/nonexistent")
        response = await gateway.route_request(request)
        
        assert response.status_code == 404
        assert gateway.metrics.failed_requests == 1
    
    @pytest.mark.asyncio
    async def test_route_when_disabled(self, api_gateway):
        """Test routing when gateway disabled"""
        gateway = api_gateway
        
        request = ApiRequest(path="/test")
        response = await gateway.route_request(request)
        
        assert response.status_code == 503


class TestRateLimiting:
    """Test rate limiting"""
    
    @pytest.mark.asyncio
    async def test_set_rate_limit(self, api_gateway):
        """Test setting rate limit"""
        gateway = api_gateway
        await gateway.start()
        
        assert await gateway.set_rate_limit(10, 60)
        assert gateway.default_rate_limit.max_requests == 10
        assert gateway.default_rate_limit.window_seconds == 60
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, api_gateway):
        """Test rate limit enforcement"""
        gateway = api_gateway
        await gateway.start()
        
        # Set low rate limit
        await gateway.set_rate_limit(2, 60)
        
        # Register route
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Send requests until rate limited
        client_id = "client1"
        responses = []
        for _ in range(4):
            request = ApiRequest(path="/test", client_id=client_id)
            response = await gateway.route_request(request)
            responses.append(response)
        
        # First 2 should succeed, rest should be rate limited
        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        assert responses[2].status_code == 429
        assert gateway.metrics.rate_limited_requests >= 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_per_client(self, api_gateway):
        """Test rate limiting is per client"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.set_rate_limit(1, 60)
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Different clients should have independent limits
        req1 = ApiRequest(path="/test", client_id="client1")
        req2 = ApiRequest(path="/test", client_id="client2")
        
        resp1 = await gateway.route_request(req1)
        resp2 = await gateway.route_request(req2)
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200


class TestCircuitBreaker:
    """Test circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_circuit_initially_closed(self, api_gateway):
        """Test circuit starts closed"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_node("node1")
        state = await gateway.get_circuit_state("node1")
        assert state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_record_failure(self, api_gateway):
        """Test recording failures"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_node("node1")
        
        # Record failures
        for _ in range(5):
            await gateway._record_failure("node1")
        
        # Circuit should open after threshold
        state = await gateway.get_circuit_state("node1")
        assert state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_record_success(self, api_gateway):
        """Test recording successes"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_node("node1")
        gateway.circuit_states["node1"] = CircuitState.HALF_OPEN
        
        # Record successes
        for _ in range(2):
            await gateway._record_success("node1")
        
        # Circuit should close
        state = await gateway.get_circuit_state("node1")
        assert state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_blocks_requests(self, api_gateway):
        """Test open circuit blocks requests"""
        gateway = api_gateway
        await gateway.start()
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Open circuit
        gateway.circuit_states["node1"] = CircuitState.OPEN
        
        # Request should be blocked
        request = ApiRequest(path="/test")
        response = await gateway.route_request(request)
        
        assert response.status_code == 503
        assert gateway.metrics.circuit_open_count > 0


class TestAuthentication:
    """Test authentication"""
    
    @pytest.mark.asyncio
    async def test_register_auth_token(self, api_gateway):
        """Test registering auth token"""
        gateway = api_gateway
        await gateway.start()
        
        assert await gateway.register_auth_token("token123")
        assert "token123" in gateway.auth_tokens
    
    @pytest.mark.asyncio
    async def test_check_auth(self, api_gateway):
        """Test authentication check"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_auth_token("valid_token")
        
        assert await gateway._check_auth("valid_token")
        assert not await gateway._check_auth("invalid_token")
    
    @pytest.mark.asyncio
    async def test_route_requires_auth(self, api_gateway):
        """Test route requiring authentication"""
        gateway = api_gateway
        await gateway.start()
        
        # Register route requiring auth
        route = RouteConfig(
            path="/secure",
            target_node="node1",
            requires_auth=True
        )
        await gateway.register_route(route)
        await gateway.register_node("node1")
        await gateway.register_auth_token("valid_token")
        
        # Request without auth should fail
        req1 = ApiRequest(path="/secure")
        resp1 = await gateway.route_request(req1)
        assert resp1.status_code == 401
        
        # Request with valid auth should succeed
        req2 = ApiRequest(
            path="/secure",
            headers={"Authorization": "valid_token"}
        )
        resp2 = await gateway.route_request(req2)
        assert resp2.status_code == 200


class TestMetrics:
    """Test metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, api_gateway):
        """Test getting metrics"""
        gateway = api_gateway
        await gateway.start()
        
        metrics = await gateway.get_metrics()
        assert metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_metrics_updates(self, api_gateway):
        """Test metrics update on requests"""
        gateway = api_gateway
        await gateway.start()
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Send request
        request = ApiRequest(path="/test")
        await gateway.route_request(request)
        
        metrics = await gateway.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_metrics_serialization(self, api_gateway):
        """Test metrics can be serialized"""
        gateway = api_gateway
        await gateway.start()
        
        metrics = await gateway.get_metrics()
        data = metrics.to_dict()
        
        assert 'total_requests' in data
        assert 'successful_requests' in data
        assert 'last_updated' in data


class TestListeners:
    """Test gateway listeners"""
    
    @pytest.mark.asyncio
    async def test_add_listener(self, api_gateway):
        """Test adding listener"""
        gateway = api_gateway
        await gateway.start()
        
        listener = MockGatewayListener()
        assert await gateway.add_listener(listener)
        assert listener in gateway.listeners
    
    @pytest.mark.asyncio
    async def test_listener_on_request_received(self, api_gateway):
        """Test listener on request received"""
        gateway = api_gateway
        await gateway.start()
        
        listener = MockGatewayListener()
        await gateway.add_listener(listener)
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        request = ApiRequest(path="/test", request_id="req123")
        await gateway.route_request(request)
        
        await asyncio.sleep(0.1)
        assert "req123" in listener.requests_received
    
    @pytest.mark.asyncio
    async def test_listener_on_response_sent(self, api_gateway):
        """Test listener on response sent"""
        gateway = api_gateway
        await gateway.start()
        
        listener = MockGatewayListener()
        await gateway.add_listener(listener)
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        request = ApiRequest(path="/test", request_id="req123")
        await gateway.route_request(request)
        
        await asyncio.sleep(0.1)
        assert "req123" in listener.responses_sent


class TestRequestResponse:
    """Test request/response handling"""
    
    def test_request_serialization(self):
        """Test request serialization"""
        request = ApiRequest(
            method=RequestMethod.POST,
            path="/api/test",
            client_id="client1"
        )
        
        data = request.to_dict()
        assert data['method'] == "POST"
        assert data['path'] == "/api/test"
        assert data['client_id'] == "client1"
    
    def test_response_serialization(self):
        """Test response serialization"""
        response = ApiResponse(
            request_id="req123",
            status_code=200,
            processing_time_ms=50
        )
        
        data = response.to_dict()
        assert data['request_id'] == "req123"
        assert data['status_code'] == 200
        assert data['processing_time_ms'] == 50


class TestLoadBalancing:
    """Test load balancing"""
    
    @pytest.mark.asyncio
    async def test_select_node_with_load_balancer(self, api_gateway):
        """Test node selection with load balancing"""
        gateway = api_gateway
        await gateway.start()
        
        # Register multiple nodes
        await gateway.register_node("node1")
        await gateway.register_node("node2")
        await gateway.register_node("node3")
        
        route = RouteConfig(path="/test", use_load_balancer=True)
        
        node = await gateway._select_node(route)
        assert node in ["node1", "node2", "node3"]
    
    @pytest.mark.asyncio
    async def test_select_specific_node(self, api_gateway):
        """Test selecting specific target node"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_node("node1")
        await gateway.register_node("node2")
        
        route = RouteConfig(path="/test", target_node="node1")
        
        node = await gateway._select_node(route)
        assert node == "node1"
    
    @pytest.mark.asyncio
    async def test_skip_open_circuit_nodes(self, api_gateway):
        """Test load balancer skips nodes with open circuits"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.register_node("node1")
        await gateway.register_node("node2")
        
        # Open circuit on node1
        gateway.circuit_states["node1"] = CircuitState.OPEN
        
        route = RouteConfig(path="/test", use_load_balancer=True)
        
        # Should select node2 (node1 has open circuit)
        node = await gateway._select_node(route)
        assert node == "node2"


class TestConcurrency:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_gateway):
        """Test concurrent request handling"""
        gateway = api_gateway
        await gateway.start()
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Send concurrent requests
        requests = [
            ApiRequest(path="/test", request_id=f"req{i}")
            for i in range(10)
        ]
        
        responses = await asyncio.gather(*[
            gateway.route_request(req) for req in requests
        ])
        
        assert len(responses) == 10
        assert all(r.status_code == 200 for r in responses)
        assert gateway.metrics.total_requests == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_node_registration(self, api_gateway):
        """Test concurrent node registration"""
        gateway = api_gateway
        await gateway.start()
        
        # Register nodes concurrently
        results = await asyncio.gather(*[
            gateway.register_node(f"node{i}")
            for i in range(5)
        ])
        
        assert all(results)
        assert len(gateway.nodes) == 5


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_route_with_no_nodes(self, api_gateway):
        """Test routing when no nodes available"""
        gateway = api_gateway
        await gateway.start()
        
        route = RouteConfig(path="/test", use_load_balancer=True)
        await gateway.register_route(route)
        
        request = ApiRequest(path="/test")
        response = await gateway.route_request(request)
        
        assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_rate_limit_without_client_id(self, api_gateway):
        """Test rate limiting without client ID"""
        gateway = api_gateway
        await gateway.start()
        
        await gateway.set_rate_limit(1, 60)
        
        route = RouteConfig(path="/test", target_node="node1")
        await gateway.register_route(route)
        await gateway.register_node("node1")
        
        # Requests without client_id should not be rate limited
        req1 = ApiRequest(path="/test")  # No client_id
        req2 = ApiRequest(path="/test")
        
        resp1 = await gateway.route_request(req1)
        resp2 = await gateway.route_request(req2)
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200
