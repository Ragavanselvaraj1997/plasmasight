import time
import json
import random
import threading
from kafka import KafkaProducer
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SensorSimulator:
    def __init__(self, bootstrap_servers='localhost:9092', topic='sensor.raw'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic
        self.running = False
        
        # Initial states
        self.state = {
            'rf_power': 1000.0,  # Watts
            'chamber_pressure': 50.0, # mTorr
            'gas_flow_sf6': 100.0, # sccm
            'gas_flow_o2': 20.0,   # sccm
            'temperature': 300.0   # Kelvin
        }

    def _update_state(self):
        # Random walk simulation
        self.state['rf_power'] += random.uniform(-5, 5)
        self.state['chamber_pressure'] += random.uniform(-0.5, 0.5)
        self.state['gas_flow_sf6'] += random.uniform(-1, 1)
        self.state['gas_flow_o2'] += random.uniform(-0.5, 0.5)
        self.state['temperature'] += random.uniform(-0.1, 0.1)

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        logging.info(f"Starting Sensor Simulator, publishing to {self.topic}")
        while self.running:
            self._update_state()
            message = {
                'sensor_id': 'chamber_1_plc',
                'timestamp': datetime.utcnow().isoformat(),
                'data': self.state
            }
            try:
                self.producer.send(self.topic, message)
                logging.debug(f"Sent: {message}")
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
            
            time.sleep(0.01) # 100Hz (10ms)

    def stop(self):
        self.running = False
        self.producer.close()

if __name__ == "__main__":
    # Wait for Kafka to start in Docker
    time.sleep(10)
    sim = SensorSimulator(bootstrap_servers='localhost:9092')
    try:
        sim.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
