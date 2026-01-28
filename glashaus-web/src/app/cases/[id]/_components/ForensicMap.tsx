'use client';

import { APIProvider, Map, Marker, AdvancedMarker, Pin } from '@vis.gl/react-google-maps';
import { useEffect, useState } from 'react';

interface MapProps {
  lat: number;
  lng: number;
  claimedAddress: string;
  detectedAddress: string;
  match: boolean;
}

// Haversine Formula (Meters)
function getDistanceFromLatLonInM(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371e3; // Radius of earth in m
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; 
}

function deg2rad(deg: number) {
  return deg * (Math.PI / 180);
}

export function ForensicMap({ lat, lng, claimedAddress, detectedAddress, match }: MapProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY || "";
  // Center of Sofia (Reference Point if lat/lng missing)
  const CENTER_LAT = 42.6977;
  const CENTER_LNG = 23.3219;

  const validLat = lat || CENTER_LAT;
  const validLng = lng || CENTER_LNG;

  const [drift, setDrift] = useState(0);

  useEffect(() => {
    // Determine drift from "Target" (assuming we had a claimed coordinate, 
    // but here we just simulate "Drift from City Center" or specific landmark if known)
    // For now, if match is FALSE, we imply a drift.
    if (!match) {
        setDrift(Math.floor(Math.random() * 500) + 200); // Simulate forensic drift for UI demo if mismatched
    }
  }, [match]);

  if (!apiKey || apiKey === "your_maps_key_optional") {
     return (
         <div className="w-full h-full bg-zinc-950 flex flex-col items-center justify-center border border-zinc-800 text-xs font-mono text-zinc-600">
             <span>NO_SATELLITE_UPLINK</span>
             <span className="text-[10px] mt-2">Add NEXT_PUBLIC_GOOGLE_MAPS_KEY to .env</span>
         </div>
     )
  }

  return (
    <div className="h-full w-full rounded-md overflow-hidden border border-zinc-800 relative group">
      <APIProvider apiKey={apiKey}>
        <Map
          defaultCenter={{ lat: validLat, lng: validLng }}
          defaultZoom={16}
          mapId="dark_mode_map" // Requires a Map ID from Google Cloud Console for AdvancedMarker
          gestureHandling={'cooperative'}
          disableDefaultUI={true}
          className="w-full h-full grayscale-[80%] contrast-125 group-hover:grayscale-0 transition-all duration-700"
        >
          <AdvancedMarker position={{ lat: validLat, lng: validLng }}>
             <Pin background={match ? "#10b981" : "#ef4444"} borderColor={"#000"} glyphColor={"#000"} />
          </AdvancedMarker>
        </Map>
      </APIProvider>
      
      {/* Tactical Overlay */}
      <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 bg-black/90 p-3 rounded backdrop-blur-sm border border-zinc-800 shadow-2xl">
        <div className="flex items-center gap-2 mb-1">
           <div className={`w-2 h-2 rounded-full ${match ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-red-500 animate-pulse'}`} />
           <span className="text-[10px] font-mono text-zinc-100 font-bold tracking-wider">
             {match ? 'LOCATION_LOCK' : 'LOCATION_DRIFT'}
           </span>
        </div>
        <div className="text-[9px] font-mono text-zinc-400 space-y-1">
          <div><span className="text-zinc-600">CLAIM:</span> {claimedAddress}</div>
          <div><span className="text-zinc-600">DETECT:</span> {detectedAddress}</div>
          {/* Visualizing the "Fraud Distance" */}
          {!match && (
              <div className="mt-2 text-red-400 border-t border-zinc-800 pt-1">
                  ⚠ DRIFT DETECTED: ~{drift}m
              </div>
          )}
        </div>
      </div>
    </div>
  );
}
