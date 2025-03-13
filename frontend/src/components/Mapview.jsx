import React, { useEffect, useRef } from 'react';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css';
import './Mapview.css';

function Mapview({ results, pieChartData, colors }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const mapLoaded = useRef(false);
  const markersRef = useRef([]);

  useEffect(() => {
    // Define updateMap function first before using it
    const updateMap = () => {
      if (!map.current || !mapLoaded.current) {
        console.log('Map not ready yet, cannot update');
        return;
      }
    
      console.log('Updating map with results:', results);
    
      // Clear any existing markers
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];
    
      // Remove existing sources and layers
      try {
        if (map.current.getSource('area-data')) {
          map.current.removeLayer('poi-points');
          map.current.removeLayer('boundary-fill');
          map.current.removeLayer('boundary-line');
          map.current.removeSource('area-data');
        }
      } catch (e) {
        console.log('Error removing existing layers/sources:', e);
      }
    
      // If we have a bounding box, fit the map to it
      if (results.bbox) {
        map.current.fitBounds([
          [results.bbox[0], results.bbox[1]], // Southwest corner
          [results.bbox[2], results.bbox[3]]  // Northeast corner
        ], {
          padding: 50,
          duration: 1000
        });
      }
    
      // If we have a GeoJSON, add it to the map
      if (results?.geojson) {
        try {
          console.log('Adding GeoJSON to map:', results.geojson);
          
          // Add the GeoJSON source
          map.current.addSource('area-data', {
            'type': 'geojson',
            'data': results.geojson
          });
          
          // Add a fill layer for the boundary
          map.current.addLayer({
            'id': 'boundary-fill',
            'type': 'fill',
            'source': 'area-data',
            'filter': ['==', ['get', 'type'], 'boundary'],
            'paint': {
              'fill-color': ['get', 'fillColor'],
              'fill-opacity': ['get', 'fillOpacity']
            }
          });
          
          // Add a line layer for the boundary
          map.current.addLayer({
            'id': 'boundary-line',
            'type': 'line',
            'source': 'area-data',
            'filter': ['==', ['get', 'type'], 'boundary'],
            'paint': {
              'line-color': ['get', 'strokeColor'],
              'line-width': ['get', 'strokeWidth'],
              'line-opacity': 0.9
            }
          });
          
          // Add a circle layer for POIs
          map.current.addLayer({
            'id': 'poi-points',
            'type': 'circle',
            'source': 'area-data',
            'filter': ['==', ['get', 'type'], 'poi'],
            'paint': {
              'circle-radius': 8,
              'circle-color': ['get', 'color'],
              'circle-stroke-width': 2,
              'circle-stroke-color': '#ffffff'
            }
          });
          
          // Add popups for POIs
          map.current.on('click', 'poi-points', (e) => {
            if (!e.features.length) return;
            
            const feature = e.features[0];
            const coordinates = feature.geometry.coordinates.slice();
            const { name, category } = feature.properties;
            
            // Create popup
            new maptilersdk.Popup()
              .setLngLat(coordinates)
              .setHTML(`
                <div class="popup-content">
                  <h4>${name}</h4>
                  <p>Category: ${category}</p>
                </div>
              `)
              .addTo(map.current);
          });
          
          // Change cursor on hover
          map.current.on('mouseenter', 'poi-points', () => {
            map.current.getCanvas().style.cursor = 'pointer';
          });
          
          map.current.on('mouseleave', 'poi-points', () => {
            map.current.getCanvas().style.cursor = '';
          });
          
          console.log('Successfully added GeoJSON layers to map');
        } catch (e) {
          console.error('Error adding GeoJSON to map:', e);
        }
      } else if (results?.pois) {
        // Fallback to old method if no GeoJSON but we have POIs
        console.log('No GeoJSON found, falling back to POI markers');
        
        // Create a mapping of categories to colors
        const categoryColors = {};
        if (pieChartData && Array.isArray(pieChartData)) {
          pieChartData.forEach((item, index) => {
            const category = typeof item.name === 'object' ? Object.keys(item.name)[0] : item.name;
            categoryColors[category] = colors[index % colors.length];
          });
        }
        
        // Process POIs and add markers
        Object.entries(results.pois).forEach(([category, pois]) => {
          // Get color for this category or use default
          const markerColor = categoryColors[category] || '#FF0000';
          
          pois.forEach(poi => {
            // Check if POI has valid coordinates
            if (poi.lat && poi.lon) {
              // Create custom marker element
              const el = document.createElement('div');
              el.className = 'color-coded-marker';
              el.style.backgroundColor = markerColor;
              el.style.width = '14px';
              el.style.height = '14px';
              el.style.borderRadius = '50%';
              el.style.border = '2px solid white';
              el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
              
              // Create marker with popup
              const marker = new maptilersdk.Marker({element: el})
                .setLngLat([poi.lon, poi.lat])
                .addTo(map.current);
              
              // Add popup with POI name and category
              const popup = new maptilersdk.Popup({
                offset: 25,
                closeButton: true,
                className: 'custom-popup'
              }).setHTML(`
                <div class="popup-content">
                  <h4>${poi.tags?.name || category}</h4>
                  <p>Category: ${category}</p>
                </div>
              `);
              
              marker.setPopup(popup);
              markersRef.current.push(marker);
            }
          });
        });
      }
    };

    // Initialize map only once
    if (!map.current && mapContainer.current) {
      console.log('Initializing map...');
      
      // Set API key
      maptilersdk.config.apiKey = process.env.REACT_APP_MAPTILER_API_KEY;
      
      // Initialize Maptiler map
      map.current = new maptilersdk.Map({
        container: mapContainer.current,
        style: maptilersdk.MapStyle.STREETS,
        center: [0, 0],
        zoom: 1
      });

      // Add navigation controls
      map.current.addControl(new maptilersdk.NavigationControl());
      
      map.current.on('load', () => {
        console.log('Map style loaded');
        mapLoaded.current = true;
        if (results) updateMap();
      });
    }

    // Update map when results change
    if (results && map.current) {
      if (mapLoaded.current) {
        updateMap();
      } else {
        map.current.once('load', updateMap);
      }
    }
  }, [results, pieChartData, colors]);

  return (
    <div className="map-container">
      <div ref={mapContainer} className="map" />
    </div>
  );
}

export default Mapview;