"""Phase E API Examples - Working code samples for all components.

This file demonstrates how to use all Phase E endpoints:
- E1: Database, Authentication, Configuration, Monitoring
- E2: Async Job Execution
- E3: Analytics & Metrics
- E4: Knowledge Graph
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


# ============================================================================
# PHASE E1: FOUNDATION COMPONENTS
# ============================================================================

class E1Examples:
    """E1 Examples: Database, Auth, Config, Monitoring."""
    
    @staticmethod
    def user_registration() -> Dict[str, Any]:
        """Example: Register a new user."""
        payload = {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "SecurePass123!"
        }
        response = requests.post(f"{BASE_URL}/api/users/register", json=payload)
        print(f"Register User: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    
    @staticmethod
    def user_login() -> Dict[str, Any]:
        """Example: Login user and get JWT token."""
        payload = {
            "username": "john_doe",
            "password": "SecurePass123!"
        }
        response = requests.post(f"{BASE_URL}/api/users/login", json=payload)
        print(f"Login User: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_current_user(token: str) -> Dict[str, Any]:
        """Example: Get current user profile."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        print(f"Get Current User: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    
    @staticmethod
    def check_health() -> Dict[str, Any]:
        """Example: Health check endpoint."""
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Example: Get system metrics."""
        response = requests.get(f"{BASE_URL}/api/metrics")
        print(f"Get Metrics: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()


# ============================================================================
# PHASE E2: ASYNC JOB EXECUTION
# ============================================================================

class E2Examples:
    """E2 Examples: Async Job Execution with Celery."""
    
    @staticmethod
    def enqueue_project_evaluation(token: str, project_id: str) -> Dict[str, Any]:
        """Example: Enqueue a project evaluation job."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "project_id": project_id,
            "depth": 2,
            "include_dependencies": True
        }
        response = requests.post(
            f"{BASE_URL}/api/async/evaluate",
            json=payload,
            headers=headers
        )
        print(f"Enqueue Evaluation: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def enqueue_batch_processing(token: str, artifact_ids: list) -> Dict[str, Any]:
        """Example: Enqueue batch processing job."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "artifact_ids": artifact_ids,
            "batch_size": 50
        }
        response = requests.post(
            f"{BASE_URL}/api/async/batch-process",
            json=payload,
            headers=headers
        )
        print(f"Enqueue Batch: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def enqueue_report_generation(token: str, format: str = "pdf") -> Dict[str, Any]:
        """Example: Enqueue report generation job."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "report_type": "comprehensive",
            "format": format,
            "include_graphs": True
        }
        response = requests.post(
            f"{BASE_URL}/api/async/generate-report",
            json=payload,
            headers=headers
        )
        print(f"Enqueue Report: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_job_status(token: str, job_id: str) -> Dict[str, Any]:
        """Example: Get job status."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/async/jobs/{job_id}",
            headers=headers
        )
        print(f"Get Job Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def list_jobs(token: str, status: str = None) -> Dict[str, Any]:
        """Example: List all jobs."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{BASE_URL}/api/async/jobs",
            headers=headers,
            params=params
        )
        print(f"List Jobs: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def cancel_job(token: str, job_id: str) -> Dict[str, Any]:
        """Example: Cancel a running job."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(
            f"{BASE_URL}/api/async/jobs/{job_id}",
            headers=headers
        )
        print(f"Cancel Job: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def check_async_health(token: str) -> Dict[str, Any]:
        """Example: Check async execution health."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/async/health",
            headers=headers
        )
        print(f"Async Health: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result


# ============================================================================
# PHASE E3: ANALYTICS & METRICS
# ============================================================================

class E3Examples:
    """E3 Examples: Analytics, Metrics, Dashboards."""
    
    @staticmethod
    def record_metric(token: str, metric_name: str, value: float) -> Dict[str, Any]:
        """Example: Record a metric."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "metric_name": metric_name,
            "value": value,
            "tags": {
                "environment": "production",
                "service": "evaluation"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/analytics/metrics",
            json=payload,
            headers=headers
        )
        print(f"Record Metric: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_metric_history(token: str, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Example: Get metric history."""
        headers = {"Authorization": f"Bearer {token}"}
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/metrics/{metric_name}/history",
            headers=headers,
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        print(f"Get Metric History: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_realtime_dashboard(token: str) -> Dict[str, Any]:
        """Example: Get realtime dashboard data."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/dashboards/realtime",
            headers=headers
        )
        print(f"Realtime Dashboard: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_performance_dashboard(token: str) -> Dict[str, Any]:
        """Example: Get performance dashboard."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/dashboards/performance",
            headers=headers
        )
        print(f"Performance Dashboard: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_health_dashboard(token: str) -> Dict[str, Any]:
        """Example: Get health dashboard."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/dashboards/health",
            headers=headers
        )
        print(f"Health Dashboard: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_daily_report(token: str, date: str = None) -> Dict[str, Any]:
        """Example: Get daily report."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if date:
            params["date"] = date
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/reports/daily",
            headers=headers,
            params=params
        )
        print(f"Daily Report: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_weekly_report(token: str, week_start: str = None) -> Dict[str, Any]:
        """Example: Get weekly report."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if week_start:
            params["week_start"] = week_start
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/reports/weekly",
            headers=headers,
            params=params
        )
        print(f"Weekly Report: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_monthly_report(token: str, month: str = None) -> Dict[str, Any]:
        """Example: Get monthly report."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if month:
            params["month"] = month
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/reports/monthly",
            headers=headers,
            params=params
        )
        print(f"Monthly Report: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def export_metrics(token: str, format: str = "csv") -> bytes:
        """Example: Export metrics."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export",
            headers=headers,
            params={"format": format}
        )
        print(f"Export Metrics ({format}): {response.status_code}\n")
        return response.content


# ============================================================================
# PHASE E4: KNOWLEDGE GRAPH
# ============================================================================

class E4Examples:
    """E4 Examples: Knowledge Graph, Recommendations."""
    
    @staticmethod
    def create_node(token: str, node_type: str, properties: Dict) -> Dict[str, Any]:
        """Example: Create a graph node."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "node_type": node_type,
            "properties": properties
        }
        response = requests.post(
            f"{BASE_URL}/api/graph/nodes",
            json=payload,
            headers=headers
        )
        print(f"Create Node: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def create_edge(token: str, source_id: str, target_id: str, 
                    relationship_type: str) -> Dict[str, Any]:
        """Example: Create a graph edge."""
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type
        }
        response = requests.post(
            f"{BASE_URL}/api/graph/edges",
            json=payload,
            headers=headers
        )
        print(f"Create Edge: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_node(token: str, node_id: str) -> Dict[str, Any]:
        """Example: Get a node."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/nodes/{node_id}",
            headers=headers
        )
        print(f"Get Node: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def search_nodes(token: str, query: str, node_type: str = None) -> Dict[str, Any]:
        """Example: Search nodes."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {"query": query}
        if node_type:
            params["node_type"] = node_type
        
        response = requests.get(
            f"{BASE_URL}/api/graph/search",
            headers=headers,
            params=params
        )
        print(f"Search Nodes: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def get_nodes_by_type(token: str, node_type: str) -> Dict[str, Any]:
        """Example: Get nodes by type."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/nodes/type/{node_type}",
            headers=headers
        )
        print(f"Get Nodes by Type: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def find_path(token: str, source_id: str, target_id: str, 
                  max_depth: int = 3) -> Dict[str, Any]:
        """Example: Find path between nodes."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/paths",
            headers=headers,
            params={
                "source_id": source_id,
                "target_id": target_id,
                "max_depth": max_depth
            }
        )
        print(f"Find Path: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def find_connections(token: str, node_id: str, 
                        relationship_type: str = None) -> Dict[str, Any]:
        """Example: Find node connections."""
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if relationship_type:
            params["relationship_type"] = relationship_type
        
        response = requests.get(
            f"{BASE_URL}/api/graph/connections/{node_id}",
            headers=headers,
            params=params
        )
        print(f"Find Connections: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def recommend_papers(token: str, paper_id: str) -> Dict[str, Any]:
        """Example: Get paper recommendations."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/recommendations/papers/{paper_id}",
            headers=headers
        )
        print(f"Recommend Papers: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def recommend_technologies(token: str, tech_id: str) -> Dict[str, Any]:
        """Example: Get technology recommendations."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/recommendations/technologies/{tech_id}",
            headers=headers
        )
        print(f"Recommend Technologies: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def find_experts(token: str, topic: str) -> Dict[str, Any]:
        """Example: Find experts for topic."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/experts",
            headers=headers,
            params={"topic": topic}
        )
        print(f"Find Experts: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result
    
    @staticmethod
    def calculate_similarity(token: str, node1_id: str, node2_id: str) -> Dict[str, Any]:
        """Example: Calculate similarity between nodes."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/graph/similarity",
            headers=headers,
            params={
                "node1_id": node1_id,
                "node2_id": node2_id
            }
        )
        print(f"Calculate Similarity: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
        return result


# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================

def run_complete_workflow():
    """Run a complete workflow demonstrating all Phase E components."""
    print("=" * 80)
    print("PHASE E: COMPLETE WORKFLOW EXAMPLE")
    print("=" * 80)
    print()
    
    # STEP 1: E1 - Authentication
    print("PHASE E1: AUTHENTICATION")
    print("-" * 80)
    user_data = E1Examples.user_registration()
    login_data = E1Examples.user_login()
    token = login_data.get("access_token")
    E1Examples.get_current_user(token)
    E1Examples.check_health()
    E1Examples.get_metrics()
    
    # STEP 2: E2 - Async Jobs
    print("PHASE E2: ASYNC JOB EXECUTION")
    print("-" * 80)
    job_eval = E2Examples.enqueue_project_evaluation(token, "proj-123")
    job_id = job_eval.get("job_id")
    E2Examples.get_job_status(token, job_id)
    E2Examples.list_jobs(token)
    E2Examples.check_async_health(token)
    
    # STEP 3: E3 - Analytics
    print("PHASE E3: ANALYTICS & METRICS")
    print("-" * 80)
    E3Examples.record_metric(token, "project_evaluations", 1.0)
    E3Examples.get_metric_history(token, "project_evaluations")
    E3Examples.get_realtime_dashboard(token)
    E3Examples.get_performance_dashboard(token)
    E3Examples.get_health_dashboard(token)
    E3Examples.get_daily_report(token)
    
    # STEP 4: E4 - Knowledge Graph
    print("PHASE E4: KNOWLEDGE GRAPH")
    print("-" * 80)
    paper_node = E4Examples.create_node(
        token,
        "Paper",
        {"title": "Secure Coding Agents", "year": 2024}
    )
    paper_id = paper_node.get("node_id")
    
    tech_node = E4Examples.create_node(
        token,
        "Technology",
        {"name": "FlowGuard", "category": "Security"}
    )
    tech_id = tech_node.get("node_id")
    
    E4Examples.create_edge(token, paper_id, tech_id, "IMPLEMENTS")
    E4Examples.get_node(token, paper_id)
    E4Examples.search_nodes(token, "security")
    E4Examples.recommend_papers(token, paper_id)
    
    print("=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Run complete workflow
    run_complete_workflow()
    
    # Or use individual examples:
    # token = E1Examples.user_login()["access_token"]
    # E2Examples.enqueue_project_evaluation(token, "proj-123")
    # E3Examples.get_realtime_dashboard(token)
    # E4Examples.search_nodes(token, "query")
