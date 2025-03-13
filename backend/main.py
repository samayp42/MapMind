import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv
import json
import requests
import math
from urllib.parse import quote

load_dotenv()

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://map-mind.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')

def get_pois_overpass(area_name, city_name, poi_categories):
    """Get POIs using Overpass API for multiple categories within a 1km radius."""
    overpass_url = "https://overpass-api.de/api/interpreter"

    # --- 1. Define Search Area ---
    geocode_query = f"{area_name}, {city_name}"
    geocode_url = f"https://nominatim.openstreetmap.org/search?q={quote(geocode_query)}&format=json&limit=1"
    try:
        geocode_response = requests.get(geocode_url, headers={'User-Agent': 'MapMind/1.0'})
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
    except requests.RequestException as e:
        print(f"Geocoding Error: {str(e)}")
        return {"error": f"Geocoding failed: {str(e)}"}
    except json.JSONDecodeError:
        print(f"Geocoding JSON Error: {geocode_response.text}")
        return {"error": "Error decoding geocoding JSON response"}

    if not geocode_data:
        return {"error": "Could not geocode area/city"}

    geocode_lat = float(geocode_data[0].get('lat'))
    geocode_lon = float(geocode_data[0].get('lon'))
    
    # Get bounding box for the area
    bbox = None
    if 'boundingbox' in geocode_data[0]:
        bbox_raw = geocode_data[0]['boundingbox']
        # Convert to [west, south, east, north] format
        bbox = [float(bbox_raw[2]), float(bbox_raw[0]), float(bbox_raw[3]), float(bbox_raw[1])]
    else:
        # Create a bounding box around the center point (approximately 1km radius)
        radius_deg = 0.009  # ~1km at equator
        bbox = [
            geocode_lon - radius_deg,
            geocode_lat - radius_deg,
            geocode_lon + radius_deg,
            geocode_lat + radius_deg
        ]

    # --- 2. Query for POIs by Category ---
    all_pois = {}
    
    # Use a 1km radius
    search_radius = 1000
    
    for category in poi_categories:
        # Use a more confined search area with a smaller radius
        overpass_query = f"""
        [out:json];
        (
          node["amenity"="{category}"](around:{search_radius},{geocode_lat},{geocode_lon});
          way["amenity"="{category}"](around:{search_radius},{geocode_lat},{geocode_lon});
          relation["amenity"="{category}"](around:{search_radius},{geocode_lat},{geocode_lon});
        );
        out center;
        """
        
        try:
            response = requests.post(overpass_url, data=overpass_query)
            response.raise_for_status()
            data = response.json()
            
            # Extract POIs
            pois = []
            for element in data.get('elements', []):
                # Get coordinates (either directly or from center)
                if element['type'] == 'node':
                    lat, lon = element.get('lat'), element.get('lon')
                else:  # way or relation
                    center = element.get('center', {})
                    lat, lon = center.get('lat'), center.get('lon')
                
                if lat and lon:
                    # Calculate distance from center point (in meters)
                    # This is a simple approximation using the Haversine formula
                    R = 6371000  # Earth radius in meters
                    dlat = abs(lat - geocode_lat) * (3.14159/180)
                    dlon = abs(lon - geocode_lon) * (3.14159/180)
                    a = (dlat/2) * (dlat/2) + math.cos(lat * 3.14159/180) * math.cos(geocode_lat * 3.14159/180) * (dlon/2) * (dlon/2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance = R * c
                    
                    # Only include POIs within the 1km radius
                    if distance <= 1000:
                        pois.append({
                            'lat': lat,
                            'lon': lon,
                            'tags': element.get('tags', {}),
                            'distance': round(distance)  # Include distance in meters
                        })
            
            if pois:
                all_pois[category] = pois
                
        except Exception as e:
            print(f"Error fetching {category} POIs: {str(e)}")
    
    return {
        "pois": all_pois,
        "geocode": {
            "lat": geocode_lat,
            "lon": geocode_lon,
            "display_name": geocode_data[0].get('display_name', '')
        },
        "bbox": bbox
    }

def generate_complete_geojson(area_name, city_name, pois_data, bbox):
    """Generate a complete GeoJSON with boundary polygon and POIs using LLM."""
    
    # Create a prompt for the LLM to generate the GeoJSON
    prompt = f"""
    Create a complete GeoJSON FeatureCollection for {area_name}, {city_name} that includes:
    
    1. A boundary polygon feature with these properties:
       - type: "boundary"
       - name: "{area_name}, {city_name}"
       - fillColor: "#0070f3"
       - fillOpacity: 0.2
       - strokeColor: "#0070f3"
       - strokeWidth: 2
    
    2. Point features for each POI in this data:
    {json.dumps(pois_data, indent=2)}
    
    The boundary should be a simple polygon that covers the bounding box: {bbox}
    [west, south, east, north] = {bbox}
    
    Each POI should have these properties:
    - type: "poi"
    - category: (the POI category)
    - name: (the POI name if available, otherwise use the category)
    - color: (assign a unique color to each category)
    
    Return ONLY valid GeoJSON with no additional text or explanations.
    The response must be a complete, valid GeoJSON FeatureCollection.
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Extract JSON from the response
        json_start = response.text.find('{')
        json_end = response.text.rfind('}') + 1
        
        if json_start == -1 or json_end == -1:
            # If no JSON found, create a basic GeoJSON with just the boundary
            return create_basic_geojson(bbox, area_name, city_name, pois_data)
            
        json_str = response.text[json_start:json_end]
        
        try:
            geojson = json.loads(json_str)
            # Validate basic GeoJSON structure
            if geojson.get('type') != 'FeatureCollection' or 'features' not in geojson:
                return create_basic_geojson(bbox, area_name, city_name, pois_data)
            return geojson
        except json.JSONDecodeError:
            return create_basic_geojson(bbox, area_name, city_name, pois_data)
            
    except Exception as e:
        print(f"Error generating GeoJSON: {str(e)}")
        return create_basic_geojson(bbox, area_name, city_name, pois_data)

# Add this function at the module level, before it's called
def generate_boundary_geojson(area_name, city_name, bbox):
    """Generate a simple GeoJSON with just the boundary polygon from bbox."""
    # Create boundary polygon from bbox
    boundary_coords = [
        [bbox[0], bbox[1]],  # Southwest
        [bbox[0], bbox[3]],  # Northwest
        [bbox[2], bbox[3]],  # Northeast
        [bbox[2], bbox[1]],  # Southeast
        [bbox[0], bbox[1]]   # Close the polygon
    ]
    
    # Create the GeoJSON structure with just the boundary
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [boundary_coords]
                },
                "properties": {
                    "type": "boundary",
                    "name": f"{area_name}, {city_name}",
                    "fillColor": "#0070f3",
                    "fillOpacity": 0.2,
                    "strokeColor": "#0070f3",
                    "strokeWidth": 2
                }
            }
        ]
    }
    
    return geojson

# Then fix the create_basic_geojson function to remove the nested definition
def create_basic_geojson(bbox, area_name, city_name, pois_data):
    """Create a basic GeoJSON with boundary and POIs as fallback."""
    # Create boundary polygon from bbox
    boundary_coords = [
        [bbox[0], bbox[1]],  # Southwest
        [bbox[0], bbox[3]],  # Northwest
        [bbox[2], bbox[3]],  # Northeast
        [bbox[2], bbox[1]],  # Southeast
        [bbox[0], bbox[1]]   # Close the polygon
    ]
    
    # Create the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [boundary_coords]
                },
                "properties": {
                    "type": "boundary",
                    "name": f"{area_name}, {city_name}",
                    "fillColor": "#0070f3",
                    "fillOpacity": 0.2,
                    "strokeColor": "#0070f3",
                    "strokeWidth": 2
                }
            }
        ]
    }
    
    # Add POI features
    colors = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#AF19FF", "#FF1919"]
    color_index = 0
    
    for category, pois in pois_data.items():
        color = colors[color_index % len(colors)]
        color_index += 1
        
        for poi in pois:
            if poi.get('lat') and poi.get('lon'):
                geojson["features"].append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [poi['lon'], poi['lat']]
                    },
                    "properties": {
                        "type": "poi",
                        "category": category,
                        "name": poi.get('tags', {}).get('name', category),
                        "color": color
                    }
                })
    
    return geojson

def generate_pois_geojson(area_name, city_name, pois_data):
    """Generate a GeoJSON with just POI points."""
    # Create the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Add POI features with color coding
    colors = {
        "hospital": "#0088FE",
        "school": "#00C49F", 
        "pharmacy": "#FFBB28",
        "restaurant": "#FF8042",
        "cafe": "#AF19FF",
        "bank": "#FF1919",
        "atm": "#17BECF",
        "supermarket": "#9467BD",
        "grocery": "#D62728",
        "bus_stop": "#2CA02C",
        "train_station": "#E377C2",
        "park": "#7F7F7F",
        "playground": "#BCBD22",
        "post_office": "#8C564B"
    }
    
    for category, pois in pois_data.items():
        color = colors.get(category, "#000000")  # Default black if category not in colors
        
        for poi in pois:
            if poi.get('lat') and poi.get('lon'):
                geojson["features"].append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [poi['lon'], poi['lat']]
                    },
                    "properties": {
                        "type": "poi",
                        "category": category,
                        "name": poi.get('tags', {}).get('name', category),
                        "color": color
                    }
                })
    
    return geojson

@app.post("/analyze-area")
async def analyze_area(area_request: dict):
    city_name = area_request.get('city')
    area_name = area_request.get('area')
    full_area_name = f"{area_name}, {city_name}"

    print(f"\n=== Starting Analysis for: {full_area_name} ===")

    poi_categories = [
        "school", "hospital", "pharmacy", "supermarket", "grocery",
        "restaurant", "cafe", "bar", "pub", "bus_stop", "train_station",
        "park", "playground", "bank", "atm", "post_office"
    ]

    try:
        # Get POIs from Overpass API
        print("\n[1/3] Getting POIs from Overpass...")
        overpass_pois_data = get_pois_overpass(area_name, city_name, poi_categories)

        if "error" in overpass_pois_data:
            print(f"Error fetching POIs from Overpass: {overpass_pois_data['error']}")
            raise HTTPException(status_code=500, detail=overpass_pois_data['error'])

        categorized_pois = overpass_pois_data['pois']
        geocode = overpass_pois_data['geocode']
        bbox = overpass_pois_data.get('bbox')
        
        # Generate GeoJSON with just POIs
        print("\n[2/3] Generating POIs GeoJSON...")
        pois_geojson = generate_pois_geojson(area_name, city_name, categorized_pois)
        
        # Prepare analysis prompt
        print("\n[3/3] Preparing analysis prompt...")
        analysis_prompt = f"""
        You are a expert location analyser for people to move in there. Analyze the living potential of {full_area_name} based on these categorized Points of Interest (POIs):
        {json.dumps(categorized_pois, indent=2)}
        Focus on the following aspects which are important for living standards and dont be strict whatever data you get analyze that and provide your opnion and analysis based on that.
        
        Provide a structured JSON response with the following keys:
        - "summary":(in simple text) A concise summary of the living potential of the area, highlighting the strengths and weaknesses in each category.
        - "pie_chart_data": Data suitable for a pie chart visualizing the distribution of POI types. Include "name" and "value" for each category. Example: [{{"name": "Residential", "value": 30}}, {{"name": "Commercial", "value": 70}}]
        - "ai_rating": A numerical rating from 0 to 100 representing how well this area functions as a "15-minute city" where residents can access most daily needs within a 15-minute walk or bike ride.
        
        IMPORTANT: Only return the raw JSON, no additional text or explanations. The response must start with '{{' and end with '}}'."""

        # Get analysis
        try:
            response = model.generate_content(analysis_prompt)
            
            # Extract JSON from the response
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON found in the response")
                
            json_str = response.text[json_start:json_end]
            analysis_results = json.loads(json_str)
            
            # Combine all results
            final_results = {
                "summary": analysis_results.get("summary", ""),
                "pie_chart_data": analysis_results.get("pie_chart_data", []),
                "ai_rating": analysis_results.get("ai_rating", 0),
                "geocode": geocode,
                "bbox": bbox,
                "geojson": pois_geojson,  # Include only the POIs GeoJSON
                "pois": categorized_pois  # Keep the POIs separate for the frontend
            }
            
            return final_results
            
        except Exception as e:
            print(f"LLM API Error: {str(e)}")
            raise HTTPException(status_code=502, detail=f"LLM API Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable if available (for Render), otherwise use 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    
