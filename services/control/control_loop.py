import json
import time
import logging
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0
        self.last_time = time.time()

    def update(self, error):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt <= 0: dt = 1e-3
        
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        
        self.prev_error = error
        self.last_time = current_time
        return output

class ControlLoop:
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.consumer = KafkaConsumer(
            'inference.result',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Target trajectory (simple constant rate for now)
        # e.g., etch rate = 2 micron/min -> 0.033 micron/sec
        self.target_depth_rate = 0.033 
        self.start_time = datetime.utcnow()
        
        # Controllers
        self.pid_rf = PIDController(kp=10.0, ki=1.0, kd=0.5)
        self.pid_gas = PIDController(kp=2.0, ki=0.5, kd=0.1)

    def _get_target_depth(self):
        # Calculate expected depth based on time running
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        return elapsed * self.target_depth_rate

    def _check_safety(self, delta_rf, delta_gas):
        # Clamp values
        MAX_RF_DELTA = 50.0
        MAX_GAS_DELTA = 5.0
        
        safe_rf = max(min(delta_rf, MAX_RF_DELTA), -MAX_RF_DELTA)
        safe_gas = max(min(delta_gas, MAX_GAS_DELTA), -MAX_GAS_DELTA)
        
        blocked = False
        if safe_rf != delta_rf or safe_gas != delta_gas:
            logging.warning("Control actions clamped by Safety Guard")
            blocked = True
            
        return safe_rf, safe_gas, blocked

    def start(self):
        logging.info("Starting Control Loop")
        for msg in self.consumer:
            result = msg.value
            predicted_depth = result['predicted_depth']
            
            target = self._get_target_depth()
            error = target - predicted_depth
            
            # Compute Deltas
            d_rf = self.pid_rf.update(error)
            d_gas = self.pid_gas.update(error)
            
            # Safety Check
            safe_rf, safe_gas, safety_trigger = self._check_safety(d_rf, d_gas)
            
            command = {
                'timestamp': datetime.utcnow().isoformat(),
                'target_depth': target,
                'predicted_depth': predicted_depth,
                'error': error,
                'actuation': {
                    'delta_rf': safe_rf,
                    'delta_gas': safe_gas
                },
                'safety_intervention': safety_trigger
            }
            
            # Send Command
            self.producer.send('control.command', command)
            logging.info(f"Cmd Sent: RF={safe_rf:.2f}, Gas={safe_gas:.2f}, Err={error:.4f}")

if __name__ == "__main__":
    time.sleep(20) # Wait for others
    loop = ControlLoop(bootstrap_servers='localhost:9092')
    try:
        loop.start()
    except KeyboardInterrupt:
        pass
