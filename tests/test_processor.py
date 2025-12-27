import pytest
from services.processor.processor import StreamProcessor

def test_feature_extraction():
    p = StreamProcessor()
    # Mock image (small white square)
    import base64
    import numpy as np
    import cv2
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = 255
    _, buf = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(buf).decode('utf-8')
    
    feats = p._extract_image_features(b64)
    assert 'mean_r' in feats
    assert feats['mean_r'] > 250 # Should be near 255
