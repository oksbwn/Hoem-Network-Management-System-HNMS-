from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.topology import TopologyService

router = APIRouter(
    tags=["topology"],
    responses={404: {"description": "Not found"}},
)

topology_service = TopologyService()

@router.get("/", response_model=Dict[str, Any])
async def get_topology():
    """
    Get the network topology graph (nodes and edges).
    """
    return topology_service.get_graph()
