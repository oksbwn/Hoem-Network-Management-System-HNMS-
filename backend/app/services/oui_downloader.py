import httpx
import re
import logging
import asyncio
from app.core.db import get_connection

logger = logging.getLogger(__name__)

IEEE_OUI_URL = "https://standards-oui.ieee.org/oui/oui.txt"

async def download_and_update_oui():
    """Downloads the IEEE OUI list and updates the mac_vendors table."""
    logger.info("Starting IEEE OUI database download...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            resp = await client.get(IEEE_OUI_URL, timeout=60.0)
            if resp.status_code != 200:
                logger.error(f"Failed to download OUI list: {resp.status_code}")
                return
            
            content = resp.text
            matches = re.findall(r"^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.*)$", content, re.MULTILINE)
            
            if not matches:
                logger.error("No OUI matches found in the downloaded file. Format might have changed.")
                return

            logger.info(f"Parsed {len(matches)} OUI entries. Updating database...")
            
            def sync_save():
                conn = get_connection()
                try:
                    conn.execute("BEGIN TRANSACTION")
                    for oui_raw, vendor in matches:
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
                    raise e
                finally:
                    conn.close()
            
            await asyncio.to_thread(sync_save)

    except Exception as e:
        logger.error(f"Error while updating OUI database: {e}")

async def ensure_oui_data():
    """Triggers download if the mac_vendors table is empty."""
    def check_count():
        conn = get_connection()
        try:
            return conn.execute("SELECT COUNT(*) FROM mac_vendors").fetchone()[0]
        finally:
            conn.close()
            
    count = await asyncio.to_thread(check_count)
    if count == 0:
        logger.info("OUI table is empty. Triggering initial download...")
        await download_and_update_oui()
