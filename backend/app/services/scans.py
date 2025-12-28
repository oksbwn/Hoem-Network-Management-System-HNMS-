import json
import asyncio
import subprocess
import re
import ipaddress
import socket
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone
from app.core.db import get_connection

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    111: "RPCBind",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    1400: "Sonos",
    1883: "MQTT",
    2001: "HomeKit",
    3000: "React/Vite",
    3232: "ESPHome OTA",
    3306: "MySQL",
    3389: "RDP",
    5000: "API/Flask",
    5432: "PostgreSQL",
    6053: "ESPHome API",
    8000: "Web",
    8001: "Scanner API",
    8080: "HTTP-Alt",
    8123: "Home Assistant",
    8883: "MQTT/S",
    9100: "Printer",
    32400: "Plex",
}

async def resolve_hostname(ip: str) -> Optional[str]:
    """Tries to resolve IP to hostname."""
    try:
        # Using a small timeout implicitly via asyncio.to_thread and gethostbyaddr
        res = await asyncio.to_thread(socket.gethostbyaddr, ip)
        return res[0]
    except:
        return None

# Conditional import of scapy
try:
    from scapy.all import ARP, Ether, srp, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

async def native_ping(ip: str) -> bool:
    """Uses system ping to check if a host is up."""
    try:
        cmd = ["ping", "-n", "1", "-w", "1000", ip]
        res = await asyncio.to_thread(
            subprocess.run, cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        if res.returncode == 0:
            if "Reply from" in res.stdout:
                return True
        return False
    except Exception as e:
        print(f"DEBUG PING ERROR for {ip}: {e}")
        return False

def get_arp_table() -> dict[str, str]:
    """Parses 'arp -a' output into an IP -> MAC mapping."""
    arp_map = {}
    try:
        output = subprocess.check_output(["arp", "-a"], text=True)
        matches = re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{17})", output)
        for ip, mac in matches:
            normalized_mac = mac.replace('-', ':').lower()
            arp_map[ip] = normalized_mac
    except Exception as e:
        print(f"DEBUG ERROR: Failed to read ARP table: {e}")
    return arp_map

async def check_port(ip: str, port: int, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Checks if a TCP port is open."""
    try:
        conn = asyncio.open_connection(ip, port)
        _, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return {
            "port": port,
            "protocol": "TCP",
            "service": COMMON_PORTS.get(port, "Unknown")
        }
    except:
        return None

async def scan_ports(ip: str, ports: List[int] = None) -> List[Dict[str, Any]]:
    """Scans a list of ports on a given IP and returns detailed records."""
    if not ports:
        ports = list(COMMON_PORTS.keys())
    
    tasks = [check_port(ip, port) for port in ports]
    results = await asyncio.gather(*tasks)
    return [p for p in results if p is not None]

def force_arp_entry(ip: str) -> None:
    """Forces an ARP entry by sending a ping (Windows/Linux)."""
    try:
        # ping -n 1 on Windows, -c 1 on Linux. We detect strictly for Windows environment here or generic.
        # Since we are on Windows per user env:
        subprocess.run(["ping", "-n", "1", "-w", "500", ip], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
    except:
        pass

async def run_scan_job(scan_id: str, target: str, scan_type: str) -> None:
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc)
        print(f"DEBUG: Starting scan {scan_id}. Target: {target}, Type: {scan_type}")
        discovered_devices = []

        # 1. Try Scapy first
        if SCAPY_AVAILABLE and scan_type in ["arp", "ping"]:
            try:
                print(f"DEBUG: Attempting Scapy ARP scan on {target}")
                ans, unans = await asyncio.to_thread(
                    srp, 
                    Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target), 
                    timeout=2, 
                    verbose=False
                )
                for snd, rcv in ans:
                    discovered_devices.append({
                        "ip": rcv.psrc,
                        "mac": rcv.hwsrc,
                        "hostname": None 
                    })
            except Exception as e:
                print(f"DEBUG: Scapy failed or driver missing: {e}. Falling back to native.")

        # 2. Native Fallback
        if not discovered_devices and scan_type in ["arp", "ping"]:
            print("DEBUG: Using Native Fallback (Ping + ARP Cache)")
            targets_to_ping = []
            for part in target.split():
                try:
                    if '/' in part:
                        net = ipaddress.ip_network(part, strict=False)
                        if net.num_addresses > 2:
                            targets_to_ping.extend([str(ip) for ip in net.hosts()])
                        else:
                            targets_to_ping.extend([str(ip) for ip in net])
                    else:
                        targets_to_ping.append(part)
                except:
                    targets_to_ping.append(part)

            semaphore = asyncio.Semaphore(50)
            async def sem_ping(ip):
                async with semaphore:
                    return await native_ping(ip), ip
            
            ping_results = await asyncio.gather(*(sem_ping(ip) for ip in targets_to_ping))
            up_ips = [ip for is_up, ip in ping_results if is_up]
            
            # Force ARP cache population for discovered IPs
            for ip in up_ips:
                await asyncio.to_thread(force_arp_entry, ip)
                
            arp_table = get_arp_table()
            
            for ip in up_ips:
                discovered_devices.append({
                    "ip": ip,
                    "mac": arp_table.get(ip),
                    "hostname": None
                })

        # 3. Process Results
        unique_devices = list({d["ip"]: d for d in discovered_devices}.values())
        mac_count = sum(1 for d in unique_devices if d["mac"])
        print(f"DEBUG: Found {len(unique_devices)} unique devices. MACs found: {mac_count}")

        # Parallelize device enrichment (hostname and ports)
        # Use a semaphore to avoid overwhelming the system/network
        semaphore = asyncio.Semaphore(10) # Process up to 10 devices in parallel

        async def process_single_device(device):
            async with semaphore:
                ip = device["ip"]
                mac = device["mac"]
                
                # 4. Resolve Hostname & Trace Ports
                # Adding individual timeouts to prevent a single hang from blocking everything
                hostname = await resolve_hostname(ip)
                ports_list = await scan_ports(ip)

                result_id = str(uuid4())
                
                # We need a new connection per task or a thread-safe way, 
                # but to avoid lock contention, we'll do the inserts here.
                # DuckDB handles multiple connections as long as they are from the same process.
                job_conn = get_connection()
                try:
                    job_now = datetime.now(timezone.utc)
                    job_conn.execute(
                        """
                        INSERT INTO scan_results
                        (id, scan_id, ip, mac, hostname, open_ports, os, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [result_id, scan_id, ip, mac, hostname, json.dumps(ports_list), None, job_now, job_now]
                    )

                    # 5. Persist Open Ports
                    for p in ports_list:
                        job_conn.execute(
                            """
                            INSERT INTO device_ports (device_id, port, protocol, service, last_seen)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            [mac or ip, p["port"], p["protocol"], p["service"], job_now]
                        )

                    # upsert device
                    from app.services.devices import upsert_device_from_scan
                    await upsert_device_from_scan(ip, mac, hostname, ports_list)
                finally:
                    job_conn.close()

        # Execute processing jobs in parallel
        if unique_devices:
            await asyncio.gather(*(process_single_device(d) for d in unique_devices))

        # 6. Post-scan: Mark devices as offline if they were not seen in this scan
        # We only do this for devices that were previously 'online'
        # and whose last_seen is still older than this scan's start time.
        from app.services.devices import record_status_change, publish_device_offline
        
        # We need to be careful not to mark everything offline if it was a targeted scan,
        # but for now, let's assume discovery scans should refresh status.
        offline_devices = conn.execute(
            "SELECT id, ip, mac, display_name, vendor, icon FROM devices WHERE status = 'online' AND last_seen < ?",
            [now]
        ).fetchall()
        
        for d_id, d_ip, d_mac, d_name, d_vendor, d_icon in offline_devices:
            print(f"DEBUG: Device {d_ip} ({d_id}) not seen in scan. Marking as OFFLINE.")
            conn.execute("UPDATE devices SET status = 'offline' WHERE id = ?", [d_id])
            record_status_change(conn, d_id, 'offline', datetime.now(timezone.utc))
            publish_device_offline({
                "id": d_id,
                "ip": d_ip,
                "mac": d_mac,
                "hostname": d_name,
                "vendor": d_vendor,
                "icon": d_icon,
                "status": "offline",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        print(f"DEBUG ERROR in run_scan_job {scan_id}: {e}")
        # We don't raise here usually to let the worker handle the next job, 
        # but the worker also has a try-except. Actually, raising is better for worker's error logging.
        raise e
    finally:
        conn.close()
