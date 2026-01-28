# -*- coding: utf-8 -*-
"""
Load balancer for distributing requests across multiple model endpoints.

Supports multiple load balancing strategies:
- round_robin: Distribute requests evenly in a circular fashion
- random: Randomly select an endpoint
- least_connections: Select endpoint with fewest active connections (requires tracking)
- weighted_round_robin: Round robin with weights based on endpoint health
"""

import random
import threading
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger(__name__)


def is_full_url(host: str) -> bool:
    """Check if the host is a full URL (starts with http:// or https://)."""
    return host.startswith('http://') or host.startswith('https://')


def build_endpoint_url(host: str, port: int, path: str = "") -> str:
    """
    Build endpoint URL from host and port.
    
    Args:
        host: Host address (can be full URL or hostname)
        port: Port number (ignored if host is full URL)
        path: Optional path to append (e.g., "/v1")
    
    Returns:
        Full endpoint URL
    """
    if is_full_url(host):
        # Host is already a full URL, just append path if provided
        base_url = host.rstrip('/')
        return f"{base_url}{path}" if path else base_url
    else:
        # Build URL from host and port
        base_url = f"http://{host}:{port}"
        return f"{base_url}{path}" if path else base_url


@dataclass
class EndpointStats:
    """Statistics for a single endpoint."""
    host: str
    port: int
    active_connections: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    
    @property
    def endpoint(self) -> str:
        """Get the endpoint string."""
        return f"{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if endpoint is considered healthy."""
        # Consider unhealthy if 3+ consecutive failures in last 5 minutes
        if self.consecutive_failures >= 3:
            if self.last_failure and (datetime.now() - self.last_failure) < timedelta(minutes=5):
                return False
        return True
    
    @property
    def weight(self) -> float:
        """Calculate weight for weighted strategies."""
        if not self.is_healthy:
            return 0.0
        
        # Base weight is 1.0, reduced by failure rate
        if self.total_requests == 0:
            return 1.0
        
        failure_rate = self.total_failures / self.total_requests
        return max(0.1, 1.0 - failure_rate)


class LoadBalancer:
    """
    Load balancer for distributing requests across multiple endpoints.
    
    Thread-safe implementation supporting multiple load balancing strategies.
    """
    
    def __init__(self, strategy: str = "round_robin"):
        """
        Initialize the load balancer.
        
        Args:
            strategy: Load balancing strategy to use
                     Options: "round_robin", "random", "least_connections", "weighted_round_robin"
        """
        self.strategy = strategy
        self._lock = threading.Lock()
        self._endpoint_stats: Dict[str, Dict[str, EndpointStats]] = defaultdict(dict)
        self._round_robin_counters: Dict[str, int] = defaultdict(int)
        
        logger.info(f"Initialized load balancer with strategy: {strategy}")
    
    def get_endpoint(self, hosts: List[str], ports: List[int], model_name: str = "default") -> Tuple[str, int]:
        """
        Get the next endpoint to use based on the load balancing strategy.
        
        Args:
            hosts: List of host addresses (can be full URLs like https://example.com or host names)
            ports: List of port numbers (must match hosts length or be single value)
            model_name: Name of the model (used for tracking per-model stats)
        
        Returns:
            Tuple of (host, port) to use. If host is a full URL, port will be 0.
        
        Raises:
            ValueError: If no hosts provided or all endpoints are unhealthy
        """
        if not hosts:
            raise ValueError("No hosts provided for load balancing")
        
        # Handle single host case
        if len(hosts) == 1:
            port = ports[0] if ports else 8000
            return hosts[0], port
        
        # Normalize ports to match hosts length
        if len(ports) == 1:
            ports = ports * len(hosts)
        elif len(ports) != len(hosts):
            logger.warning(f"Ports length ({len(ports)}) doesn't match hosts length ({len(hosts)}), using first port")
            ports = [ports[0]] * len(hosts)
        
        # Initialize endpoint stats if not exists
        with self._lock:
            for host, port in zip(hosts, ports):
                endpoint_key = f"{host}:{port}"
                if endpoint_key not in self._endpoint_stats[model_name]:
                    self._endpoint_stats[model_name][endpoint_key] = EndpointStats(host=host, port=port)
        
        # Select endpoint based on strategy
        if self.strategy == "round_robin":
            return self._round_robin_select(hosts, ports, model_name)
        elif self.strategy == "random":
            return self._random_select(hosts, ports, model_name)
        elif self.strategy == "least_connections":
            return self._least_connections_select(hosts, ports, model_name)
        elif self.strategy == "weighted_round_robin":
            return self._weighted_round_robin_select(hosts, ports, model_name)
        else:
            logger.warning(f"Unknown strategy '{self.strategy}', falling back to round_robin")
            return self._round_robin_select(hosts, ports, model_name)
    
    def _round_robin_select(self, hosts: List[str], ports: List[int], model_name: str) -> Tuple[str, int]:
        """Round-robin selection strategy."""
        with self._lock:
            # Get healthy endpoints
            healthy_endpoints = self._get_healthy_endpoints(hosts, ports, model_name)
            if not healthy_endpoints:
                logger.warning(f"No healthy endpoints for {model_name}, using all endpoints")
                healthy_endpoints = list(zip(hosts, ports))
            
            # Get next index
            counter = self._round_robin_counters[model_name]
            index = counter % len(healthy_endpoints)
            self._round_robin_counters[model_name] = counter + 1
            
            host, port = healthy_endpoints[index]
            logger.debug(f"Round-robin selected {host}:{port} for {model_name} (index {index}/{len(healthy_endpoints)})")
            return host, port
    
    def _random_select(self, hosts: List[str], ports: List[int], model_name: str) -> Tuple[str, int]:
        """Random selection strategy."""
        with self._lock:
            # Get healthy endpoints
            healthy_endpoints = self._get_healthy_endpoints(hosts, ports, model_name)
            if not healthy_endpoints:
                logger.warning(f"No healthy endpoints for {model_name}, using all endpoints")
                healthy_endpoints = list(zip(hosts, ports))
            
            host, port = random.choice(healthy_endpoints)
            logger.debug(f"Random selected {host}:{port} for {model_name}")
            return host, port
    
    def _least_connections_select(self, hosts: List[str], ports: List[int], model_name: str) -> Tuple[str, int]:
        """Least connections selection strategy."""
        with self._lock:
            # Get healthy endpoints
            healthy_endpoints = self._get_healthy_endpoints(hosts, ports, model_name)
            if not healthy_endpoints:
                logger.warning(f"No healthy endpoints for {model_name}, using all endpoints")
                healthy_endpoints = list(zip(hosts, ports))
            
            # Find endpoint with least active connections
            min_connections = float('inf')
            selected = healthy_endpoints[0]
            
            for host, port in healthy_endpoints:
                endpoint_key = f"{host}:{port}"
                stats = self._endpoint_stats[model_name][endpoint_key]
                if stats.active_connections < min_connections:
                    min_connections = stats.active_connections
                    selected = (host, port)
            
            logger.debug(f"Least-connections selected {selected[0]}:{selected[1]} for {model_name} ({min_connections} active)")
            return selected
    
    def _weighted_round_robin_select(self, hosts: List[str], ports: List[int], model_name: str) -> Tuple[str, int]:
        """Weighted round-robin selection strategy based on endpoint health."""
        with self._lock:
            # Get healthy endpoints with weights
            healthy_endpoints = self._get_healthy_endpoints(hosts, ports, model_name)
            if not healthy_endpoints:
                logger.warning(f"No healthy endpoints for {model_name}, using all endpoints")
                healthy_endpoints = list(zip(hosts, ports))
            
            # Calculate weights for each endpoint
            weights = []
            for host, port in healthy_endpoints:
                endpoint_key = f"{host}:{port}"
                stats = self._endpoint_stats[model_name][endpoint_key]
                weights.append(stats.weight)
            
            # If all weights are 0, use equal weights
            if sum(weights) == 0:
                weights = [1.0] * len(weights)
            
            # Select based on weights using weighted random selection
            selected = random.choices(healthy_endpoints, weights=weights, k=1)[0]
            logger.debug(f"Weighted-round-robin selected {selected[0]}:{selected[1]} for {model_name}")
            return selected
    
    def _get_healthy_endpoints(self, hosts: List[str], ports: List[int], model_name: str) -> List[Tuple[str, int]]:
        """Get list of healthy endpoints."""
        healthy = []
        for host, port in zip(hosts, ports):
            endpoint_key = f"{host}:{port}"
            stats = self._endpoint_stats[model_name][endpoint_key]
            if stats.is_healthy:
                healthy.append((host, port))
        return healthy
    
    def mark_request_start(self, host: str, port: int, model_name: str = "default") -> None:
        """
        Mark the start of a request to an endpoint.
        
        Args:
            host: Host address
            port: Port number
            model_name: Name of the model
        """
        with self._lock:
            endpoint_key = f"{host}:{port}"
            if endpoint_key in self._endpoint_stats[model_name]:
                stats = self._endpoint_stats[model_name][endpoint_key]
                stats.active_connections += 1
                stats.total_requests += 1
                logger.debug(f"Request start: {endpoint_key} ({stats.active_connections} active)")
    
    def mark_request_end(self, host: str, port: int, model_name: str = "default", success: bool = True) -> None:
        """
        Mark the end of a request to an endpoint.
        
        Args:
            host: Host address
            port: Port number
            model_name: Name of the model
            success: Whether the request was successful
        """
        with self._lock:
            endpoint_key = f"{host}:{port}"
            if endpoint_key in self._endpoint_stats[model_name]:
                stats = self._endpoint_stats[model_name][endpoint_key]
                stats.active_connections = max(0, stats.active_connections - 1)
                
                if not success:
                    stats.total_failures += 1
                    stats.consecutive_failures += 1
                    stats.last_failure = datetime.now()
                    logger.warning(f"Request failed: {endpoint_key} ({stats.consecutive_failures} consecutive failures)")
                else:
                    stats.consecutive_failures = 0
                
                logger.debug(f"Request end: {endpoint_key} ({stats.active_connections} active, success={success})")
    
    def get_stats(self, model_name: str = "default") -> Dict[str, Dict[str, any]]:
        """
        Get statistics for all endpoints of a model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Dictionary of endpoint to stats
        """
        with self._lock:
            stats = {}
            for endpoint_key, endpoint_stats in self._endpoint_stats[model_name].items():
                stats[endpoint_key] = {
                    'active_connections': endpoint_stats.active_connections,
                    'total_requests': endpoint_stats.total_requests,
                    'total_failures': endpoint_stats.total_failures,
                    'consecutive_failures': endpoint_stats.consecutive_failures,
                    'is_healthy': endpoint_stats.is_healthy,
                    'weight': endpoint_stats.weight,
                    'last_failure': endpoint_stats.last_failure.isoformat() if endpoint_stats.last_failure else None
                }
            return stats
    
    def reset_stats(self, model_name: Optional[str] = None) -> None:
        """
        Reset statistics for a model or all models.
        
        Args:
            model_name: Name of the model to reset, or None to reset all
        """
        with self._lock:
            if model_name:
                if model_name in self._endpoint_stats:
                    self._endpoint_stats[model_name].clear()
                    self._round_robin_counters[model_name] = 0
                    logger.info(f"Reset stats for {model_name}")
            else:
                self._endpoint_stats.clear()
                self._round_robin_counters.clear()
                logger.info("Reset all stats")


# Global load balancer instance
_global_load_balancer: Optional[LoadBalancer] = None
_lb_lock = threading.Lock()


def get_load_balancer(strategy: str = "round_robin") -> LoadBalancer:
    """
    Get the global load balancer instance.
    
    Args:
        strategy: Load balancing strategy (only used on first call)
    
    Returns:
        Global LoadBalancer instance
    """
    global _global_load_balancer
    
    if _global_load_balancer is None:
        with _lb_lock:
            if _global_load_balancer is None:
                _global_load_balancer = LoadBalancer(strategy=strategy)
    
    return _global_load_balancer


def select_endpoint(hosts: List[str], ports: List[int], model_name: str = "default") -> Tuple[str, int]:
    """
    Convenience function to select an endpoint using the global load balancer.
    
    Args:
        hosts: List of host addresses
        ports: List of port numbers
        model_name: Name of the model
    
    Returns:
        Tuple of (host, port) to use
    """
    lb = get_load_balancer()
    return lb.get_endpoint(hosts, ports, model_name)
