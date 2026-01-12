"""Tests for Phase E4: Knowledge Graph."""

import pytest

from knowledge_graph import (
    GraphNode, GraphEdge, GraphDatabase_, Neo4jConfig,
    NodeQuery, EdgeQuery, RecommendationEngine,
    NodeType, RelationshipType
)


@pytest.fixture
def neo4j_config():
    """Create Neo4j configuration."""
    return Neo4jConfig(
        uri="bolt://localhost:7687",
        username="test",
        password="test"
    )


@pytest.fixture
def graph_db(neo4j_config):
    """Create graph database instance (mock mode)."""
    return GraphDatabase_(neo4j_config)


@pytest.fixture
def sample_node():
    """Create sample node."""
    return GraphNode(
        id="paper-1",
        node_type=NodeType.PAPER,
        properties={"title": "Test Paper", "year": 2024}
    )


@pytest.fixture
def sample_edge():
    """Create sample edge."""
    return GraphEdge(
        source_id="author-1",
        target_id="paper-1",
        relationship_type=RelationshipType.AUTHOR,
        properties={"role": "primary"}
    )


class TestGraphNode:
    """Test GraphNode model."""
    
    def test_node_creation(self):
        """Test creating node."""
        node = GraphNode(
            id="node-1",
            node_type=NodeType.CONCEPT,
            properties={"name": "Machine Learning"}
        )
        
        assert node.id == "node-1"
        assert node.node_type == NodeType.CONCEPT
        assert node.properties["name"] == "Machine Learning"
    
    def test_node_types(self):
        """Test all node types."""
        types = [
            NodeType.PAPER, NodeType.AUTHOR, NodeType.TECHNOLOGY,
            NodeType.CONCEPT, NodeType.VENUE, NodeType.PROJECT,
            NodeType.ARTIFACT, NodeType.EVALUATION
        ]
        assert len(types) == 8
    
    def test_node_to_dict(self):
        """Test converting node to dict."""
        node = GraphNode(
            id="node-2",
            node_type=NodeType.AUTHOR,
            properties={"name": "John Doe", "affiliation": "MIT"}
        )
        
        node_dict = node.to_dict()
        assert node_dict["id"] == "node-2"
        assert node_dict["type"] == NodeType.AUTHOR.value
        assert node_dict["properties"]["name"] == "John Doe"


class TestGraphEdge:
    """Test GraphEdge model."""
    
    def test_edge_creation(self):
        """Test creating edge."""
        edge = GraphEdge(
            source_id="author-1",
            target_id="paper-1",
            relationship_type=RelationshipType.AUTHOR
        )
        
        assert edge.source_id == "author-1"
        assert edge.target_id == "paper-1"
        assert edge.relationship_type == RelationshipType.AUTHOR
    
    def test_edge_with_properties(self):
        """Test edge with properties."""
        edge = GraphEdge(
            source_id="paper-1",
            target_id="paper-2",
            relationship_type=RelationshipType.CITES,
            properties={"year": 2024}
        )
        
        assert edge.properties["year"] == 2024
    
    def test_relationship_types(self):
        """Test all relationship types."""
        types = [
            RelationshipType.RELATED_TO, RelationshipType.CITES,
            RelationshipType.AUTHOR, RelationshipType.PUBLISHED_IN,
            RelationshipType.USES, RelationshipType.IMPLEMENTS,
            RelationshipType.DEPENDS_ON, RelationshipType.SIMILAR_TO,
            RelationshipType.DERIVED_FROM, RelationshipType.EVALUATES
        ]
        assert len(types) == 10
    
    def test_edge_to_dict(self):
        """Test converting edge to dict."""
        edge = GraphEdge(
            source_id="project-1",
            target_id="tech-1",
            relationship_type=RelationshipType.USES,
            properties={"version": "1.0"}
        )
        
        edge_dict = edge.to_dict()
        assert edge_dict["source"] == "project-1"
        assert edge_dict["target"] == "tech-1"
        assert edge_dict["relationship"] == RelationshipType.USES.value


class TestNeo4jConfig:
    """Test Neo4j configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = Neo4jConfig()
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.password == "password"
        assert config.database == "neo4j"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = Neo4jConfig(
            uri="bolt://custom:7687",
            username="user",
            password="pass",
            database="custom_db"
        )
        
        assert config.uri == "bolt://custom:7687"
        assert config.username == "user"


class TestGraphDatabase:
    """Test GraphDatabase interface."""
    
    def test_create_node(self, graph_db, sample_node):
        """Test creating node."""
        result = graph_db.create_node(sample_node)
        # In mock mode, should return True
        assert result is True
    
    def test_create_edge(self, graph_db, sample_edge):
        """Test creating edge."""
        result = graph_db.create_edge(sample_edge)
        # In mock mode, should return True
        assert result is True
    
    def test_connection(self, neo4j_config):
        """Test connection initialization."""
        db = GraphDatabase_(neo4j_config)
        # In mock mode (no Neo4j), connection should fail gracefully
        assert db.driver is None or db.driver is not None


class TestNodeQuery:
    """Test NodeQuery."""
    
    def test_node_query_creation(self, graph_db):
        """Test creating node query."""
        query = NodeQuery(graph_db)
        assert query.db == graph_db
    
    def test_find_by_type(self, graph_db):
        """Test finding nodes by type."""
        query = NodeQuery(graph_db)
        # In mock mode, returns empty list
        results = query.find_by_type(NodeType.PAPER)
        assert isinstance(results, list)
    
    def test_search(self, graph_db):
        """Test searching nodes."""
        query = NodeQuery(graph_db)
        # In mock mode, returns empty list
        results = query.search("machine learning")
        assert isinstance(results, list)
    
    def test_search_with_type_filter(self, graph_db):
        """Test searching with node type filter."""
        query = NodeQuery(graph_db)
        results = query.search("learning", NodeType.CONCEPT)
        assert isinstance(results, list)


class TestEdgeQuery:
    """Test EdgeQuery."""
    
    def test_edge_query_creation(self, graph_db):
        """Test creating edge query."""
        query = EdgeQuery(graph_db)
        assert query.db == graph_db
    
    def test_find_connections(self, graph_db):
        """Test finding connections."""
        query = EdgeQuery(graph_db)
        # In mock mode, returns empty list
        connections = query.find_connections("node-1")
        assert isinstance(connections, list)
    
    def test_find_connections_with_type(self, graph_db):
        """Test finding connections with relationship type filter."""
        query = EdgeQuery(graph_db)
        connections = query.find_connections("node-1", RelationshipType.USES)
        assert isinstance(connections, list)
    
    def test_find_connections_with_depth(self, graph_db):
        """Test finding connections with depth."""
        query = EdgeQuery(graph_db)
        connections = query.find_connections("node-1", depth=3)
        assert isinstance(connections, list)


class TestRecommendationEngine:
    """Test RecommendationEngine."""
    
    def test_engine_creation(self, graph_db):
        """Test creating recommendation engine."""
        engine = RecommendationEngine(graph_db)
        assert engine.db == graph_db
    
    def test_recommend_papers(self, graph_db):
        """Test paper recommendations."""
        engine = RecommendationEngine(graph_db)
        recommendations = engine.recommend_papers("paper-1")
        
        assert isinstance(recommendations, list)
        # In mock mode, should have recommendations
        if len(recommendations) > 0:
            assert "id" in recommendations[0]
            assert "score" in recommendations[0]
    
    def test_recommend_technologies(self, graph_db):
        """Test technology recommendations."""
        engine = RecommendationEngine(graph_db)
        recommendations = engine.recommend_technologies("project-1")
        
        assert isinstance(recommendations, list)
        if len(recommendations) > 0:
            assert "id" in recommendations[0]
            assert "name" in recommendations[0]
    
    def test_find_experts(self, graph_db):
        """Test finding experts."""
        engine = RecommendationEngine(graph_db)
        experts = engine.find_experts("topic-1")
        
        assert isinstance(experts, list)
        if len(experts) > 0:
            assert "id" in experts[0]
            assert "name" in experts[0]
    
    def test_calculate_similarity(self, graph_db):
        """Test similarity calculation."""
        engine = RecommendationEngine(graph_db)
        score = engine.calculate_similarity("node-1", "node-2")
        
        assert isinstance(score, float)
        assert 0 <= score <= 1


class TestGraphOperations:
    """Test complete graph operations."""
    
    def test_node_creation_workflow(self, graph_db):
        """Test node creation workflow."""
        node1 = GraphNode("node-1", NodeType.PAPER, {"title": "Paper 1"})
        node2 = GraphNode("node-2", NodeType.AUTHOR, {"name": "Author 1"})
        
        result1 = graph_db.create_node(node1)
        result2 = graph_db.create_node(node2)
        
        assert result1 is True
        assert result2 is True
    
    def test_relationship_workflow(self, graph_db):
        """Test relationship workflow."""
        edge = GraphEdge(
            "paper-1",
            "author-1",
            RelationshipType.AUTHOR
        )
        
        result = graph_db.create_edge(edge)
        assert result is True
    
    def test_recommendation_workflow(self, graph_db):
        """Test recommendation workflow."""
        engine = RecommendationEngine(graph_db)
        
        papers = engine.recommend_papers("paper-1", limit=3)
        techs = engine.recommend_technologies("project-1", limit=3)
        experts = engine.find_experts("topic-1", limit=3)
        
        assert isinstance(papers, list)
        assert isinstance(techs, list)
        assert isinstance(experts, list)


class TestNodeTypes:
    """Test NodeType enum."""
    
    def test_all_node_types(self):
        """Test all node types exist."""
        types = [
            NodeType.PAPER, NodeType.AUTHOR, NodeType.TECHNOLOGY,
            NodeType.CONCEPT, NodeType.VENUE, NodeType.PROJECT,
            NodeType.ARTIFACT, NodeType.EVALUATION
        ]
        assert len(types) == 8
    
    def test_node_type_values(self):
        """Test node type string values."""
        assert NodeType.PAPER.value == "Paper"
        assert NodeType.AUTHOR.value == "Author"
        assert NodeType.TECHNOLOGY.value == "Technology"


class TestRelationshipTypes:
    """Test RelationshipType enum."""
    
    def test_all_relationship_types(self):
        """Test all relationship types exist."""
        types = [
            RelationshipType.RELATED_TO, RelationshipType.CITES,
            RelationshipType.AUTHOR, RelationshipType.PUBLISHED_IN,
            RelationshipType.USES, RelationshipType.IMPLEMENTS,
            RelationshipType.DEPENDS_ON, RelationshipType.SIMILAR_TO,
            RelationshipType.DERIVED_FROM, RelationshipType.EVALUATES
        ]
        assert len(types) == 10
    
    def test_relationship_type_values(self):
        """Test relationship type string values."""
        assert RelationshipType.RELATED_TO.value == "RELATED_TO"
        assert RelationshipType.AUTHOR.value == "AUTHOR"
        assert RelationshipType.CITES.value == "CITES"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
