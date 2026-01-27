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
