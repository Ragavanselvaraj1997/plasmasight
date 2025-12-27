import json
import time
import threading
import logging
import base64
import numpy as np
import cv2
import redis
import pymongo
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime, timedelta
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StreamProcessor:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.consumer_sensor = KafkaConsumer(
            'sensor.raw',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.consumer_image = KafkaConsumer(
            'image.raw',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Connect to DBs
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
            self.mongo_db = self.mongo_client['plasma_etch']
            self.mongo_col = self.mongo_db['archived_features']
        except Exception as e:
            logging.error(f"DB Connection failed: {e}")

        self.sensor_buffer = deque(maxlen=1000) # Buffer last ~10s of sensor data
        self.running = False

    def _process_sensor_stream(self):
        for msg in self.consumer_sensor:
            if not self.running: break
            data = msg.value
            # Parse timestamp
            ts = datetime.fromisoformat(data['timestamp'])
            self.sensor_buffer.append((ts, data['data']))

    def _extract_image_features(self, b64_img):
        # Decode
        try:
            img_bytes = base64.b64decode(b64_img)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Feature: Average Color
            mean_color = cv2.mean(img)[:3]
            
            # Feature: Edge Density (Canny)
            edges = cv2.Canny(img, 100, 200)
            edge_density = np.sum(edges) / (img.shape[0] * img.shape[1])
            
            return {
                'mean_r': mean_color[2],
                'mean_g': mean_color[1],
                'mean_b': mean_color[0],
                'edge_density': float(edge_density)
            }
        except Exception as e:
            logging.error(f"Image processing error: {e}")
            return {}

    def _sync_and_process(self):
        for msg in self.consumer_image:
            if not self.running: break
            img_data = msg.value
            img_ts = datetime.fromisoformat(img_data['timestamp'])
            
            # Find closest sensor reading
            best_sensor = None
            min_diff = timedelta(seconds=1)
            
            # In a real system, we'd use a better search or index
            # This is a naive O(N) scan of the buffer
            current_buffer = list(self.sensor_buffer) # Snapshot
            for sensor_ts, sensor_val in current_buffer:
                diff = abs(sensor_ts - img_ts)
                if diff < min_diff:
                    min_diff = diff
                    best_sensor = sensor_val
            
            if best_sensor and min_diff.total_seconds() < 0.2: # 200ms tolerance
                # Extract features
                img_feats = self._extract_image_features(img_data['image_data'])
                
                # Create Unified Feature Vector
                unified_features = {
                    'timestamp': img_ts.isoformat(),
                    'sensor': best_sensor,
                    'image': img_feats
                }
                
                # 1. Publish to Sync Topic (for Inference)
                self.producer.send('sync.frame', unified_features)
                
                # 2. Cache in Redis
                try:
                    self.redis_client.set('latest_features', json.dumps(unified_features))
                except: pass

                # 3. Archive to MongoDB
                try:
                    self.mongo_col.insert_one(unified_features)
                except: pass
                
                logging.info(f" synced frame at {img_ts}")
            else:
                logging.warning(f"Could not sync image at {img_ts} with sensors (diff: {min_diff})")

    def start(self):
        self.running = True
        t1 = threading.Thread(target=self._process_sensor_stream)
        t2 = threading.Thread(target=self._sync_and_process)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

if __name__ == "__main__":
    # Wait for services
    time.sleep(15)
    processor = StreamProcessor(bootstrap_servers='localhost:9092')
    try:
        processor.start()
    except KeyboardInterrupt:
        processor.running = False
