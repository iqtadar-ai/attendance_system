import cv2
import numpy as np
from ultralytics import YOLO
import face_recognition

# ==========================================
# 1. LOAD THE AI MODEL
# ==========================================
# Load the YOLO anti-spoofing model into memory when the server starts.
try:
    spoof_model = YOLO('model/best.pt') 
except Exception as e:
    print(f"Warning: YOLO model failed to load. Error: {e}")


# ==========================================
# 2. ANTI-SPOOFING (Is it a live human?)
# ==========================================
def is_real_face(image_to_check):
    """
    Analyzes the webcam image to see if the person is real or a photo on a screen.
    """
    # Ask YOLO to evaluate the image (verbose=False keeps the terminal clean)
    results = spoof_model.predict(image_to_check, verbose=False)
    
    if not results:
        return False
        
    class_name = ""
        
    # Step A: Check if YOLO is acting as a Classification model (returns probabilities)
    if hasattr(results[0], 'probs') and results[0].probs is not None:
        top_class_id = results[0].probs.top1
        class_name = results[0].names[top_class_id]
        
    # Step B: Check if YOLO is acting as an Object Detection model (returns bounding boxes)
    elif hasattr(results[0], 'boxes') and len(results[0].boxes) > 0:
        # Find the bounding box the AI is most confident about
        best_box_idx = results[0].boxes.conf.argmax() 
        class_id = int(results[0].boxes.cls[best_box_idx])
        class_name = results[0].names[class_id]
        
    else:
        # If it didn't find any faces, deny access
        return False
        
    # Step C: Verify the result
    # Convert to lowercase and remove spaces so "Real" and " real " are treated identically.
    safe_class_name = class_name.lower().strip()
    
    # If YOLO labeled the face as 'real', let them in. Otherwise, block them.
    return safe_class_name in ["real", "live", "genuine", "0"]


# ==========================================
# 3. FACE RECOGNITION (Who is this person?)
# ==========================================
def get_face_encoding(image):
    """
    Finds a face in the image and translates it into a mathematical array (Face Math).
    """
    # Webcams use BGR colors, but the recognition library needs RGB. We convert it here.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Locate where the face is in the picture
    boxes = face_recognition.face_locations(rgb_image)
    
    # If no face is found, return empty data
    if not boxes:
        return None, None, None
    
    # Translate the face into a 128-number mathematical array (the 'encoding')
    encoding = face_recognition.face_encodings(rgb_image, boxes)[0]
    
    # We return the encoding. 
    # (The two 'None's are just placeholders so we don't break our app.py logic!)
    return encoding, None, None