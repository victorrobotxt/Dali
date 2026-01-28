'use client';

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useParams } from 'next/navigation';
import { ForensicLog } from './_components/ForensicLog';
import { ForensicMap } from './_components/ForensicMap';
import { RiskBadge } from './_components/RiskBadge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from '@/components/ui/badge';
import type { ForensicReport } from '@/types/api';
import { ShieldCheck, ShieldAlert, Activity, Building, Microscope, Scale } from 'lucide-react';
import { CadastreTable } from './_components/CadastreTable';

export default function WarRoom() {
  const { id } = useParams();

  // Polling Logic
  const { data: report, isLoading } = useQuery<ForensicReport>({
    queryKey: ['report', id],
    queryFn: async () => {
      const { data } = await axios.get(`/api/reports/${id}`);
      return data;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return (status === 'PENDING' || status === 'PROCESSING') ? 2000 : false;
    }
  });

  if (isLoading || !report) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center space-y-4">
        <Activity className="w-12 h-12 text-tech-blue animate-pulse" />
        <p className="font-mono text-zinc-500 text-sm tracking-[0.2em]">ESTABLISHING SECURE LINK...</p>
      </div>
    );
  }

  // Safe Accessors
  const scraped = report.discrepancies?.scraped;
  const ai = report.discrepancies?.ai;
  const cad = report.discrepancies?.cadastre;
  const geo = report.discrepancies?.geo;
  const legal = report.discrepancies?.legal_status;

  return (
    <div className="min-h-screen bg-zinc-950 p-4 md:p-6 font-sans text-zinc-100 flex flex-col gap-4">
      
      {/* 1. HEADER BAR */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-zinc-900 pb-4">
        <div className="space-y-1">
          <h1 className="text-xl md:text-2xl font-bold tracking-tight flex items-center gap-3">
            CASE FILE <span className="font-mono text-zinc-600">#{id}</span>
            <Badge variant="outline" className="font-mono text-[10px] text-zinc-400 border-zinc-800">
               {report.status}
            </Badge>
          </h1>
          <div className="flex gap-4 text-xs font-mono text-zinc-500">
            <span>CAD_ID: <span className="text-zinc-300">{cad?.cadastre_id || '---'}</span></span>
            <span>URL: <span className="text-zinc-300 truncate max-w-[200px] inline-block align-bottom">{scraped?.source_url || '---'}</span></span>
          </div>
        </div>
        <div className="mt-4 md:mt-0">
          <RiskBadge score={report.risk_score} status={report.status} />
        </div>
      </header>

      {/* 2. THE BENTO GRID */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 flex-1">
        
        {/* QUADRANT A: THE TARGET (Top Left) - 4 Cols */}
        <Card className="md:col-span-4 bg-zinc-900/50 border-zinc-800 flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Building className="w-3 h-3" /> Target Asset
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {/* Main Photo (Placeholder if no URL) */}
            <div className="aspect-video bg-black border border-zinc-800 rounded-md overflow-hidden relative group">
              {scraped?.image_urls?.[0] ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={scraped.image_urls[0]} alt="Target" className="object-cover w-full h-full opacity-80 group-hover:opacity-100 transition-opacity" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-700 font-mono text-xs">NO_OPTICAL_DATA</div>
              )}
              {/* Overlay Data */}
              <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/90 to-transparent p-3 pt-8">
                <div className="flex justify-between items-end">
                  <div className="text-xl font-mono font-bold text-white">
                    {scraped?.price_predicted?.toLocaleString() || 0} <span className="text-sm text-zinc-500">EUR</span>
                  </div>
                  <div className="text-right text-xs font-mono text-zinc-400">
                    {scraped?.area_sqm} m²
                  </div>
                </div>
              </div>
            </div>

            {/* AI Summary Tabs */}
            <Tabs defaultValue="visual" className="w-full">
              <TabsList className="w-full bg-zinc-950 border border-zinc-800">
                <TabsTrigger value="visual" className="text-[10px] flex-1">VISUAL</TabsTrigger>
                <TabsTrigger value="legal" className="text-[10px] flex-1">LEGAL</TabsTrigger>
              </TabsList>
              <TabsContent value="visual" className="space-y-2 mt-2">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                    <span className="text-zinc-500 block text-[9px]">TYPE</span>
                    {ai?.building_type || 'Unknown'}
                  </div>
                  <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                    <span className="text-zinc-500 block text-[9px]">ERA</span>
                    {ai?.construction_year_est || 'Unknown'}
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="legal" className="mt-2">
                 <div className="p-2 bg-zinc-950 rounded border border-zinc-800 text-xs font-mono space-y-1">
                    <div className="flex justify-between">
                       <span className="text-zinc-500">HEIGHT</span>
                       <span className={ai?.ceiling_height && ai.ceiling_height < 2.6 ? "text-red-400" : "text-emerald-400"}>
                          {ai?.ceiling_height}m
                       </span>
                    </div>
                    <div className="flex justify-between">
                       <span className="text-zinc-500">STORAGE</span>
                       <span className={ai?.heating_inventory?.has_central_heating ? "text-emerald-400" : "text-zinc-400"}>
                          {ai?.has_storage ? "FOUND" : "MISSING"}
                       </span>
                    </div>
                 </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* QUADRANT B: THE MAP (Top Right) - 5 Cols */}
        <Card className="md:col-span-5 bg-zinc-900/50 border-zinc-800 flex flex-col">
           <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Microscope className="w-3 h-3" /> Geospatial Triangulation
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0 overflow-hidden relative min-h-[300px] md:min-h-0">
             {/* Map Component */}
             <div className="absolute inset-2 bottom-2 rounded-md overflow-hidden border border-zinc-800">
                <ForensicMap 
                   lat={42.6977} // Default to Sofia Center if null
                   lng={23.3219} 
                   claimedAddress={scraped?.neighborhood || "Unknown"}
                   detectedAddress={geo?.detected_neighborhood || "Scanning..."}
                   match={!!geo?.match}
                />
             </div>
          </CardContent>
        </Card>

        {/* QUADRANT C: THE EVIDENCE (Right Sidebar) - 3 Cols */}
        <Card className="md:col-span-3 bg-zinc-900/50 border-zinc-800 flex flex-col row-span-2">
           <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-3 h-3" /> Live Audit Log
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0">
             <div className="h-full p-2">
               <ForensicLog 
                  status={report.status} 
                  logs={[
                     "Initializing forensic handshake...",
                     report.status !== 'PENDING' ? "Scraper payload received." : "Waiting for scraper...",
                     cad?.cadastre_id ? `Cadastre ID locked: ${cad.cadastre_id}` : null,
                     cad?.official_area ? `Official Area: ${cad.official_area} m²` : null,
                     cad?.social_risk_ratio && cad.social_risk_ratio > 0 ? `WARN: Social Housing Density ${cad.social_risk_ratio * 100}%` : null,
                     legal?.is_trap ? "ALERT: Legal Status 'ATELIER' Detected" : null,
                     "Audit cycle active."
                  ].filter(Boolean) as string[]} 
               />
             </div>
          </CardContent>
        </Card>

        {/* QUADRANT D: THE LEDGER (Bottom) - 9 Cols */}
        <Card className="md:col-span-9 bg-zinc-900/50 border-zinc-800">
           <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Scale className="w-3 h-3" /> Registry & Legal Discrepancies
            </CardTitle>
          </CardHeader>
          <CardContent>
             <CadastreTable 
                scrapedArea={scraped?.area_sqm || 0}
                officialArea={cad?.official_area || 0}
                cadastreId={cad?.cadastre_id || ""}
                isExpropriated={report.discrepancies?.city_risk?.is_expropriated || false}
                hasAct16={report.discrepancies?.compliance?.has_act16 || false}
             />
          </CardContent>
        </Card>

      </div>
    </div>
  );
}

// Helper utility
function cn(...inputs: (string | undefined | null | boolean)[]) {
  return inputs.filter(Boolean).join(" ");
}
