import os
import json
import time
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from face_utils import get_face_encoding, is_real_face, face_recognition
from datetime import datetime, timezone, timedelta

# Load environment variables (API keys) securely
load_dotenv()

# Initialize the Flask web server
app = Flask(__name__)

# Connect to Supabase (our cloud database)
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def decode_image(base64_string):
    encoded_data = base64_string.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Resize to cap memory usage — 480px width is plenty for face detection
    max_width = 480
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / w
        frame = cv2.resize(frame, (max_width, int(h * scale)))
    
    return frame

# ==========================================
# WEB PAGE ROUTES (Serving the HTML)
# ==========================================

@app.route('/')
def index():
    return render_template('index.html') # Serves the main Attendance Scanner page

@app.route('/register_page')
def register_page():
    return render_template('register.html') # Serves the Admin Enrollment page


# ==========================================
# API ROUTES (The Brains of the App)
# ==========================================

@app.route('/register', methods=['POST'])
def register_student():
    """Handles securely adding a new student to the system."""
    data = request.json
    name = data.get('name')
    student_id = data.get('student_id')
    
    # Step 1: Ensure the form isn't empty
    if not name or not student_id or not data.get('image'):
        return jsonify({"error": "Missing information!"}), 400
        
    # Step 2: Decode the image and extract the facial measurements (encoding)
    frame = decode_image(data.get('image'))
    encoding, _, _ = get_face_encoding(frame)
    
    if encoding is None:
        return jsonify({"error": "No face detected in the image."}), 400
        
    # Step 3: Save the original photo to Supabase Storage (for our visual records)
    filename = f"{student_id}_{int(time.time())}.jpg"
    _, buffer = cv2.imencode('.jpg', frame)
    
    try:
        supabase.storage.from_("student-faces").upload(
            path=filename, 
            file=buffer.tobytes(), 
            file_options={"content-type": "image/jpeg"}
        )
    except Exception:
        return jsonify({"error": "Failed to upload image file to storage."}), 500

    # Step 4: Save the student's text data and Face Math into the database table
    try:
        supabase.table('students').insert({
            "name": name,
            "student_id": student_id,
            "encoding_data": json.dumps(encoding.tolist()) # Convert math array to text string
        }).execute()
        
        return jsonify({"success": True, "message": f"{name} successfully enrolled!"})
    except Exception:
        return jsonify({"error": "Registration failed. ID might already exist."}), 400


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """Handles verifying a face and recording the attendance timestamp."""
    if not request.json.get('image'):
        return jsonify({"error": "No image provided"}), 400
        
    # Step 1: Decode the webcam image and extract the facial measurements
    frame = decode_image(request.json.get('image'))
    encoding, _, _ = get_face_encoding(frame) # We use '_' to ignore extra data we don't need here
    
    if encoding is None:
        return jsonify({"error": "No face detected in frame."}), 400
        
    # Step 2: AI Security Check (YOLO checks if it's a real 3D human or a fake photo)
    if not is_real_face(frame):
        return jsonify({"error": "Spoofing detected! Live face required."}), 403
        
    # Step 3: Download all known student faces from the database
    students = supabase.table('students').select('*').execute().data
    
    if not students:
        return jsonify({"error": "No registered students found."}), 404
        
    # Group the database data into usable lists
    known_encodings = [np.array(json.loads(s['encoding_data'])) for s in students]
    
    # Step 4: Compare the live webcam face against the database faces
    matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.45)
    
    if True in matches:
        # We found a match! Find out exactly who it is.
        match_index = matches.index(True)
        matched_id = students[match_index]['student_id']
        matched_name = students[match_index]['name']
        
        # Step 5: Cooldown System (Prevent spamming attendance)
        recent_log = supabase.table('attendance').select('timestamp').eq('student_id', matched_id).order('timestamp', desc=True).limit(1).execute()
        
        if recent_log.data:
            last_time_str = recent_log.data[0]['timestamp']
            last_time = datetime.fromisoformat(last_time_str.replace('Z', '+00:00'))
            
            # If they scanned within the last 5 minutes, block the entry
            if (datetime.now(timezone.utc) - last_time) < timedelta(minutes=5):
                return jsonify({"error": f"Attendance already logged. Wait 5 minutes."}), 400
        
        # Step 6: Success! Record the timestamp in the database
        supabase.table('attendance').insert({"student_id": matched_id}).execute()
        return jsonify({"success": True, "message": f"Welcome, {matched_name}!"})
        
    # If the comparison loop finishes and no faces matched
    return jsonify({"error": "Identity not recognized. Access Denied."}), 401


if __name__ == '__main__':
    app.run(debug=True, port=5000)