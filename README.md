```markdown
# MapMind 🗺️

<div align="center">
  <img src="frontend/public/logo.png" alt="MapMind Logo" width="200"/>
  <p><strong>Intelligent Location Analysis for Smart Living Decisions</strong></p>
</div>

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Live Demo](#live-demo)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

MapMind is an advanced location analysis tool that helps users make informed decisions about where to live. By analyzing various points of interest (POIs) within a specified area, it provides comprehensive insights about the neighborhood's livability, amenities, and overall potential.

## 🎯 Key Features

- **Interactive Map Visualization**
  - Real-time POI mapping
  - Custom area selection
  - Dynamic zoom and pan controls

- **Smart Location Analysis**
  - AI-powered area evaluation
  - 15-minute city assessment
  - Proximity scoring for essential amenities

- **Data Visualization**
  - Interactive charts and graphs
  - POI distribution analysis
  - Comparative neighborhood metrics

## 🚀 Tech Stack

### Frontend
- React.js
- Mapbox GL JS
- Recharts
- TailwindCSS
- Axios

### Backend
- FastAPI
- Google Gemini AI
- Python 3.8+
- OpenStreetMap API

## 💻 Getting Started

### Prerequisites
- Python 3.8 or higher
- Node.js 14.0 or higher
- npm or yarn
- Git

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/samayp42/MapMind.git
cd MapMind
 ```
```

2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
 ```

3. Configure Environment Variables
Edit .env file in the backend directory:

```plaintext
GOOGLE_API_KEY=your_google_api_key_here
 ```

4. Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
 ```

## 🎮 Usage
1. Start Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
 ```

Backend will run at: http://localhost:8000

2. Start Frontend Development Server
```bash
cd frontend
npm start
 ```

Frontend will run at: http://localhost:3000

## 📚 API Documentation
### Analyze Area Endpoint
POST /analyze-area

Request Body:

```json
{
  "city": "New York",
  "area": "Manhattan"
}
 ```

Response:

```json
{
  "summary": "Area analysis summary...",
  "pie_chart_data": [...],
  "ai_rating": 85,
  "geocode": {...},
  "bbox": [...],
  "geojson": {...},
  "pois": {...}
}
 ```

## 📸 Screenshots
Main Dashboard View

Area Analysis Results

## 🔍 Features in Detail
### 1. Area Analysis
- Comprehensive POI mapping
- Distance calculations
- Amenity density analysis
### 2. AI Insights
- Smart area evaluation
- Livability scoring
- Future potential assessment
### 3. Visualization
- Interactive maps
- Statistical charts
- Comparative analysis
## 🛠️ Development
### Project Structure
```plaintext
MapMind/
├── backend/
│   ├── main.py           # Main FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
├── frontend/
│   ├── src/             # React source files
│   ├── public/          # Static assets
│   └── package.json     # Node.js dependencies
└── docs/
    └── screenshots/     # Application screenshots
 ```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
 ```

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch ( git checkout -b feature/AmazingFeature )
3. Commit changes ( git commit -m 'Add AmazingFeature' )
4. Push to branch ( git push origin feature/AmazingFeature )
5. Open a Pull Request
## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- OpenStreetMap for POI data
- Google Gemini AI for analysis
- Mapbox for map visualization
## 📞 Support
For support, email support@mapmind.com or join our Discord channel.

Made with ❤️ by Samay Patel
 ```
