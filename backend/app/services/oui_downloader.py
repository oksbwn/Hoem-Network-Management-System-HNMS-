import httpx
import re
import logging
from app.core.db import get_connection

logger = logging.getLogger(__name__)

IEEE_OUI_URL = "https://standards-oui.ieee.org/oui/oui.txt"

async def download_and_update_oui():
    """Downloads the IEEE OUI list and updates the mac_vendors table."""
    logger.info("Starting IEEE OUI database download...")
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(IEEE_OUI_URL, timeout=60.0)
            if resp.status_code != 200:
                logger.error(f"Failed to download OUI list: {resp.status_code}")
                return
            
            content = resp.text
            # Format: 00-00-00   (hex)		XEROX CORPORATION
            # Matches: 6-char hex prefix and the name after (hex)\t\t
            matches = re.findall(r"^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.*)$", content, re.MULTILINE)
            
            if not matches:
                logger.error("No OUI matches found in the downloaded file. Format might have changed.")
                return

            logger.info(f"Parsed {len(matches)} OUI entries. Updating database...")
            
            conn = get_connection()
            try:
                # Use a transaction for speed
                conn.execute("BEGIN TRANSACTION")
                # Clear old data (optional, but ensures fresh start)
                # conn.execute("DELETE FROM mac_vendors") 
                
                # Bulk insert using DuckDB's executemany (or just raw SQL if speed is an issue)
                # For 30k+ rows, a single large INSERT or using a temp table might be faster.
                # Here we use UPSERT logic:
                for oui_raw, vendor in matches:
                    # Normalize OUI to XX:XX:XX
                    oui = oui_raw.replace('-', ':').upper()
                    conn.execute(
                        "INSERT OR REPLACE INTO mac_vendors (oui, vendor, updated_at) VALUES (?, ?, now())",
                        [oui, vendor.strip()]
                    )
                
                conn.execute("COMMIT")
                logger.info("IEEE OUI database updated successfully.")
            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Failed to save OUI data to database: {e}")
            finally:
                conn.close()

    except Exception as e:
        logger.error(f"Error while updating OUI database: {e}")

async def ensure_oui_data():
    """Triggers download if the mac_vendors table is empty."""
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM mac_vendors").fetchone()[0]
        if count == 0:
            logger.info("OUI table is empty. Triggering initial download...")
            await download_and_update_oui()
    finally:
        conn.close()
