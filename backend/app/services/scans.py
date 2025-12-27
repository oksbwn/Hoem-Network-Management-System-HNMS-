import json
import asyncio
import nmap  # from python-nmap
from uuid import uuid4
from datetime import datetime, timezone
from app.core.db import get_connection

def _build_nmap_args(scan_type: str) -> dict:
    if scan_type == "arp":
        return {"arguments": "-sn"}
    elif scan_type == "ping":
        return {"arguments": "-sn"}
    elif scan_type == "tcp-syn":
        return {"arguments": "-sS -Pn -T4 --top-ports 1000"}
    else:
        return {"arguments": "-sn"}

async def run_scan_job(scan_id: str, target: str, scan_type: str) -> None:
    conn = get_connection()
    nm = nmap.PortScanner()
    args = _build_nmap_args(scan_type)
    # run blocking nmap scan in a thread
    await asyncio.to_thread(nm.scan, hosts=target, **args)

    now = datetime.now(timezone.utc)

    for host in nm.all_hosts():
        state = nm[host].state()
        if state != "up":
            continue

        ip = host
        mac = nm[host]["addresses"].get("mac")
        hostname = nm[host].hostname() or None

        ports_list: list[dict] = []
        if "tcp" in nm[host]:
            for port, pdata in nm[host]["tcp"].items():
                if pdata.get("state") != "open":
                    continue
                ports_list.append(
                    {
                        "port": port,
                        "protocol": "tcp",
                        "service": pdata.get("name"),
                    }
                )

        result_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO scan_results
            (id, scan_id, ip, mac, hostname, open_ports, os, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                result_id,
                scan_id,
                ip,
                mac,
                hostname,
                json.dumps(ports_list) if ports_list else None,
                None,
                now,
                now,
            ],
        )

        # upsert device
        row = conn.execute(
            "SELECT id, first_seen FROM devices WHERE ip = ?", [ip]
        ).fetchone()
        if row:
            device_id, first_seen = row
            conn.execute(
                """
                UPDATE devices
                SET mac = COALESCE(?, mac),
                    last_seen = ?
                WHERE id = ?
                """,
                [mac, now, device_id],
            )
        else:
            device_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO devices (id, ip, mac, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                [device_id, ip, mac, now, now],
            )
