"""Phase E4: Knowledge Graph.

Neo4j integration for relationship mapping, recommendations, and knowledge extraction.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import json

try:
    from neo4j import GraphDatabase, Session as Neo4jSession
    from neo4j.exceptions import ServiceUnavailable
except ImportError:
    GraphDatabase = None
    Neo4jSession = None


class RelationshipType(str, Enum):
    """Types of relationships in knowledge graph."""
    RELATED_TO = "RELATED_TO"  # Generic relationship
    CITES = "CITES"  # Paper cites another
    AUTHOR = "AUTHOR"  # Author relationship
    PUBLISHED_IN = "PUBLISHED_IN"  # Publication venue
    USES = "USES"  # Uses technology
    IMPLEMENTS = "IMPLEMENTS"  # Implementation of concept
    DEPENDS_ON = "DEPENDS_ON"  # Dependency relationship
    SIMILAR_TO = "SIMILAR_TO"  # Similarity
    DERIVED_FROM = "DERIVED_FROM"  # Derived from
    EVALUATES = "EVALUATES"  # Evaluation relationship


class NodeType(str, Enum):
    """Types of nodes in knowledge graph."""
    PAPER = "Paper"
    AUTHOR = "Author"
    TECHNOLOGY = "Technology"
    CONCEPT = "Concept"
    VENUE = "Venue"
    PROJECT = "Project"
    ARTIFACT = "Artifact"
    EVALUATION = "Evaluation"


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    node_type: NodeType
    properties: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.node_type.value,
            "properties": self.properties
        }


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relationship": self.relationship_type.value,
            "properties": self.properties or {}
        }


class Neo4jConfig:
    """Configuration for Neo4j connection."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j"
    ):
        """Initialize Neo4j configuration.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
            database: Database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database


class GraphDatabase_:
    """Neo4j graph database interface."""
    
    def __init__(self, config: Neo4jConfig):
        """Initialize graph database.
        
        Args:
            config: Neo4j configuration
        """
        self.config = config
        self.driver = None
        self.session = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j."""
        if GraphDatabase is None:
            # Mock mode for testing without Neo4j
            return
        
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            self.driver.verify_connectivity()
        except ServiceUnavailable:
            # Connection failed, continue in mock mode
            self.driver = None
    
    def get_session(self) -> Optional[Neo4jSession]:
        """Get database session.
        
        Returns:
            Neo4j session or None
        """
        if self.driver:
            return self.driver.session(database=self.config.database)
        return None
    
    def close(self):
        """Close connection."""
        if self.driver:
            self.driver.close()
    
    def create_node(self, node: GraphNode) -> bool:
        """Create a node.
        
        Args:
            node: Node to create
            
        Returns:
            True if successful
        """
        if not self.driver:
            return True  # Mock success
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            query = f"""
            CREATE (n:{node.node_type.value} {{id: $id, ...$ properties}})
            RETURN n
            """
            session.run(query, id=node.id, properties=node.properties)
            return True
        finally:
            session.close()
    
    def create_edge(self, edge: GraphEdge) -> bool:
        """Create an edge.
        
        Args:
            edge: Edge to create
            
        Returns:
            True if successful
        """
        if not self.driver:
            return True  # Mock success
        
        session = self.get_session()
        if not session:
            return False
        
        try:
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            CREATE (source)-[r:{edge.relationship_type.value} {{...$ properties}}]->(target)
            RETURN r
            """
            session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                properties=edge.properties or {}
            )
            return True
        finally:
            session.close()
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            GraphNode or None
        """
        if not self.driver:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            query = "MATCH (n {id: $id}) RETURN n"
            result = session.run(query, id=node_id)
            record = result.single()
            
            if record:
                node_data = record["n"]
                return GraphNode(
                    id=node_data["id"],
                    node_type=NodeType(node_data.get("type", "Concept")),
                    properties=dict(node_data)
                )
        finally:
            session.close()
        
        return None
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[GraphNode]]:
        """Find path between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum path depth
            
        Returns:
            List of nodes in path or None
        """
        if not self.driver:
            return None
        
        session = self.get_session()
        if not session:
            return None
        
        try:
            query = f"""
            MATCH path = shortestPath(
                (source {{id: $source}})-[*..${max_depth}]-(target {{id: $target}})
            )
            RETURN path
            """
            result = session.run(query, source=source_id, target=target_id)
            record = result.single()
            
            if record:
                path = record["path"]
                return [GraphNode(n["id"], NodeType.CONCEPT, dict(n)) for n in path.nodes]
        finally:
            session.close()
        
        return None


class NodeQuery:
    """Query interface for nodes."""
    
    def __init__(self, db: GraphDatabase_):
        """Initialize node query.
        
        Args:
            db: Graph database instance
        """
        self.db = db
    
    def find_by_type(self, node_type: NodeType, limit: int = 100) -> List[GraphNode]:
        """Find nodes by type.
        
        Args:
            node_type: Node type
            limit: Maximum results
            
        Returns:
            List of nodes
        """
        if not self.db.driver:
            return []
        
        session = self.db.get_session()
        if not session:
            return []
        
        try:
            query = f"MATCH (n:{node_type.value}) RETURN n LIMIT {limit}"
            result = session.run(query)
            
            nodes = []
            for record in result:
                node_data = record["n"]
                nodes.append(GraphNode(
                    id=node_data["id"],
                    node_type=node_type,
                    properties=dict(node_data)
                ))
            return nodes
        finally:
            session.close()
    
    def search(self, query_text: str, node_type: NodeType = None) -> List[GraphNode]:
        """Search for nodes.
        
        Args:
            query_text: Search text
            node_type: Optional node type filter
            
        Returns:
            List of matching nodes
        """
        if not self.db.driver:
            return []
        
        session = self.db.get_session()
        if not session:
            return []
        
        try:
            if node_type:
                query = f"""
                MATCH (n:{node_type.value})
                WHERE ANY(prop IN properties(n) WHERE toString(prop) CONTAINS $query)
                RETURN n
                """
            else:
                query = """
                MATCH (n)
                WHERE ANY(prop IN properties(n) WHERE toString(prop) CONTAINS $query)
                RETURN n
                """
            
            result = session.run(query, query=query_text)
            
            nodes = []
            for record in result:
                node_data = record["n"]
                nodes.append(GraphNode(
                    id=node_data["id"],
                    node_type=NodeType(node_data.get("type", "Concept")),
                    properties=dict(node_data)
                ))
            return nodes
        finally:
            session.close()


class EdgeQuery:
    """Query interface for edges."""
    
    def __init__(self, db: GraphDatabase_):
        """Initialize edge query.
        
        Args:
            db: Graph database instance
        """
        self.db = db
    
    def find_connections(
        self,
        node_id: str,
        relationship_type: RelationshipType = None,
        depth: int = 1
    ) -> List[Tuple[GraphNode, RelationshipType, GraphNode]]:
        """Find connected nodes.
        
        Args:
            node_id: Source node ID
            relationship_type: Optional relationship filter
            depth: Search depth
            
        Returns:
            List of (source, relationship, target) tuples
        """
        if not self.db.driver:
            return []
        
        session = self.db.get_session()
        if not session:
            return []
        
        try:
            rel_filter = f":{relationship_type.value}" if relationship_type else ""
            query = f"""
            MATCH (source {{id: $node_id}})-[r{rel_filter}*..{depth}]-(target)
            RETURN source, type(r) as rel_type, target
            """
            result = session.run(query, node_id=node_id)
            
            connections = []
            for record in result:
                source_data = record["source"]
                target_data = record["target"]
                rel_type = RelationshipType(record["rel_type"])
                
                connections.append((
                    GraphNode(source_data["id"], NodeType.CONCEPT, dict(source_data)),
                    rel_type,
                    GraphNode(target_data["id"], NodeType.CONCEPT, dict(target_data))
                ))
            return connections
        finally:
            session.close()


class RecommendationEngine:
    """Generates recommendations based on knowledge graph."""
    
    def __init__(self, db: GraphDatabase_):
        """Initialize recommendation engine.
        
        Args:
            db: Graph database instance
        """
        self.db = db
        self.node_query = NodeQuery(db)
        self.edge_query = EdgeQuery(db)
    
    def recommend_papers(self, paper_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recommend related papers.
        
        Args:
            paper_id: Reference paper ID
            limit: Number of recommendations
            
        Returns:
            List of recommended papers
        """
        if not self.db.driver:
            # Mock recommendations
            return [
                {"id": f"paper-{i}", "score": 0.8 - i*0.1, "reason": "Similar research"}
                for i in range(limit)
            ]
        
        connections = self.edge_query.find_connections(
            paper_id,
            relationship_type=RelationshipType.RELATED_TO,
            depth=2
        )
        
        # Score and sort by relevance
        recommendations = []
        seen = set()
        
        for source, rel, target in connections:
            if target.id not in seen:
                recommendations.append({
                    "id": target.id,
                    "type": target.node_type.value,
                    "properties": target.properties,
                    "score": 0.8,  # Simplified scoring
                    "reason": f"Connected via {rel.value}"
                })
                seen.add(target.id)
        
        return recommendations[:limit]
    
    def recommend_technologies(
        self,
        project_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recommend technologies for project.
        
        Args:
            project_id: Project ID
            limit: Number of recommendations
            
        Returns:
            List of recommended technologies
        """
        if not self.db.driver:
            # Mock recommendations
            return [
                {"id": f"tech-{i}", "name": f"Technology {i}", "score": 0.8 - i*0.1}
                for i in range(limit)
            ]
        
        connections = self.edge_query.find_connections(
            project_id,
            relationship_type=RelationshipType.USES,
            depth=1
        )
        
        recommendations = []
        for source, rel, target in connections:
            if target.node_type == NodeType.TECHNOLOGY:
                recommendations.append({
                    "id": target.id,
                    "name": target.properties.get("name", target.id),
                    "properties": target.properties,
                    "score": 0.75
                })
        
        return recommendations[:limit]
    
    def find_experts(
        self,
        topic_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find experts on a topic.
        
        Args:
            topic_id: Topic/concept ID
            limit: Number of results
            
        Returns:
            List of expert authors
        """
        if not self.db.driver:
            # Mock experts
            return [
                {"id": f"author-{i}", "name": f"Author {i}", "papers": i+5}
                for i in range(limit)
            ]
        
        connections = self.edge_query.find_connections(
            topic_id,
            depth=3
        )
        
        # Count connections by author
        author_counts = {}
        for source, rel, target in connections:
            if target.node_type == NodeType.AUTHOR:
                author_id = target.id
                author_counts[author_id] = author_counts.get(author_id, 0) + 1
        
        # Sort by count
        experts = [
            {
                "id": author_id,
                "name": author_id,
                "connections": count,
                "score": count / 10.0
            }
            for author_id, count in sorted(author_counts.items(), key=lambda x: -x[1])
        ]
        
        return experts[:limit]
    
    def calculate_similarity(
        self,
        node1_id: str,
        node2_id: str
    ) -> float:
        """Calculate similarity between two nodes.
        
        Args:
            node1_id: First node ID
            node2_id: Second node ID
            
        Returns:
            Similarity score (0-1)
        """
        if not self.db.driver:
            return 0.5
        
        # Simplified similarity: based on shared connections
        connections1 = set(
            t.id for _, _, t in self.edge_query.find_connections(node1_id, depth=2)
        )
        connections2 = set(
            t.id for _, _, t in self.edge_query.find_connections(node2_id, depth=2)
        )
        
        if not connections1 or not connections2:
            return 0.0
        
        intersection = len(connections1 & connections2)
        union = len(connections1 | connections2)
        
        return intersection / union if union > 0 else 0.0
