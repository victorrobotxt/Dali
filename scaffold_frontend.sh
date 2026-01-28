#!/bin/bash

# ==========================================
# 📂 PROJECT GLASHAUS: FRONTEND SCAFFOLDER
# Version: 1.1 (The Digital Notary)
# ==========================================

APP_NAME="glashaus-web"

echo -e "\033[0;32m>>> INITIATING GLASHAUS FRONTEND PROTOCOL...\033[0m"

# 1. Initialize Next.js 15 (Non-Interactive)
# We use --yes to accept defaults where possible, but specify flags to avoid prompts
npx create-next-app@latest $APP_NAME \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-npm \
  --no-git \
  --yes

cd $APP_NAME

echo -e "\033[0;32m>>> INSTALLING CRITICAL DEPENDENCIES...\033[0m"

# Core Libs
npm install zustand @tanstack/react-query @vis.gl/react-google-maps axios lucide-react clsx tailwind-merge class-variance-authority framer-motion

# 2. Configure Shadcn/UI (Manual Bypass)
# Instead of wrestling with the interactive CLI, we manually inject the config
# so we can immediately add components non-interactively.

echo -e "\033[0;33m>>> CONFIGURING DESIGN SYSTEM (Cyber-Noir)...\033[0m"

cat > components.json <<EOF
{
  "\$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
EOF

# Create the utils helper required by shadcn
mkdir -p src/lib
cat > src/lib/utils.ts <<EOF
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF

# Update globals.css for the "Zinc-950" aesthetic
cat > src/app/globals.css <<EOF
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
EOF

# Now we can safely install shadcn components
npx shadcn@latest add -y button card input badge scroll-area table alert-dialog progress separator

# 3. Environment Setup
echo -e "\033[0;33m>>> LINKING DOCKER NETWORK...\033[0m"

cat > .env.local <<EOF
# Internal Docker URL (Next.js Server -> FastAPI Container)
API_INTERNAL_URL=http://api:8000

# Public URL (Browser -> Next.js Proxy)
NEXT_PUBLIC_API_URL=http://localhost:3000/api
EOF

# 4. Type Definitions (Mirroring Python Schemas)
mkdir -p src/types
cat > src/types/api.ts <<EOF
[cite_start]// Auto-generated mirror of src/schemas.py [cite: 143, 145]

export type ReportStatus = 'PENDING' | 'PROCESSING' | 'VERIFIED' | 'MANUAL_REVIEW' | 'REJECTED';

export interface AuditRequest {
  url: string;
  price_override?: number;
}

export interface AuditResponse {
  listing_id: number;
  status: string;
}

export interface AIAnalysisResult {
  address_prediction: string;
  landmarks: string[];
  neighborhood_match: string;
  building_type: string;
  is_panel_block: boolean;
  construction_year_est: number;
  room_count: number;
  ceiling_height: number;
  heating_inventory: {
    ac_units: number;
    radiators: number;
    has_central_heating: boolean;
  };
  net_area_sqm: number;
  visual_red_flags: string[];
}

export interface ForensicReport {
  report_id: number;
  status: ReportStatus;
  risk_score: number;
  ai_confidence: number;
  discrepancies: {
    scraped: {
      source_url: string;
      price_predicted: number;
      area_sqm: number;
      neighborhood: string;
      image_urls: string[];
    };
    ai: AIAnalysisResult;
    geo: {
      match: boolean;
      detected_neighborhood: string;
      warning?: string;
    };
    cadastre: {
      cadastre_id: string;
      official_area: number;
      social_risk_ratio: number;
    };
    legal_status: {
      status: string;
      is_trap: boolean;
      legal_flags: string[];
    };
  };
  manual_notes?: string;
  cost: number;
  created_at: string;
}
EOF

# 5. State Management & Providers
cat > src/lib/store.ts <<EOF
import { create } from 'zustand';

interface GlashausState {
  activeCaseId: number | null;
  setActiveCase: (id: number) => void;
  reset: () => void;
}

export const useStore = create<GlashausState>((set) => ({
  activeCaseId: null,
  setActiveCase: (id) => set({ activeCaseId: id }),
  reset: () => set({ activeCaseId: null }),
}));
EOF

cat > src/app/providers.tsx <<EOF
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5000,
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
EOF

# 6. The Proxy (Route Handlers)
mkdir -p src/app/api/audit src/app/api/reports/[id]

# POST /api/audit (Trigger)
cat > src/app/api/audit/route.ts <<EOF
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const body = await request.json();
  const apiUrl = process.env.API_INTERNAL_URL || 'http://localhost:8000';
  
  try {
    const res = await fetch(\`\${apiUrl}/audit\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "Forensic Handshake Failed", details: res.statusText }, 
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Upstream Unreachable" }, { status: 503 });
  }
}
EOF

# GET /api/reports/[id] (Poll)
cat > src/app/api/reports/[id]/route.ts <<EOF
import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> } // Params are promises in Next.js 15
) {
  const { id } = await params;
  const apiUrl = process.env.API_INTERNAL_URL || 'http://localhost:8000';

  try {
    const res = await fetch(\`\${apiUrl}/reports/\${id}\`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Report Not Found" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Upstream Unreachable" }, { status: 503 });
  }
}
EOF

# 7. UI Components ("The War Room")

# Update layout.tsx to include providers
cat > src/app/layout.tsx <<EOF
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Providers from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Glashaus // Forensic Engine",
  description: "Automated Due Diligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={\`\${inter.variable} \${mono.variable} antialiased bg-zinc-950 min-h-screen\`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
EOF

# The Ingest Page (Home)
cat > src/app/page.tsx <<EOF
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useStore } from '@/lib/store';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ShieldAlert, Search } from 'lucide-react';
import type { AuditResponse, AuditRequest } from '@/types/api';

export default function IngestPage() {
  const [url, setUrl] = useState('');
  const router = useRouter();
  const setActiveCase = useStore((state) => state.setActiveCase);

  const mutation = useMutation({
    mutationFn: async (newAudit: AuditRequest) => {
      const { data } = await axios.post<AuditResponse>('/api/audit', newAudit);
      return data;
    },
    onSuccess: (data) => {
      setActiveCase(data.listing_id);
      router.push(\`/cases/\${data.listing_id}\`);
    },
  });

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#18181b_1px,transparent_1px),linear-gradient(to_bottom,#18181b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] -z-10" />

      <div className="w-full max-w-xl space-y-8 z-10">
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-bold tracking-tighter text-white font-sans">
            GLASHAUS <span className="text-emerald-500 text-sm align-top tracking-widest font-mono">v1.1</span>
          </h1>
          <p className="text-zinc-500 font-mono text-sm tracking-[0.2em]">
            AUTOMATED DUE DILIGENCE ENGINE // SOFIA_MUNICIPALITY
          </p>
        </div>

        <Card className="p-1 bg-zinc-900 border-zinc-800 shadow-2xl">
          <div className="flex gap-2 p-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <Input 
                placeholder="PASTE IMOT.BG URL OR CADASTRE ID..." 
                className="bg-zinc-950 border-zinc-800 text-zinc-100 font-mono pl-9 h-10 focus-visible:ring-emerald-500"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <Button 
              onClick={() => mutation.mutate({ url })}
              disabled={mutation.isPending || !url}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold tracking-widest h-10"
            >
              {mutation.isPending ? 'UPLOADING...' : 'AUDIT'}
            </Button>
          </div>
        </Card>

        {mutation.isError && (
          <div className="flex items-center gap-2 text-red-500 font-mono text-xs justify-center bg-red-950/20 p-2 rounded border border-red-900/50">
            <ShieldAlert className="w-4 h-4" />
            <span>CONNECTION REFUSED: PROXY HANDSHAKE FAILED</span>
          </div>
        )}
      </div>
    </main>
  );
}
EOF

# The War Room Structure
mkdir -p src/app/cases/[id] src/app/cases/[id]/_components

# Dashboard Page (Polling & Layout)
cat > src/app/cases/[id]/page.tsx <<EOF
'use client';

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useParams } from 'next/navigation';
import { ForensicLog } from './_components/ForensicLog';
import { RiskBadge } from './_components/RiskBadge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ForensicReport } from '@/types/api';
import { ShieldCheck, ShieldAlert, Activity } from 'lucide-react';

export default function WarRoom() {
  const { id } = useParams();

  const { data: report, isLoading } = useQuery<ForensicReport>({
    queryKey: ['report', id],
    queryFn: async () => {
      const { data } = await axios.get(\`/api/reports/\${id}\`);
      return data;
    },
    refetchInterval: (query) => {
      // Poll every 2s if pending/processing, stop if done
      const status = query.state.data?.status;
      return (status === 'PENDING' || status === 'PROCESSING') ? 2000 : false;
    }
  });

  if (isLoading || !report) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center space-y-4">
        <Activity className="w-12 h-12 text-emerald-500 animate-pulse" />
        <p className="font-mono text-zinc-500 text-sm">ESTABLISHING SECURE LINK...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 p-6 grid grid-cols-12 grid-rows-[auto_1fr_1fr] gap-4 font-sans text-zinc-100">
      
      {/* HEADER */}
      <div className="col-span-12 flex justify-between items-center border-b border-zinc-800 pb-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            CASE FILE <span className="font-mono text-zinc-500">#{id}</span>
          </h1>
          <div className="flex gap-2 mt-1">
             <Badge variant="outline" className="text-zinc-400 border-zinc-700 font-mono text-xs">
                {report.discrepancies?.cadastre?.cadastre_id || 'ID_PENDING'}
             </Badge>
          </div>
        </div>
        <div className="text-right">
          <RiskBadge score={report.risk_score} status={report.status} />
        </div>
      </div>

      {/* LEFT COL: ASSET DATA */}
      <div className="col-span-12 md:col-span-4 row-span-2 space-y-4">
        <Card className="bg-zinc-900 border-zinc-800 h-full">
          <CardHeader>
            <CardTitle className="text-sm font-mono text-zinc-400">TARGET_ASSET</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
             {/* Image Carousel Placeholder */}
             <div className="aspect-video bg-zinc-950 border border-zinc-800 rounded flex items-center justify-center">
                <span className="text-zinc-600 font-mono text-xs">NO_SIGNAL</span>
             </div>
             
             <div className="space-y-2 text-sm">
                <div className="flex justify-between border-b border-zinc-800 pb-1">
                   <span className="text-zinc-500">Price (Scraped)</span>
                   <span className="font-mono">{report.discrepancies?.scraped?.price_predicted || 0} BGN</span>
                </div>
                <div className="flex justify-between border-b border-zinc-800 pb-1">
                   <span className="text-zinc-500">Area (Official)</span>
                   <span className="font-mono">{report.discrepancies?.cadastre?.official_area || '?'} m²</span>
                </div>
                <div className="flex justify-between border-b border-zinc-800 pb-1">
                   <span className="text-zinc-500">Type</span>
                   <span className="font-mono">{report.discrepancies?.ai?.building_type || 'ANALYZING...'}</span>
                </div>
             </div>
          </CardContent>
        </Card>
      </div>

      {/* CENTER COL: MAPS & FLAGS */}
      <div className="col-span-12 md:col-span-4 row-span-2 space-y-4">
         <Card className="bg-zinc-900 border-zinc-800 h-1/2">
            <CardHeader>
               <CardTitle className="text-sm font-mono text-zinc-400">GEOSPATIAL_TRIANGULATION</CardTitle>
            </CardHeader>
            <CardContent className="h-32 flex items-center justify-center text-zinc-600 font-mono text-xs">
               [MAP_MODULE_LOADING]
            </CardContent>
         </Card>

         <Card className="bg-zinc-900 border-zinc-800 h-[calc(50%-1rem)]">
            <CardHeader>
               <CardTitle className="text-sm font-mono text-zinc-400">RED_FLAGS</CardTitle>
            </CardHeader>
            <CardContent>
               <ul className="space-y-2 text-xs font-mono">
                  {report.discrepancies?.legal_status?.legal_flags?.map((flag, i) => (
                     <li key={i} className="text-red-400 flex gap-2">
                        <ShieldAlert className="w-4 h-4 shrink-0" />
                        {flag}
                     </li>
                  ))}
                  {report.discrepancies?.legal_status?.legal_flags?.length === 0 && (
                     <li className="text-emerald-500 flex gap-2">
                        <ShieldCheck className="w-4 h-4" />
                        NO_LEGAL_OBJECTIONS_FOUND
                     </li>
                  )}
               </ul>
            </CardContent>
         </Card>
      </div>

      {/* RIGHT COL: LOGS */}
      <div className="col-span-12 md:col-span-4 row-span-2 h-full">
        <ForensicLog 
          status={report.status} 
          logs={[
             "Initializing forensic handshake...",
             report.status !== 'PENDING' ? "Scraper data received." : "Waiting for scraper...",
             report.discrepancies?.cadastre?.cadastre_id ? \`Cadastre ID identified: \${report.discrepancies.cadastre.cadastre_id}\` : null,
             report.discrepancies?.ai?.visual_red_flags?.length ? "Visual anomalies detected via Gemini." : null,
             "Audit cycle active."
          ].filter(Boolean) as string[]} 
        />
      </div>

    </div>
  );
}
EOF

# Forensic Log Component
cat > src/app/cases/[id]/_components/ForensicLog.tsx <<EOF
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

interface LogProps {
  logs: string[];
  status: string;
}

export function ForensicLog({ logs, status }: LogProps) {
  return (
    <div className="h-full flex flex-col bg-zinc-950 border border-zinc-800 rounded-md font-mono text-xs p-4 shadow-inner shadow-black/50">
      <div className="flex justify-between items-center border-b border-zinc-800 pb-2 mb-2">
        <span className="text-zinc-500 font-bold tracking-wider">SYSTEM_LOG</span>
        <span className={cn(
          "tracking-widest",
          status === 'PROCESSING' || status === 'PENDING' ? 'text-amber-500 animate-pulse' : 'text-emerald-500'
        )}>
          {status}
        </span>
      </div>
      <ScrollArea className="flex-1 pr-4">
        <div className="space-y-2">
          {logs.map((log, i) => (
            <div key={i} className="text-zinc-400">
              <span className="text-emerald-900 mr-2">{'>'}</span>
              {log}
            </div>
          ))}
          {(status === 'PROCESSING' || status === 'PENDING') && (
            <div className="text-zinc-600 animate-pulse">
              <span className="mr-2 text-emerald-900">{'>'}</span>
              AWAITING_WORKER_RESPONSE...
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
EOF

# Risk Badge Component
cat > src/app/cases/[id]/_components/RiskBadge.tsx <<EOF
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function RiskBadge({ score, status }: { score: number; status: string }) {
  let color = "bg-zinc-800 text-zinc-400"; // Default
  let label = "PENDING";

  if (status === "VERIFIED" || status === "MANUAL_REVIEW") {
      if (score < 30) {
        color = "bg-emerald-950 text-emerald-400 border-emerald-800";
        label = "LOW RISK";
      } else if (score < 70) {
        color = "bg-amber-950 text-amber-400 border-amber-800";
        label = "CAUTION";
      } else {
        color = "bg-red-950 text-red-400 border-red-800";
        label = "HIGH RISK";
      }
  }

  return (
    <div className="flex flex-col items-end">
        <div className="text-[10px] text-zinc-500 font-mono mb-1">AGGREGATE_RISK_SCORE</div>
        <div className="flex items-center gap-3">
            <span className={cn("font-mono text-3xl font-bold", 
                score > 60 ? "text-red-500" : "text-emerald-500"
            )}>
                {score}<span className="text-zinc-700 text-lg">/100</span>
            </span>
            <Badge variant="outline" className={cn("h-6", color)}>
                {label}
            </Badge>
        </div>
    </div>
  );
}
EOF

echo -e "\033[0;32m>>> EXECUTION COMPLETE.\033[0m"
echo -e "\033[0;32m>>> Run 'cd $APP_NAME && npm run dev' to launch The Digital Notary.\033[0m"