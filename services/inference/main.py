import json
import torch
import threading
import logging
from kafka import KafkaConsumer, KafkaProducer
from fastapi import FastAPI
from pydantic import BaseModel
from .model import EtchDepthModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Global Model State
model = EtchDepthModel()
try:
    model.load_state_dict(torch.load('model.pth'))
except:
    pass # Use random weights if no file
model.eval()

# Kafka
producer = None
consumer = None

class PredictionRequest(BaseModel):
    sensor: dict
    image: dict

@app.on_event("startup")
def startup_event():
    global producer, consumer
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    # Start consumer thread
    threading.Thread(target=consume_and_predict, daemon=True).start()

def consume_and_predict():
    consumer = KafkaConsumer(
        'sync.frame',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    for msg in consumer:
        frame = msg.value
        try:
            # Extract features -> Tensor
            # Assuming sensor data order: rf_power, chamber_pressure, gas_flow_sf6, gas_flow_o2, temperature
            # And image: mean_r, mean_g, mean_b, edge_density
            
            s = frame['sensor']
            i = frame['image']
            
            # Simple list construction - robust implementations would use names
            features = [
                s.get('rf_power', 0), s.get('chamber_pressure', 0),
                s.get('gas_flow_sf6', 0), s.get('gas_flow_o2', 0), s.get('temperature', 0),
                i.get('mean_r', 0), i.get('mean_g', 0), i.get('mean_b', 0), i.get('edge_density', 0)
            ]
            
            tensor = torch.tensor([features], dtype=torch.float32)
            
            with torch.no_grad():
                depth = model(tensor).item()
            
            result = {
                'timestamp': frame['timestamp'],
                'predicted_depth': depth,
                'uncertainty': 0.05 # Dummy uncertainty for now
            }
            
            # Push to inference.result
            producer.send('inference.result', result)
            logging.info(f"Predicted depth: {depth:.4f} um")
            
        except Exception as e:
            logging.error(f"Prediction error: {e}")

@app.post("/api/v1/predict/etch-depth")
def predict_endpoint(req: PredictionRequest):
    # Similar logic for HTTP - DRY in real implementation
    s = req.sensor
    i = req.image
    features = [
        s.get('rf_power', 0), s.get('chamber_pressure', 0),
        s.get('gas_flow_sf6', 0), s.get('gas_flow_o2', 0), s.get('temperature', 0),
        i.get('mean_r', 0), i.get('mean_g', 0), i.get('mean_b', 0), i.get('edge_density', 0)
    ]
    tensor = torch.tensor([features], dtype=torch.float32)
    with torch.no_grad():
        depth = model(tensor).item()
    return {"predicted_depth": depth}
