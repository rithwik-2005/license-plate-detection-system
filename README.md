#  License Plate Detection App

A Flask web application for detecting and recognizing license plates in videos using YOLO and PaddleOCR.

##  Features

-  Upload video files (MP4, AVI, MOV)
-  Real-time license plate detection using YOLO
-  OCR text recognition using PaddleOCR
-  Export detected plates to Excel
-  Real-time processing progress bar
-  Processed video playback in browser
-  Web-based interface
-  Docker support for easy deployment

##  Tech Stack

- **Backend:** Flask (Python)
- **Detection:** YOLOv8
- **OCR:** PaddleOCR
- **Visualization:** OpenCV, cvzone
- **Data:** Pandas, Openpyxl
- **Deployment:** Docker, Docker Compose

##📋 Prerequisites

- Python 3.9+
- Docker & Docker Compose (for containerized deployment)
- 4GB+ RAM
- 30GB+ storage (for models)

##  Quick Start

### Local Installation

1. **Clone repository**
```bash
git clone https://github.com/YOUR_USERNAME/license-plate-detection.git
cd license-plate-detection
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run application**
```bash
python app.py
```

5. **Access app**
```
http://localhost:5000
```

### Docker Installation

```bash
# Build image
docker build -t license-plate-detection .

# Run container
docker-compose up -d

# Access app at http://localhost:5000
```

##  Project Structure

```
license-plate-detection/
├── app.py                    # Flask application
├── best.pt                   # YOLOv8 model
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .gitignore              # Git ignore rules
├── .env.example            # Environment variables example
│
├── templates/
│   ├── index.html          # Upload page
│   ├── progress.html       # Progress tracking page
│   └── result.html         # Results display page
│
├── static/                 # Generated files (videos, excel)
└── uploads/               # Temporary uploads
```

##  Configuration

Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` with your settings.

##  How It Works

1. **Upload Video** → User selects video file
2. **Processing** → App processes frames with YOLO + PaddleOCR
3. **Progress Tracking** → Real-time progress bar
4. **Results** → 
   - Processed video with annotations
   - Excel file with detected plates
5. **Download** → User downloads results

##  AWS Deployment (Free Tier)

See [AWS Deployment Guide](./AWS_DEPLOYMENT.md) for complete instructions.

### Quick AWS Deploy

```bash
# On EC2 instance
git clone https://github.com/YOUR_USERNAME/license-plate-detection.git
cd license-plate-detection
docker build -t license-plate-detection .
docker-compose up -d
```

Access at: `http://your-ec2-ip`

##  Usage

### API Endpoints

- `GET /` - Home page with upload form
- `POST /` - Upload and process video
- `/progress/<session_id>` - Get processing progress
- `/check-status/<session_id>` - Check completion status
- `/result/<video_file>/<excel_file>` - View results
- `/static/<filename>` - Download files

##  Model Details

- **YOLO Model:** best.pt (custom trained)
- **Detection Classes:** numberplate, license_plate, plate
- **OCR Engine:** PaddleOCR
- **Input:** Video files
- **Output:** 
  - Annotated MP4 video
  - Excel file with plates

##  Example Output

### Excel File Columns
| Timestamp | ID | Plate |
|-----------|----|----|
| 2024-01-15 10:30:45 | 1 | HR26C06869 |
| 2024-01-15 10:31:02 | 2 | KA01AB1234 |

### Video Annotations
- Bounding boxes around plates
- Plate numbers displayed
- Tracking IDs shown
- Timestamp information

##  Performance Settings

Edit `app.py` to adjust:
- `output_fps = fps / 2` - Change video speed
- `scale=1.5` - Change text size
- `frame_count % 3` - Skip frames ratio

##  Troubleshooting

### Video not loading
- Check browser console (F12)
- Ensure MP4 codec is supported
- Clear browser cache

### High memory usage
- Reduce frame processing rate
- Use smaller video files
- Increase cleanup frequency

### Docker build fails
```bash
docker build --no-cache -t license-plate-detection .
```

##  Dependencies

See `requirements.txt` for full list:
- Flask 2.3.2
- OpenCV 4.8.0
- YOLOv8 (ultralytics)
- PaddleOCR 2.7.0
- Pandas 2.0.3
- And more...

##  License

MIT License - Feel free to use for personal/commercial projects

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

##  Support

For issues or questions:
1. Check existing GitHub issues
2. Create new issue with details
3. Include screenshots/logs if possible

##  Learning Resources

- [YOLO Documentation](https://docs.ultralytics.com/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)

##  Future Enhancements

- [ ] Real-time camera feed detection
- [ ] Database storage for plates
- [ ] Web API for detection
- [ ] Batch processing
- [ ] Performance metrics dashboard
- [ ] Custom model training guide

---

**Made with  for vehicle recognition**
