from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
import os
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

LOG_FILE = "data/system.jsonl"

@router.get("/", response_model=Dict[str, Any])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    page: int = Query(1, ge=1),
    search: str = Query(None),
    level: str = Query(None)
):
    """
    Retrieve system logs with pagination, search, and level filtering.
    Returns logs in reverse chronological order (newest first).
    """
    if not os.path.exists(LOG_FILE):
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0
        }

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Reverse to show newest first
        lines.reverse()
        
        parsed_logs = []
        for line in lines:
            if not line.strip(): continue
            try:
                log_entry = json.loads(line)
                
                # Level filter
                if level and level.upper() != 'ALL' and log_entry.get('level') != level.upper():
                    continue

                # Search filter
                if search:
                    search_term = search.lower()
                    # Search in message, module, level, or exception if exists
                    if (search_term in log_entry.get('message', '').lower() or 
                        search_term in log_entry.get('module', '').lower() or 
                        search_term in log_entry.get('level', '').lower() or
                        search_term in str(log_entry.get('line', '')).lower() or
                        search_term in log_entry.get('timestamp', '').lower() or
                        (log_entry.get('exception') and search_term in log_entry['exception'].lower())):
                        parsed_logs.append(log_entry)
                else:
                    parsed_logs.append(log_entry)
            except json.JSONDecodeError:
                continue
        
        # Pagination
        total = len(parsed_logs)
        total_pages = (total + limit - 1) // limit
        
        start = (page - 1) * limit
        end = start + limit
        
        paginated_items = parsed_logs[start:end]
        
        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
            
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error reading logs")

@router.delete("/", status_code=200)
async def clear_logs():
    """
    Clear all system logs.
    """
    try:
        # Open in write mode to truncate
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            pass
        logger.info("System logs cleared by user.")
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing log file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error clearing logs")
