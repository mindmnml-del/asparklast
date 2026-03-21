"""
Circuit breakers for external service calls (Vertex AI Search, Gemini).
Prevents cascading failures when upstream services are degraded.
"""

import logging
import pybreaker

logger = logging.getLogger(__name__)


class LoggingListener(pybreaker.CircuitBreakerListener):
    """Logs circuit breaker state transitions and failures."""

    def state_change(self, cb, old_state, new_state):
        logger.warning(
            "Circuit breaker '%s': %s -> %s", cb.name, old_state.name, new_state.name
        )

    def failure(self, cb, exc):
        logger.warning("Circuit breaker '%s' recorded failure: %s", cb.name, exc)


_listener = LoggingListener()

# Vertex Search: 5 failures -> open for 30 seconds
vertex_search_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="vertex_search",
    listeners=[_listener],
)

# Gemini generation: 3 failures -> open for 60 seconds
gemini_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    name="gemini_generation",
    listeners=[_listener],
)
