'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ShieldAlert, Search, Activity } from 'lucide-react';

export default function IntelHome() {
  const [url, setUrl] = useState('');
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: async (payload: { url: string }) => {
      const { data } = await axios.post('/api/audit', payload);
      return data;
    },
    onSuccess: (data) => router.push(`/cases/${data.listing_id}`),
  });

  return (
    <main className="max-w-7xl mx-auto px-6 py-12 md:py-24 relative z-10">
      <div className="mb-8 animate-in fade-in slide-in-from-bottom-2">
        <span className="border border-zinc-800 bg-zinc-900/50 text-[9px] font-bold px-3 py-1 text-zinc-400 uppercase tracking-[0.2em]">
          Classified: Institutional Tier
        </span>
      </div>

      <h1 className="text-4xl md:text-7xl font-bold leading-none tracking-tighter mb-8 text-white">
        SEE WHAT THE<br />
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00F0FF] to-zinc-600">
          BROKER HIDES.
        </span>
      </h1>

      <p className="text-sm md:text-xl text-zinc-500 max-w-2xl mb-12 leading-relaxed font-light">
        Automated forensic auditing engine for Sofia Real Estate. 
        Cross-referencing <span className="text-zinc-300">Expropriation</span>, 
        <span className="text-zinc-300">Act 16</span>, and 
        <span className="text-zinc-300">Social Risk</span>.
      </p>

      {/* SEARCH INTERFACE */}
      <div className="max-w-2xl mb-20">
        <div className="flex gap-2 p-1 bg-zinc-900/50 border border-zinc-800 backdrop-blur-md rounded-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-600" />
            <Input 
              placeholder="PASTE IMOT.BG URL..." 
              className="bg-black/50 border-transparent text-white font-mono pl-10 h-10 focus:ring-0 focus:border-tech-blue"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <Button 
            onClick={() => mutation.mutate({ url })}
            disabled={mutation.isPending}
            className="bg-tech-blue text-black font-bold uppercase tracking-widest text-xs hover:bg-white transition-all h-10 px-8"
          >
            {mutation.isPending ? <Activity className="animate-spin h-4 w-4" /> : 'INITIATE SCAN'}
          </Button>
        </div>
        {mutation.isError && (
          <p className="mt-2 text-red-500 text-[10px] font-mono flex items-center gap-2">
            <ShieldAlert size={12} /> SCAN_FAILED: UPSTREAM_API_UNREACHABLE
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { id: '01', title: 'INSOLVENCY RADAR', desc: 'Real-time liquidity stress testing for developer portfolios.' },
          { id: '02', title: 'TOXIC COLLATERAL', desc: 'Automated detection of Atelier traps and "The Death List" seizure plans.' },
          { id: '03', title: 'SHADOW LAND BANK', desc: 'Predictive modeling for municipal parcel acquisition.' }
        ].map((module) => (
          <div key={module.id} className="group border border-zinc-800 p-6 bg-black/40 backdrop-blur-md hover:border-tech-blue transition-all">
            <div className="text-zinc-600 text-[9px] font-bold mb-3 uppercase tracking-widest flex justify-between">
              Module / {module.id} <span className="text-tech-blue opacity-0 group-hover:opacity-100 italic">● ACTIVE</span>
            </div>
            <h3 className="text-lg font-bold mb-2 text-white tracking-tight">{module.title}</h3>
            <p className="text-[10px] text-zinc-500 leading-relaxed font-mono">{module.desc}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
