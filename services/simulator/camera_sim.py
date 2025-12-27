import time
import json
import random
import threading
import numpy as np
import base64
import cv2
from kafka import KafkaProducer
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CameraSimulator:
    def __init__(self, bootstrap_servers='localhost:9092', topic='image.raw'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = topic
        self.running = False

    def _generate_frame(self):
        # Create a dummy image (noise + moving circle)
        img = np.zeros((256, 256, 3), dtype=np.uint8)
        
        # Add some noise
        noise = np.random.randint(0, 50, (256, 256, 3), dtype=np.uint8)
        img = cv2.add(img, noise)

        # Draw a moving circle to simulate change
        t = time.time()
        x = int(128 + 50 * np.sin(t))
        y = int(128 + 50 * np.cos(t))
        cv2.circle(img, (x, y), 30, (0, 255, 0), -1)

        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', img)
        return base64.b64encode(buffer).decode('utf-8')

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        logging.info(f"Starting Camera Simulator, publishing to {self.topic}")
        while self.running:
            frame_b64 = self._generate_frame()
            message = {
                'camera_id': 'chamber_1_cam',
                'timestamp': datetime.utcnow().isoformat(),
                'image_data': frame_b64,
                'metadata': {
                    'exposure': 5000,
                    'gain': 1.0
                }
            }
            try:
                self.producer.send(self.topic, message)
                logging.debug("Sent image frame")
            except Exception as e:
                logging.error(f"Failed to send image: {e}")
            
            time.sleep(0.1) # 10fps

    def stop(self):
        self.running = False
        self.producer.close()

if __name__ == "__main__":
    # Wait for Kafka to start
    time.sleep(10) 
    sim = CameraSimulator(bootstrap_servers='localhost:9092')
    try:
        sim.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
