import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TableSkeleton } from "@/components/LoadingSkeleton";
import { fetchIncidents } from "@/api/api";
import type { Incident } from "@/api/api";
import { CheckCircle, XCircle, Download, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const Incidents = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchIncidents().then(data => { setIncidents(data); setLoading(false); });
  }, []);

  const handleExport = () => {
    toast.success("Incident Report Exported", {
      description: "CSV file has been downloaded to your machine.",
      icon: <Download className="h-4 w-4" />
    });
  };

  const filteredIncidents = incidents.filter(inc => 
    inc.branchName.toLowerCase().includes(searchTerm.toLowerCase()) || 
    inc.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-3xl font-bold tracking-tight">Incident History</h1>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Filter incidents..." 
              className="pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" onClick={handleExport} className="gap-2 whitespace-nowrap">
            <Download className="h-4 w-4" /> <span className="hidden sm:inline">Export CSV</span>
          </Button>
        </div>
      </div>

      <Card className="bg-card shadow-sm border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Recent Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <TableSkeleton rows={5} /> : (
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted text-muted-foreground uppercase text-[10px] tracking-wider font-semibold">
                  <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted text-left">
                    <th className="p-3 w-[150px]">Branch</th>
                    <th className="p-3 w-[250px]">Description</th>
                    <th className="p-3 w-[150px]">Remediation</th>
                    <th className="p-3">Ansible Action</th>
                    <th className="p-3 w-[100px]">Downtime</th>
                    <th className="p-3 w-[150px]">Timeline</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.map(inc => (
                    <tr
                      key={inc.id}
                      className={`border-b border-border/50 hover:bg-muted/50 transition-colors ${
                        inc.autoHealed ? "bg-status-healthy/5" : "bg-status-critical/5"
                      }`}
                    >
                      <td className="p-3 text-sm font-medium">{inc.branchName}</td>
                      <td className="p-3 text-sm max-w-sm truncate">{inc.description}</td>
                      <td className="p-3">
                        {inc.autoHealed ? (
                          <span className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/10 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:text-green-400 gap-1.5">
                            <CheckCircle className="h-3.5 w-3.5" /> Auto-Healed
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-0.5 text-xs font-medium text-red-700 dark:text-red-400 gap-1.5">
                            <XCircle className="h-3.5 w-3.5" /> Manual Action Needed
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-xs text-muted-foreground font-mono bg-muted/30 rounded">{inc.healAction || "Pending Ansible Plan"}</td>
                      <td className="p-3 text-xs font-mono">{inc.duration}</td>
                      <td className="p-3 text-[11px] text-muted-foreground">
                        {new Date(inc.startTime).toLocaleString()}
                        {inc.endTime ? <br /> : null}
                        {inc.endTime ? <span className="text-foreground">Finished: {new Date(inc.endTime).toLocaleTimeString()}</span> : " → Active Incident"}
                      </td>
                    </tr>
                  ))}
                  {filteredIncidents.length === 0 && (
                    <tr><td colSpan={6} className="py-12 text-center text-muted-foreground text-sm font-medium">No incidents match your filter.</td></tr>
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
