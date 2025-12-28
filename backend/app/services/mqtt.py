import paho.mqtt.client as mqtt
import json
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
    
    # Use newer API version
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    
    if config['username']:
        client.username_pw_set(config['username'], config['password'])
        
    return client

def publish_event(topic_suffix: str, payload: dict):
    config = get_mqtt_config()
    full_topic = f"{config['base_topic']}/{topic_suffix}"
    
    try:
        client = get_mqtt_client()
        client.connect(config['broker'], config['port'], 60)
        client.publish(full_topic, json.dumps(payload))
        client.disconnect()
    except Exception as e:
        # We don't want to crash the scanner if MQTT is down
        print(f"Failed to publish MQTT event: {e}")

def publish_device_online(device_info: dict):
    publish_event("device/online", device_info)

def publish_device_offline(device_info: dict):
    publish_event("device/offline", device_info)
