import cv2
from ultralytics import YOLO
import cvzone
from paddleocr import PaddleOCR
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import re
import time
import threading

app = Flask(__name__)

# Create folders if they don't exist
STATIC_FOLDER = os.path.join(app.root_path, 'static')
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load YOLO and PaddleOCR
print("[INFO] Loading YOLO model...")
model = YOLO('best.pt')
names = model.names

print("[INFO] Loading PaddleOCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

# Global variable to track processing status
processing_status = {}

def cleanup_old_files(folder, days=7):
    """Delete files older than specified days"""
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            if os.stat(file_path).st_mtime < now - days * 86400:
                try:
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted old file: {filename}")
                except:
                    pass

def process_video(input_path, session_id):
    """Process video and return paths to output video and excel file"""
    try:
        # Prepare filenames
        now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = f"plates_{now_str}.xlsx"
        video_filename = f"detected_{now_str}.mp4"
        excel_path = os.path.join(STATIC_FOLDER, log_filename)
        video_path = os.path.join(STATIC_FOLDER, video_filename)

        saved_ids = set()
        id_to_plate = {}
        log_data = []

        # Load video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Slow down video by reducing FPS (half speed)
        output_fps = fps / 2
        
        print(f"[INFO] Original FPS: {fps}, Output FPS: {output_fps}, Size: {frame_width}x{frame_height}, Total Frames: {total_frames}")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        out = cv2.VideoWriter(video_path, fourcc, output_fps, (frame_width, frame_height))
        
        # If H264 fails, try mp4v
        if not out.isOpened():
            print("[WARNING] H264 codec not available, trying mp4v...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, output_fps, (frame_width, frame_height))
        
        if not out.isOpened():
            cap.release()
            raise ValueError("Could not initialize video writer")

        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            
            # Update progress
            progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
            processing_status[session_id] = {
                'progress': progress,
                'status': 'processing',
                'frames': f"{frame_count}/{total_frames}"
            }
            
            # Skip frames for performance
            if frame_count % 3 != 0:
                out.write(frame)
                continue

            results = model.track(frame, persist=True)

            if results[0].boxes.id is not None:
                ids = results[0].boxes.id.cpu().numpy().astype(int)
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                class_ids = results[0].boxes.cls.int().cpu().tolist()

                for track_id, box, class_id in zip(ids, boxes, class_ids):
                    x1, y1, x2, y2 = box
                    label = names[class_id]

                    # Draw bounding box and label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cvzone.putTextRect(frame, f'{label.upper()}', (x1, y1 - 10), scale=1.5, thickness=3,
                                       colorT=(255, 255, 255), colorR=(0, 0, 255), offset=5, border=2)

                    # Detect and recognize number plate text
                    if label.lower() in ["numberplate", "license_plate", "plate"]:
                        cropped_plate = frame[y1:y2, x1:x2]
                        if cropped_plate.size == 0:
                            continue

                        if track_id not in id_to_plate:
                            try:
                                result = ocr.predict(cropped_plate)
                                plate_text = ""

                                # Extract detected text
                                if result and isinstance(result, list) and len(result) > 0 and "rec_texts" in result[0]:
                                    rec_texts = result[0]["rec_texts"]
                                    # Join texts without spaces
                                    plate_text = "".join(rec_texts)
                                    plate_text = plate_text.upper()
                                    # Remove all non-alphanumeric characters
                                    plate_text = re.sub(r'[^A-Z0-9]', '', plate_text)
                                    
                                    # Filter: Indian plates are typically 9-12 characters
                                    if len(plate_text) >= 9:
                                        # Try to extract valid plate pattern
                                        match = re.search(r'[A-Z]{2}\d{2}[A-Z]{1,2}\d{4,5}', plate_text)
                                        if match:
                                            plate_text = match.group(0)
                                        else:
                                            # Fallback: take first 10 chars if it starts with letters
                                            if plate_text[0:2].isalpha():
                                                plate_text = plate_text[:10]
                                            else:
                                                plate_text = ""
                                    else:
                                        plate_text = ""
                                    
                                    print(f"Full Plate: {plate_text}")

                                if plate_text:
                                    id_to_plate[track_id] = plate_text
                                    if track_id not in saved_ids:
                                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        log_data.append({"Timestamp": timestamp, "ID": track_id, "Plate": plate_text})
                                        saved_ids.add(track_id)
                                        print(f"Saved: ID={track_id}, Plate={plate_text}")
                            except Exception as e:
                                print(f"[ERROR] OCR failed: {str(e)}")

                        # Display detected plate text on video (with larger text)
                        if track_id in id_to_plate:
                            plate_text = id_to_plate[track_id]
                            label_text = f"ID: {track_id} | {plate_text}"
                            cvzone.putTextRect(frame, label_text, (x1, y2 + 10), scale=1.5, thickness=3,
                                               colorT=(0, 0, 0), colorR=(255, 255, 0), offset=5, border=2)

            out.write(frame)

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        # Write data to Excel once at the end
        if log_data:
            df = pd.DataFrame(log_data)
            df.to_excel(excel_path, index=False)
            print(f"[INFO] Excel saved with {len(log_data)} records")

        print(f"[INFO] Processed {frame_count} frames")
        
        # Update status to completed
        processing_status[session_id] = {
            'progress': 100,
            'status': 'completed',
            'video_file': video_filename,
            'excel_file': log_filename
        }
        
        return video_filename, log_filename
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        processing_status[session_id] = {
            'progress': 0,
            'status': 'error',
            'message': str(e)
        }
        raise

# =====================
# FLASK ROUTES
# =====================
@app.route('/', methods=['GET', 'POST'])
def index():
    # Cleanup old files every time app starts
    cleanup_old_files(STATIC_FOLDER, days=7)
    
    if request.method == 'POST':
        if 'video' not in request.files:
            return render_template('index.html', error='No video file provided'), 400
        
        video = request.files['video']
        if video.filename == '':
            return render_template('index.html', error='No file selected'), 400

        # Create unique session ID
        session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        input_path = os.path.join(UPLOAD_FOLDER, 'input_' + session_id + '_' + video.filename)
        video.save(input_path)

        # Start processing in background thread
        thread = threading.Thread(target=process_video, args=(input_path, session_id))
        thread.start()
        
        # Redirect to progress page
        return render_template('progress.html', session_id=session_id)

    return render_template('index.html')

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get current processing progress"""
    status = processing_status.get(session_id, {'progress': 0, 'status': 'initializing'})
    return jsonify(status)

@app.route('/check-status/<session_id>')
def check_status(session_id):
    """Check if processing is complete"""
    status = processing_status.get(session_id, {})
    if status.get('status') == 'completed':
        return jsonify({
            'completed': True,
            'video_file': status.get('video_file'),
            'excel_file': status.get('excel_file')
        })
    elif status.get('status') == 'error':
        return jsonify({
            'completed': False,
            'error': True,
            'message': status.get('message', 'Unknown error')
        })
    else:
        return jsonify({
            'completed': False,
            'progress': status.get('progress', 0),
            'frames': status.get('frames', 'Starting...')
        })

@app.route('/result/<video_file>/<excel_file>')
def result(video_file, excel_file):
    """Display results page"""
    return render_template('result.html', video_path=video_file, excel_path=excel_file)

@app.route('/static/<filename>')
def static_files(filename):
    if filename.endswith('.mp4'):
        return send_from_directory(STATIC_FOLDER, filename, mimetype='video/mp4')
    elif filename.endswith('.xlsx'):
        return send_from_directory(STATIC_FOLDER, filename, as_attachment=True)
    else:
        return send_from_directory(STATIC_FOLDER, filename)

# =====================
# MAIN ENTRY POINT
# =====================
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)