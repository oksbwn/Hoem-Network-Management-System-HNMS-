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
    1883: "MQTT",
    3000: "React/Vite",
    3306: "MySQL",
    3389: "RDP",
    5000: "API/Flask",
    5432: "PostgreSQL",
    8000: "Web",
    8001: "Scanner API",
    8080: "HTTP-Alt",
    8883: "MQTT/S",
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
            arp_table = get_arp_table()
            
            for ip in up_ips:
                discovered_devices.append({
                    "ip": ip,
                    "mac": arp_table.get(ip),
                    "hostname": None
                })

        # 3. Process Results
        unique_devices = {d["ip"]: d for d in discovered_devices}.values()
        mac_count = sum(1 for d in unique_devices if d["mac"])
        print(f"DEBUG: Found {len(unique_devices)} unique devices. MACs found: {mac_count}")

        for device in unique_devices:
            ip = device["ip"]
            mac = device["mac"]
            
            # 4. Resolve Hostname & Trace Ports
            hostname = await resolve_hostname(ip)
            ports_list = await scan_ports(ip)

            result_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO scan_results
                (id, scan_id, ip, mac, hostname, open_ports, os, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [result_id, scan_id, ip, mac, hostname, json.dumps(ports_list), None, now, now]
            )

            # 5. Persist Open Ports to separate table for long-term tracking
            for p in ports_list:
                conn.execute(
                    """
                    INSERT INTO device_ports (device_id, port, protocol, service, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [mac or ip, p["port"], p["protocol"], p["service"], now]
                )

            # upsert device
            from app.services.devices import upsert_device_from_scan
            await upsert_device_from_scan(ip, mac, hostname, ports_list)
            
    except Exception as e:
        print(f"DEBUG ERROR in run_scan_job {scan_id}: {e}")
        # We don't raise here usually to let the worker handle the next job, 
        # but the worker also has a try-except. Actually, raising is better for worker's error logging.
        raise e
    finally:
        conn.close()
