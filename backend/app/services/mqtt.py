import paho.mqtt.client as mqtt
import json
from app.core.config import get_settings

def get_mqtt_client():
    settings = get_settings()
    broker = getattr(settings, "mqtt_broker", "localhost")
    port = getattr(settings, "mqtt_port", 1883)
    client_id = f"{settings.app_name.lower().replace(' ', '_')}_backend"
    
    # Use newer API version
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    return client

def publish_event(topic_suffix: str, payload: dict):
    settings = get_settings()
    broker = getattr(settings, "mqtt_broker", "localhost")
    port = getattr(settings, "mqtt_port", 1883)
    base_topic = getattr(settings, "mqtt_base_topic", "network_scanner")
    
    full_topic = f"{base_topic}/{topic_suffix}"
    
    try:
        client = get_mqtt_client()
        client.connect(broker, port, 60)
        client.publish(full_topic, json.dumps(payload))
        client.disconnect()
    except Exception as e:
        # We don't want to crash the scanner if MQTT is down
        print(f"Failed to publish MQTT event: {e}")

def publish_device_online(device_info: dict):
    publish_event("device/online", device_info)

def publish_device_offline(device_info: dict):
    publish_event("device/offline", device_info)
