'use client';

import { APIProvider, Map, Marker } from '@vis.gl/react-google-maps';
import { Badge } from "@/components/ui/badge";

interface MapProps {
  lat: number;
  lng: number;
  claimedAddress: string;
  detectedAddress: string;
  match: boolean;
}

export function ForensicMap({ lat, lng, claimedAddress, detectedAddress, match }: MapProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY || "";

  if (!apiKey || apiKey === "your_key_here") {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center bg-zinc-950 border border-zinc-800 rounded-md relative overflow-hidden">
        {/* Mock Grid for visual flair without API Key */}
        <div className="absolute inset-0 grid-bg opacity-20" />
        <div className="text-zinc-500 font-mono text-xs text-center z-10 p-4">
          <span className="text-amber-500 block mb-2">⚠ API KEY REQUIRED</span>
          Google Maps SDK is inactive.<br/>
          <span className="text-[10px] opacity-50">Target: {lat.toFixed(5)}, {lng.toFixed(5)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full rounded-md overflow-hidden border border-zinc-800 relative group">
      <APIProvider apiKey={apiKey}>
        <Map
          defaultCenter={{ lat, lng }}
          defaultZoom={18} // Close up for forensic detail
          mapId="DEMO_MAP_ID" // Required for advanced markers
          gestureHandling={'cooperative'}
          disableDefaultUI={true}
          className="w-full h-full grayscale-[50%] contrast-125 group-hover:grayscale-0 transition-all duration-700"
        >
          <Marker position={{ lat, lng }} />
        </Map>
      </APIProvider>
      
      {/* Tactical Overlay */}
      <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 bg-black/80 p-2 rounded backdrop-blur-sm border border-zinc-800">
        <div className="flex items-center gap-2">
           <div className={`w-2 h-2 rounded-full ${match ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`} />
           <span className="text-[10px] font-mono text-zinc-300">
             {match ? 'LOCATION_VERIFIED' : 'LOCATION_MISMATCH'}
           </span>
        </div>
        <div className="text-[9px] font-mono text-zinc-500 truncate max-w-[200px]">
          CLAIM: {claimedAddress}<br/>
          SCAN: {detectedAddress}
        </div>
      </div>
    </div>
  );
}