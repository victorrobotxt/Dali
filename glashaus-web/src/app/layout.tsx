import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Providers from "./providers";

const jbMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "GLASHAUS // INTEL",
  description: "Automated Real Estate Forensics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${jbMono.variable} grid-bg min-h-screen relative`}>
        <div className="scanline" />
        <nav className="flex justify-between items-center p-6 border-b border-zinc-900 bg-black/90 backdrop-blur-sm relative z-50">
          <div className="text-sm md:text-lg font-bold tracking-tighter flex items-center gap-2">
            GLASHAUS <span className="text-zinc-700">//</span> v1.1<span className="cursor-blink"></span>
          </div>
          <div className="text-[9px] uppercase tracking-widest text-emerald-500 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            LIVE_NODE_CONNECTED
          </div>
        </nav>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
