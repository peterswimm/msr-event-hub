"""
Load Testing for MSR Event Hub Chat API

MVP Target: 1000 concurrent users @ 2 rps for 30 minutes, p99 < 2s

Usage:
    # Install: pip install locust
    # Run: locust -f tests/load/locustfile.py --host=http://localhost:8000
    # Web UI: http://localhost:8089
    # MVP test: 1000 users, spawn rate 10/sec, run 30 min
"""

from locust import HttpUser, task, between, events
import json
import random
import time

# Sample queries representing real usage patterns
SAMPLE_QUERIES = [
    "Show me AI projects",
    "What projects are about machine learning?",
    "Find projects by John Smith",
    "What's happening now?",
    "Show me sessions at 2:30 PM",
    "Which projects need large displays?",
    "Recording link for Healthcare AI project",
    "Projects in HCI category",
    "What are the most popular projects?",
    "Show me similar projects to quantum computing",
]

# Card actions
SAMPLE_ACTIONS = [
    {"action": "browse_all"},
    {"action": "category_select", "category": "AI"},
    {"action": "filter_by_area", "area": "Systems"},
]


class ChatUser(HttpUser):
    """Simulates a user interacting with the chat API."""
    
    # MVP requirement: 2 requests per second per user
    wait_time = between(0.4, 0.6)  # Average 0.5s = 2 rps
    
    def on_start(self):
        """Called when a user starts - check health."""
        self.client.get("/api/chat/health")
    
    @task(10)
    def stream_chat_natural_language(self):
        """Natural language chat queries (70% of traffic)."""
        query = random.choice(SAMPLE_QUERIES)
        
        payload = {
            "messages": [
                {"role": "user", "content": query}
            ],
            "temperature": 0.3,
            "max_tokens": 400
        }
        
        # Stream endpoint
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/api/chat/stream [query]"
        ) as response:
            if response.status_code == 200:
                # Consume stream
                for line in response.iter_lines():
                    if line and line.startswith(b"data: [DONE]"):
                        break
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)
    def stream_chat_card_action(self):
        """Card action requests (30% of traffic)."""
        action = random.choice(SAMPLE_ACTIONS)
        
        payload = {
            "messages": [
                {"role": "user", "content": json.dumps(action)}
            ]
        }
        
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/api/chat/stream [action]"
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line and line.startswith(b"data: [DONE]"):
                        break
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def get_welcome(self):
        """Fetch welcome card."""
        self.client.get("/api/chat/welcome")
    
    @task(1)
    def submit_feedback(self):
        """Submit user feedback."""
        feedback = {
            "query": random.choice(SAMPLE_QUERIES),
            "feedback": random.choice(["positive", "negative"])
        }
        
        self.client.post(
            "/api/chat/intent-feedback",
            json=feedback,
            headers={"Content-Type": "application/json"},
            name="/api/chat/intent-feedback"
        )
    
    @task(1)
    def get_metrics(self):
        """Check routing quality metrics."""
        self.client.get("/api/chat/metrics/routing-quality")


class StressTestUser(HttpUser):
    """High-load stress test user (use separately from normal load test)."""
    
    wait_time = between(0.1, 0.2)  # 5-10 rps per user
    
    @task
    def rapid_fire_queries(self):
        """Rapid-fire queries to stress test rate limiting."""
        query = random.choice(SAMPLE_QUERIES)
        
        payload = {
            "messages": [{"role": "user", "content": query}]
        }
        
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            catch_response=True,
            name="/api/chat/stream [stress]"
        ) as response:
            if response.status_code == 429:
                # Rate limit expected under stress
                response.success()
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")


# Custom metrics reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("=" * 60)
    print("🚀 MSR Event Hub Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.parsed_options.num_users} users @ ~2 rps")
    print(f"Run time: {environment.parsed_options.run_time or 'manual stop'}")
    print(f"Host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion and results."""
    stats = environment.stats
    
    print("\n" + "=" * 60)
    print("✅ Load Test Complete")
    print("=" * 60)
    
    # Check MVP requirements
    p99_latency = stats.total.get_response_time_percentile(0.99)
    success_rate = (stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100
    
    print(f"📊 Results:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Failures: {stats.total.num_failures}")
    print(f"  Success Rate: {success_rate:.2f}%")
    print(f"  P50 Latency: {stats.total.get_response_time_percentile(0.50):.0f}ms")
    print(f"  P95 Latency: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99 Latency: {p99_latency:.0f}ms")
    print(f"  RPS: {stats.total.total_rps:.2f}")
    print()
    
    # MVP validation
    print("🎯 MVP Requirements Check:")
    print(f"  P99 < 2000ms: {'✅ PASS' if p99_latency < 2000 else '❌ FAIL'} ({p99_latency:.0f}ms)")
    print(f"  Success Rate > 99%: {'✅ PASS' if success_rate > 99 else '❌ FAIL'} ({success_rate:.2f}%)")
    print(f"  RPS Target (~2000): {'✅ PASS' if stats.total.total_rps > 1800 else '⚠️ LOW'} ({stats.total.total_rps:.0f})")
    print("=" * 60)
