import { useState, useEffect, useRef, useMemo } from 'react'
import axios from 'axios'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

function FlyToLocation({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, 18);
    }
  }, [center, map]);
  return null;
}

function App() {
  const [place, setPlace] = useState(null);
  const [markerPos, setMarkerPos] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchNextPlace = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://127.0.0.1:8000/place/next');
      const data = response.data;
      
      setPlace(data);
      setMarkerPos([data.latitude, data.longitude]);
    } catch (error) {
      console.error("Error fetching place:", error);
      alert("Failed to fetch place. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNextPlace();
  }, []);

  const eventHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const { lat, lng } = marker.getLatLng();
          setMarkerPos([lat, lng]);
          console.log("New Position:", lat, lng);
        }
      },
    }),
    []
  )
  const markerRef = useRef(null)

  const handleSubmit = async () => {
    if (!place || !markerPos) return;

    try {
      await axios.post('http://127.0.0.1:8000/place/verify', {
        id: place.id,
        correct_lat: markerPos[0],
        correct_lon: markerPos[1]
      });
      fetchNextPlace();
    } catch (error) {
      console.error("Error saving:", error);
      alert("Failed to save correction.");
    }
  };

  if (loading && !place) return <div className="container">Loading Map Data...</div>;

  return (
    <div className="container">
      <h1>Overture Spatial Fixer</h1>
      
      <div style={{ marginBottom: '10px', textAlign: 'left' }}>
        <strong>Name:</strong> {place.name} <br/>
        <strong>Category:</strong> {place.category} <br/>
        <small>ID: {place.id}</small>
      </div>

      <p style={{color: '#666'}}>
        💡 Drag the blue pin to the <strong>actual main entrance</strong> or center of the building.
      </p>

      {place && (
        <MapContainer 
          center={[place.latitude, place.longitude]} 
          zoom={18} 
          className="map-container"
        >
          <TileLayer
            attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
          
          <FlyToLocation center={[place.latitude, place.longitude]} />

          <Marker 
            draggable={true}
            eventHandlers={eventHandlers}
            position={markerPos}
            ref={markerRef}
          >
            <Popup>
              {place.name}
            </Popup>
          </Marker>
        </MapContainer>
      )}

      <button onClick={handleSubmit}>
        ✅ Confirm & Next
      </button>
    </div>
  )
}

export default App
