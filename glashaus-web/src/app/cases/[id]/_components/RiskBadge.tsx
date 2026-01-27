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
