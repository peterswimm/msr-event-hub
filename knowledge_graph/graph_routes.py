"""FastAPI routes for knowledge graph."""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends

from knowledge_graph import (
    GraphDatabase_, Neo4jConfig, NodeQuery, EdgeQuery,
    RecommendationEngine, NodeType, RelationshipType,
    GraphNode, GraphEdge
)

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


# Global graph DB instance
_graph_db = None


def get_graph_db() -> GraphDatabase_:
    """Get or create graph database instance.
    
    Returns:
        GraphDatabase_ instance
    """
    global _graph_db
    if _graph_db is None:
        config = Neo4jConfig()
        _graph_db = GraphDatabase_(config)
    return _graph_db


def get_node_query(db: GraphDatabase_ = Depends(get_graph_db)) -> NodeQuery:
    """Get NodeQuery dependency."""
    return NodeQuery(db)


def get_edge_query(db: GraphDatabase_ = Depends(get_graph_db)) -> EdgeQuery:
    """Get EdgeQuery dependency."""
    return EdgeQuery(db)


def get_recommendation_engine(db: GraphDatabase_ = Depends(get_graph_db)) -> RecommendationEngine:
    """Get RecommendationEngine dependency."""
    return RecommendationEngine(db)


@router.post("/nodes")
async def create_node(
    node_id: str,
    node_type: str,
    properties: dict,
    db: GraphDatabase_ = Depends(get_graph_db)
) -> dict:
    """Create a graph node.
    
    Args:
        node_id: Node ID
        node_type: Node type (Paper, Author, Technology, etc.)
        properties: Node properties
        db: Graph database dependency
        
    Returns:
        Created node
    """
    try:
        node = GraphNode(
            id=node_id,
            node_type=NodeType[node_type.upper()],
            properties=properties
        )
        
        success = db.create_node(node)
        
        if success:
            return {"created": True, "node": node.to_dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to create node")
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid node type. Must be one of: {', '.join([t.value for t in NodeType])}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    db: GraphDatabase_ = Depends(get_graph_db)
) -> dict:
    """Get node by ID.
    
    Args:
        node_id: Node ID
        db: Graph database dependency
        
    Returns:
        Node data
    """
    try:
        node = db.get_node(node_id)
        
        if node:
            return {"node": node.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="Node not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges")
async def create_edge(
    source_id: str,
    target_id: str,
    relationship_type: str,
    properties: dict = None,
    db: GraphDatabase_ = Depends(get_graph_db)
) -> dict:
    """Create relationship between nodes.
    
    Args:
        source_id: Source node ID
        target_id: Target node ID
        relationship_type: Relationship type
        properties: Relationship properties
        db: Graph database dependency
        
    Returns:
        Created relationship
    """
    try:
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=RelationshipType[relationship_type.upper()],
            properties=properties or {}
        )
        
        success = db.create_edge(edge)
        
        if success:
            return {"created": True, "edge": edge.to_dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to create edge")
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid relationship type. Must be one of: {', '.join([r.value for r in RelationshipType])}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/search")
async def search_nodes(
    query: str,
    node_type: Optional[str] = None,
    node_query: NodeQuery = Depends(get_node_query)
) -> dict:
    """Search for nodes.
    
    Args:
        query: Search query
        node_type: Optional node type filter
        node_query: NodeQuery dependency
        
    Returns:
        Search results
    """
    try:
        node_type_enum = None
        if node_type:
            try:
                node_type_enum = NodeType[node_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid node type. Must be one of: {', '.join([t.value for t in NodeType])}"
                )
        
        results = node_query.search(query, node_type_enum)
        
        return {
            "query": query,
            "node_type_filter": node_type,
            "count": len(results),
            "nodes": [n.to_dict() for n in results]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/by-type/{node_type}")
async def get_nodes_by_type(
    node_type: str,
    limit: int = 100,
    node_query: NodeQuery = Depends(get_node_query)
) -> dict:
    """Get nodes by type.
    
    Args:
        node_type: Node type
        limit: Maximum results
        node_query: NodeQuery dependency
        
    Returns:
        Nodes of specified type
    """
    try:
        node_type_enum = NodeType[node_type.upper()]
        results = node_query.find_by_type(node_type_enum, limit)
        
        return {
            "node_type": node_type,
            "count": len(results),
            "limit": limit,
            "nodes": [n.to_dict() for n in results]
        }
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid node type. Must be one of: {', '.join([t.value for t in NodeType])}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths/{source_id}/{target_id}")
async def find_path(
    source_id: str,
    target_id: str,
    max_depth: int = 5,
    db: GraphDatabase_ = Depends(get_graph_db)
) -> dict:
    """Find path between nodes.
    
    Args:
        source_id: Source node ID
        target_id: Target node ID
        max_depth: Maximum path depth
        db: Graph database dependency
        
    Returns:
        Path data
    """
    try:
        path = db.find_path(source_id, target_id, max_depth)
        
        if path:
            return {
                "source": source_id,
                "target": target_id,
                "path_length": len(path),
                "nodes": [n.to_dict() for n in path]
            }
        else:
            raise HTTPException(status_code=404, detail="No path found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{node_id}")
async def get_connections(
    node_id: str,
    relationship_type: Optional[str] = None,
    depth: int = 1,
    edge_query: EdgeQuery = Depends(get_edge_query)
) -> dict:
    """Get connected nodes.
    
    Args:
        node_id: Source node ID
        relationship_type: Optional relationship filter
        depth: Search depth
        edge_query: EdgeQuery dependency
        
    Returns:
        Connected nodes
    """
    try:
        rel_type = None
        if relationship_type:
            try:
                rel_type = RelationshipType[relationship_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid relationship type. Must be one of: {', '.join([r.value for r in RelationshipType])}"
                )
        
        connections = edge_query.find_connections(node_id, rel_type, depth)
        
        return {
            "source": node_id,
            "relationship_filter": relationship_type,
            "depth": depth,
            "connection_count": len(connections),
            "connections": [
                {
                    "source": src.to_dict(),
                    "relationship": rel.value,
                    "target": tgt.to_dict()
                }
                for src, rel, tgt in connections
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/papers/{paper_id}")
async def recommend_papers(
    paper_id: str,
    limit: int = 5,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> dict:
    """Get paper recommendations.
    
    Args:
        paper_id: Reference paper ID
        limit: Number of recommendations
        engine: RecommendationEngine dependency
        
    Returns:
        Recommended papers
    """
    try:
        recommendations = engine.recommend_papers(paper_id, limit)
        
        return {
            "reference_paper": paper_id,
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/technologies/{project_id}")
async def recommend_technologies(
    project_id: str,
    limit: int = 5,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> dict:
    """Get technology recommendations.
    
    Args:
        project_id: Project ID
        limit: Number of recommendations
        engine: RecommendationEngine dependency
        
    Returns:
        Recommended technologies
    """
    try:
        recommendations = engine.recommend_technologies(project_id, limit)
        
        return {
            "project": project_id,
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experts/{topic_id}")
async def find_experts(
    topic_id: str,
    limit: int = 5,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> dict:
    """Find experts on a topic.
    
    Args:
        topic_id: Topic/concept ID
        limit: Number of experts
        engine: RecommendationEngine dependency
        
    Returns:
        Expert authors
    """
    try:
        experts = engine.find_experts(topic_id, limit)
        
        return {
            "topic": topic_id,
            "count": len(experts),
            "experts": experts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similarity")
async def calculate_similarity(
    node1_id: str,
    node2_id: str,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> dict:
    """Calculate similarity between nodes.
    
    Args:
        node1_id: First node ID
        node2_id: Second node ID
        engine: RecommendationEngine dependency
        
    Returns:
        Similarity score
    """
    try:
        score = engine.calculate_similarity(node1_id, node2_id)
        
        return {
            "node1": node1_id,
            "node2": node2_id,
            "similarity_score": score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
