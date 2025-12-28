import paho.mqtt.client as mqtt
import json
from typing import Any
from app.core.config import get_settings
from app.core.db import get_connection

def get_mqtt_config():
    settings = get_settings()
    conn = get_connection()
    try:
        keys = ['mqtt_broker', 'mqtt_port', 'mqtt_base_topic', 'mqtt_username', 'mqtt_password']
        rows = conn.execute("SELECT key, value FROM config WHERE key IN ({})".format(','.join(['?']*len(keys))), keys).fetchall()
        config = {r[0]: r[1] for r in rows}
        
        return {
            'broker': config.get('mqtt_broker') or getattr(settings, 'mqtt_broker', 'localhost'),
            'port': int(config.get('mqtt_port') or getattr(settings, 'mqtt_port', 1883)),
            'base_topic': config.get('mqtt_base_topic') or getattr(settings, 'mqtt_base_topic', 'network_scanner'),
            'username': config.get('mqtt_username') or getattr(settings, 'mqtt_username', None),
            'password': config.get('mqtt_password') or getattr(settings, 'mqtt_password', None)
        }
    finally:
        conn.close()

def get_mqtt_client():
    settings = get_settings()
    config = get_mqtt_config()
    client_id = f"{settings.app_name.lower().replace(' ', '_')}_backend"
    
    # Use standard client for 1.x compatibility
    client = mqtt.Client(client_id=client_id)
    
    if config['username']:
        client.username_pw_set(config['username'], config['password'])
        
    return client

def publish_mqtt(topic: str, payload: Any, retain: bool = False):
    config = get_mqtt_config()
    try:
        client = get_mqtt_client()
        client.connect(config['broker'], config['port'], 60)
        
        msg = payload if isinstance(payload, str) else json.dumps(payload)
        client.publish(topic, msg, retain=retain)
        client.disconnect()
    except Exception as e:
        print(f"Failed to publish to {topic}: {e}")

def publish_ha_discovery(device_info: dict):
    config = get_mqtt_config()
    mac = device_info.get("mac")
    if not mac: return
    
    mac_slug = mac.replace(":", "").lower()
    base_topic = config['base_topic']
    
    # Use binary_sensor with connectivity class for reliable "online/offline" behavior
    discovery_topic = f"homeassistant/binary_sensor/{base_topic}_{mac_slug}/config"
    
    discovery_payload = {
        "name": device_info.get("hostname") or device_info.get("ip") or f"Device {mac}",
        "state_topic": f"{base_topic}/device/{mac_slug}/state",
        "json_attributes_topic": f"{base_topic}/device/{mac_slug}/attributes",
        "unique_id": f"{base_topic}_{mac_slug}",
        "device": {
            "identifiers": [mac_slug],
            "name": device_info.get("hostname") or f"Device {mac}",
            "model": device_info.get("vendor", "Generic Network Device"),
            "manufacturer": "HNMS Network Scanner",
            "sw_version": "1.0.0"
        },
        "payload_on": "home",
        "payload_off": "not_home",
        "device_class": "connectivity"
    }
    
    publish_mqtt(discovery_topic, discovery_payload, retain=True)

def publish_device_status(device_info: dict, status: str):
    config = get_mqtt_config()
    mac = device_info.get("mac")
    
    # We need a slug for the topic
    if mac:
        key = mac.replace(":", "").lower()
    else:
        key = device_info.get("ip", "unknown").replace(".", "_")
    
    base_topic = config['base_topic']
    state_topic = f"{base_topic}/device/{key}/state"
    attr_topic = f"{base_topic}/device/{key}/attributes"
    
    # 'home'/'not_home' are standard for presence/connectivity
    state_val = "home" if status == "online" else "not_home"
    
    # 1. Publish state and attributes
    publish_mqtt(state_topic, state_val, retain=True)
    publish_mqtt(attr_topic, device_info, retain=True)
    
    # 2. Publish legacy event for backwards compatibility (optional but safe)
    legacy_topic = f"device/{status}"
    publish_mqtt(f"{base_topic}/{legacy_topic}", device_info)
    
    # 3. Handle HA Discovery
    if status == "online":
        publish_ha_discovery(device_info)

def publish_device_online(device_info: dict):
    publish_device_status(device_info, "online")

def publish_device_offline(device_info: dict):
    publish_device_status(device_info, "offline")
