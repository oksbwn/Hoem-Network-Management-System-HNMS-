from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.core.db import get_connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/traffic")
def get_traffic_analytics(range: str = "24h"):
    """
    Returns time-series traffic data aggregated by time buckets.
    range: 24h, yesterday, 7d, 30d, 3m, mtd, last_month, ytd, 1y, all
    """
    conn = get_connection()
    try:
        now = datetime.now()
        start_time, end_time, bucket_size, trunc_arg = get_date_range(range, now)

        sql = f"""
            SELECT 
                date_trunc('{trunc_arg}', timestamp) as bucket,
                SUM(down_rate) as download,
                SUM(up_rate) as upload
            FROM device_traffic_history
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY bucket
            ORDER BY bucket ASC
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        # Format response
        series = []
        for r in rows:
            series.append({
                "timestamp": r[0],
                "download": r[1],
                "upload": r[2]
            })
            
        # Calculate totals for the period
        totals_row = conn.execute("""
            SELECT 
                SUM(down_rate), 
                SUM(up_rate),
                COUNT(DISTINCT device_id)
            FROM device_traffic_history
            WHERE timestamp >= ? AND timestamp <= ?
        """, [start_time, end_time]).fetchone()
        
        return {
            "series": series,
            "totals": {
                "download": totals_row[0] or 0,
                "upload": totals_row[1] or 0,
                "active_devices": totals_row[2] or 0
            }
        }
    finally:
        conn.close()

@router.get("/top-devices")
def get_top_devices(range: str = "24h", limit: int = 5):
    """
    Returns top consumers by total usage in the time window.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)
        
        sql = """
            SELECT 
                d.id, d.name, d.display_name, d.ip, d.icon, d.vendor,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
            GROUP BY d.id, d.name, d.display_name, d.ip, d.icon, d.vendor
            ORDER BY total_usage DESC
            LIMIT ?
        """
        
        rows = conn.execute(sql, [start_time, end_time, limit]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[2] or r[1],
                "ip": r[3],
                "icon": r[4],
                "vendor": r[5],
                "download": r[6],
                "upload": r[7],
                "total": r[8]
            })
            
        return items
    finally:
        conn.close()

@router.get("/usage-details")
def get_usage_details(range: str = "24h", page: int = 1, limit: int = 10):
    """
    Returns paginated device usage details.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)

        offset = (page - 1) * limit

        # Base Query
        base_query = """
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
        """

        # Total Count
        count_sql = f"SELECT COUNT(DISTINCT d.id) {base_query}"
        total_items = conn.execute(count_sql, [start_time, end_time]).fetchone()[0]
        total_pages = (total_items + limit - 1) // limit

        # Paginated Data
        data_sql = f"""
            SELECT 
                d.id, d.name, d.display_name, d.ip, d.icon, d.vendor, d.mac,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage,
                MAX(h.timestamp) as last_seen
            {base_query}
            GROUP BY d.id, d.name, d.display_name, d.ip, d.icon, d.vendor, d.mac
            ORDER BY total_usage DESC
            LIMIT ? OFFSET ?
        """
        
        rows = conn.execute(data_sql, [start_time, end_time, limit, offset]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[2] or r[1],
                "ip": r[3],
                "icon": r[4],
                "vendor": r[5],
                "mac": r[6],
                "download": r[7],
                "upload": r[8],
                "total": r[9],
                "last_seen": r[10]
            })
            
        return {
            "items": items,
            "total": total_items,
            "page": page,
            "pages": total_pages
        }
    finally:
        conn.close()

@router.get("/distribution")
def get_device_distribution():
    """
    Returns breakdown of devices by Vendor and Type.
    """
    conn = get_connection()
    try:
        # Vendor Distribution (Top 5 + Others)
        vendor_rows = conn.execute("""
            SELECT vendor, COUNT(*) as count
            FROM devices
            WHERE vendor IS NOT NULL AND vendor != '' AND vendor != 'Unknown'
            GROUP BY vendor
            ORDER BY count DESC
        """).fetchall()
        
        vendors = []
        other_count = 0
        for i, r in enumerate(vendor_rows):
            if i < 5:
                vendors.append({"label": r[0], "value": r[1]})
            else:
                other_count += r[1]
                
        if other_count > 0:
            vendors.append({"label": "Others", "value": other_count})
            
        # Device Type Distribution
        type_rows = conn.execute("""
            SELECT device_type, COUNT(*) as count
            FROM devices
            WHERE device_type IS NOT NULL AND device_type != ''
            GROUP BY device_type
            ORDER BY count DESC
        """).fetchall()
        
        types = [{"label": r[0].capitalize(), "value": r[1]} for r in type_rows]
        
        return {
            "vendors": vendors,
            "types": types
        }
    finally:
        conn.close()

@router.get("/category-usage")
def get_category_usage(range: str = "24h"):
    """
    Returns total traffic volume aggregated by device type.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(range)
        
        sql = """
            SELECT 
                d.device_type,
                SUM(h.down_rate) as total_down,
                SUM(h.up_rate) as total_up,
                (SUM(h.down_rate) + SUM(h.up_rate)) as total_usage
            FROM device_traffic_history h
            JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ? AND d.device_type IS NOT NULL AND d.device_type != ''
            GROUP BY d.device_type
            ORDER BY total_usage DESC
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        items = []
        for r in rows:
            items.append({
                "label": r[0].capitalize(),
                "download": r[1],
                "upload": r[2],
                "total": r[3]
            })
            
        return items
    finally:
        conn.close()

@router.get("/heatmap")
def get_traffic_heatmap(time_range: str = Query("24h", alias="range")):
    """
    Returns aggregated traffic volume by Day of Week and Hour of Day,
    including top 3 devices contributing to each bucket.
    """
    conn = get_connection()
    try:
        start_time, end_time, _, _ = get_date_range(time_range)
        
        # Optimized Fetch: Group by Dow, Hour, AND Device
        # This lets us calculate totals AND find top contributors in one pass
        sql = """
            SELECT 
                extract('isodow' from h.timestamp) as dow,
                extract('hour' from h.timestamp) as h,
                h.device_id,
                d.name,
                d.display_name,
                SUM(h.down_rate + h.up_rate) as total
            FROM device_traffic_history h
            LEFT JOIN devices d ON h.device_id = d.id
            WHERE h.timestamp >= ? AND h.timestamp <= ?
            GROUP BY extract('isodow' from h.timestamp), extract('hour' from h.timestamp), h.device_id, d.name, d.display_name
        """
        
        rows = conn.execute(sql, [start_time, end_time]).fetchall()
        
        # Python Aggregation
        # matrix[d][h] = { total: 0, devices: [] }
        matrix = [[{"total": 0, "devices": []} for _ in range(24)] for _ in range(7)]
        
        # Temp storage to aggregate per bucket before sorting
        # bucket_map[(d, h)] = [ {name, val}, ... ]
        bucket_devices = {}

        for r in rows:
            if r[0] is not None and r[1] is not None:
                d_idx = int(r[0]) - 1 # 0-6
                h_idx = int(r[1])     # 0-23
                if 0 <= d_idx <= 6 and 0 <= h_idx <= 23:
                    val = r[5] or 0
                    device_name = r[4] or r[3] or "Unknown"
                    
                    # Add to total
                    matrix[d_idx][h_idx]["total"] += val
                    
                    # Add to device list
                    key = (d_idx, h_idx)
                    if key not in bucket_devices: bucket_devices[key] = []
                    bucket_devices[key].append({"name": device_name, "value": val})

        # Sort and pick top 3 for each bucket
        for (d, h), devices in bucket_devices.items():
            # Sort by value desc
            devices.sort(key=lambda x: x["value"], reverse=True)
            matrix[d][h]["devices"] = devices[:3]

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        series = []
        
        for i, day in enumerate(days):
            data_points = []
            for h in range(24):
                cell = matrix[i][h]
                data_points.append({
                    "x": f"{h:02d}:00", 
                    "y": cell["total"],
                    "top": cell["devices"] # Pass top devices to frontend
                })
            series.append({"name": day, "data": data_points})
            
        return series
    finally:
        conn.close()

def get_date_range(range_str: str, now: Optional[datetime] = None):
    if not now:
        now = datetime.now()
    
    # Defaults
    start = now - timedelta(hours=24)
    end = now
    bucket = "1 hour"
    trunc = "hour"

    if range_str == "24h":
        start = now - timedelta(hours=24)
        bucket = "1 hour"
        trunc = "hour"
    elif range_str == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        bucket = "1 hour"
        trunc = "hour"
    elif range_str == "7d":
        start = now - timedelta(days=7)
        bucket = "6 hours"
        trunc = "hour"
    elif range_str == "30d":
        start = now - timedelta(days=30)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "3m":
        start = now - timedelta(days=90)
        bucket = "1 week"
        trunc = "week" # DuckDB supports week? Yes uses isodow or similar, but date_trunc('week',...) works usually
    elif range_str == "mtd":
        start = datetime(now.year, now.month, 1)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "last_month":
        # First day of this month
        this_month_first = datetime(now.year, now.month, 1)
        # Last day of prev month = this_month_first - resolution
        end = this_month_first - timedelta(seconds=1)
        # First day of prev month
        start = datetime(end.year, end.month, 1)
        bucket = "1 day"
        trunc = "day"
    elif range_str == "ytd":
        start = datetime(now.year, 1, 1)
        bucket = "1 month"
        trunc = "month" # date_trunc('month',...)
    elif range_str == "1y":
        start = now - timedelta(days=365)
        bucket = "1 month"
        trunc = "month"
    elif range_str == "all":
        start = datetime(2020, 1, 1) # Arbitrary old date
        bucket = "1 month"
        trunc = "month"

    return start, end, bucket, trunc
