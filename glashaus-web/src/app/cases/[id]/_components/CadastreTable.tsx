import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface CadastreTableProps {
  scrapedArea: number;
  officialArea: number;
  cadastreId: string;
  isExpropriated: boolean;
  hasAct16: boolean;
}

export function CadastreTable({ scrapedArea, officialArea, cadastreId, isExpropriated, hasAct16 }: CadastreTableProps) {
  const areaDiff = Math.abs(officialArea - scrapedArea);
  const isAreaSuspicious = areaDiff > 5; // > 5sqm difference

  return (
    <div className="w-full font-mono text-xs">
      <Table>
        <TableHeader className="bg-zinc-900/50">
          <TableRow className="border-zinc-800 hover:bg-transparent">
            <TableHead className="text-zinc-500 h-8">METRIC</TableHead>
            <TableHead className="text-zinc-500 h-8 text-right">OFFICIAL (REGISTRY)</TableHead>
            <TableHead className="text-zinc-500 h-8 text-right">CLAIMED (AD)</TableHead>
            <TableHead className="text-zinc-500 h-8 text-right">STATUS</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {/* AREA ROW */}
          <TableRow className="border-zinc-800 hover:bg-zinc-900/30">
            <TableCell className="font-medium text-zinc-300">Net Area (m²)</TableCell>
            <TableCell className="text-right text-zinc-300">{officialArea || "---"}</TableCell>
            <TableCell className="text-right text-zinc-300">{scrapedArea}</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline" className={cn("text-[9px] h-5", 
                isAreaSuspicious ? "text-red-400 border-red-900 bg-red-950/30" : "text-emerald-400 border-emerald-900 bg-emerald-950/30"
              )}>
                {isAreaSuspicious ? `-${areaDiff.toFixed(1)}m² DEV` : "MATCH"}
              </Badge>
            </TableCell>
          </TableRow>

          {/* ID ROW */}
          <TableRow className="border-zinc-800 hover:bg-zinc-900/30">
            <TableCell className="font-medium text-zinc-300">Unit ID</TableCell>
            <TableCell className="text-right text-zinc-300">{cadastreId || "PENDING"}</TableCell>
            <TableCell className="text-right text-zinc-500">---</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline" className="text-[9px] h-5 text-tech-blue border-zinc-800">
                VERIFIED
              </Badge>
            </TableCell>
          </TableRow>

          {/* EXPROPRIATION ROW */}
          <TableRow className="border-zinc-800 hover:bg-zinc-900/30">
            <TableCell className="font-medium text-zinc-300">Expropriation</TableCell>
            <TableCell className="text-right text-zinc-300">
                {isExpropriated ? "RISK FOUND" : "Clean Title"}
            </TableCell>
            <TableCell className="text-right text-zinc-500">---</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline" className={cn("text-[9px] h-5", 
                isExpropriated ? "text-red-500 border-red-900 animate-pulse" : "text-emerald-500 border-emerald-900"
              )}>
                {isExpropriated ? "CRITICAL" : "SAFE"}
              </Badge>
            </TableCell>
          </TableRow>

           {/* ACT 16 ROW */}
           <TableRow className="border-zinc-800 hover:bg-zinc-900/30">
            <TableCell className="font-medium text-zinc-300">Act 16</TableCell>
            <TableCell className="text-right text-zinc-300">
                {hasAct16 ? "Issued" : "Not Found"}
            </TableCell>
            <TableCell className="text-right text-zinc-500">---</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline" className={cn("text-[9px] h-5", 
                !hasAct16 ? "text-amber-500 border-amber-900" : "text-emerald-500 border-emerald-900"
              )}>
                {hasAct16 ? "LEGAL" : "PENDING"}
              </Badge>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  )
}