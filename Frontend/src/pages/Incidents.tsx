import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { TableSkeleton } from "@/components/LoadingSkeleton";
import { fetchIncidents } from "@/api/api";
import type { Incident } from "@/api/api";
import { CheckCircle, XCircle } from "lucide-react";

const Incidents = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIncidents().then(data => { setIncidents(data); setLoading(false); });
  }, []);

  return (
    <div className="container py-6 space-y-6">
      <h1 className="text-2xl font-bold">Incidents</h1>

      <Card className="bg-card">
        <CardContent className="pt-6">
          {loading ? <TableSkeleton rows={5} /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2">Branch</th><th className="pb-2">Description</th><th className="pb-2">Auto-Healed?</th>
                    <th className="pb-2">Heal Action</th><th className="pb-2">Duration</th><th className="pb-2">Start → End</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map(inc => (
                    <tr
                      key={inc.id}
                      className={`border-b border-border/50 ${
                        inc.autoHealed ? "bg-status-healthy/5" : "bg-status-critical/5"
                      }`}
                    >
                      <td className="py-2.5 text-xs font-medium">{inc.branchName}</td>
                      <td className="py-2.5 text-xs">{inc.description}</td>
                      <td className="py-2.5">
                        {inc.autoHealed ? (
                          <span className="flex items-center gap-1 text-status-healthy text-xs">
                            <CheckCircle className="h-3.5 w-3.5" /> Yes
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-status-critical text-xs">
                            <XCircle className="h-3.5 w-3.5" /> No
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 text-xs text-muted-foreground">{inc.healAction}</td>
                      <td className="py-2.5 text-xs font-mono">{inc.duration}</td>
                      <td className="py-2.5 text-[10px] text-muted-foreground font-mono">
                        {new Date(inc.startTime).toLocaleString()}
                        {inc.endTime ? ` → ${new Date(inc.endTime).toLocaleTimeString()}` : " → ongoing"}
                      </td>
                    </tr>
                  ))}
                  {incidents.length === 0 && (
                    <tr><td colSpan={6} className="py-8 text-center text-muted-foreground text-sm">No incidents recorded</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Incidents;
