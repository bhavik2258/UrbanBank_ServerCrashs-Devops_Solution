import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import AlertBadge from "@/components/AlertBadge";
import { TableSkeleton } from "@/components/LoadingSkeleton";
import { fetchAlerts, resolveAlert } from "@/api/api";
import type { Alert } from "@/api/api";

const Alerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterBranch, setFilterBranch] = useState("all");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  const load = async () => {
    const data = await fetchAlerts();
    setAlerts(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleResolve = async (id: string) => {
    await resolveAlert(id);
    toast.success("Alert resolved");
    load();
  };

  const branches = [...new Set(alerts.map(a => a.branchName))];

  const filtered = alerts.filter(a => {
    if (filterBranch !== "all" && a.branchName !== filterBranch) return false;
    if (filterSeverity !== "all" && a.severity !== filterSeverity) return false;
    if (filterStatus === "active" && a.resolved) return false;
    if (filterStatus === "resolved" && !a.resolved) return false;
    return true;
  });

  return (
    <div className="container py-6 space-y-6">
      <h1 className="text-2xl font-bold">Alerts</h1>

      <div className="flex flex-wrap gap-3">
        <Select value={filterBranch} onValueChange={setFilterBranch}>
          <SelectTrigger className="w-[180px] bg-card"><SelectValue placeholder="Branch" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Branches</SelectItem>
            {branches.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterSeverity} onValueChange={setFilterSeverity}>
          <SelectTrigger className="w-[150px] bg-card"><SelectValue placeholder="Severity" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severity</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="info">Info</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[150px] bg-card"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="bg-card">
        <CardContent className="pt-6">
          {loading ? <TableSkeleton rows={5} /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2">Branch</th><th className="pb-2">Type</th><th className="pb-2">Severity</th>
                    <th className="pb-2">Message</th><th className="pb-2">Time</th><th className="pb-2">Status</th><th className="pb-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(a => (
                    <tr key={a.id} className="border-b border-border/50">
                      <td className="py-2.5 text-xs font-medium">{a.branchName}</td>
                      <td className="py-2.5 font-mono text-xs">{a.type}</td>
                      <td className="py-2.5"><AlertBadge severity={a.severity} /></td>
                      <td className="py-2.5 text-xs max-w-[200px] truncate">{a.message}</td>
                      <td className="py-2.5 text-xs text-muted-foreground font-mono">{new Date(a.firedAt).toLocaleTimeString()}</td>
                      <td className="py-2.5">
                        <span className={`text-xs font-mono ${a.resolved ? "text-status-healthy" : "text-status-critical"}`}>
                          {a.resolved ? "Resolved" : "Active"}
                        </span>
                      </td>
                      <td className="py-2.5">
                        {!a.resolved && (
                          <Button size="sm" variant="outline" className="text-[10px] h-7" onClick={() => handleResolve(a.id)}>
                            Mark Resolved
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={7} className="py-8 text-center text-muted-foreground text-sm">No alerts match your filters</td></tr>
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

export default Alerts;
