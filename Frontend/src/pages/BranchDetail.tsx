import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import UptimeChart from "@/components/UptimeChart";
import AlertBadge from "@/components/AlertBadge";
import IncidentTimeline from "@/components/IncidentTimeline";
import MetricGauge from "@/components/MetricGauge";
import StatusPill from "@/components/StatusPill";
import { CardSkeleton, TableSkeleton } from "@/components/LoadingSkeleton";
import { fetchBranch, fetchMetricHistory, fetchAlertsByBranch, fetchIncidentsByBranch } from "@/api/api";
import type { Branch, MetricReading, Alert, Incident } from "@/api/api";

const BranchDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [branch, setBranch] = useState<Branch | null>(null);
  const [history, setHistory] = useState<MetricReading[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      fetchBranch(id),
      fetchMetricHistory(id),
      fetchAlertsByBranch(id),
      fetchIncidentsByBranch(id),
    ]).then(([b, h, a, i]) => {
      setBranch(b || null);
      setHistory(h);
      setAlerts(a);
      setIncidents(i);
      setLoading(false);
    });
  }, [id]);

  if (loading) return (
    <div className="container py-6 space-y-6">
      <CardSkeleton />
      <TableSkeleton rows={3} />
    </div>
  );

  if (!branch) return (
    <div className="container py-12 text-center">
      <p className="text-muted-foreground">Branch not found</p>
      <Button variant="outline" className="mt-4" onClick={() => navigate("/")}>Go back</Button>
    </div>
  );

  return (
    <div className="container py-6 space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/")} className="text-muted-foreground">
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
      </Button>

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">{branch.name}</h1>
        <span className="text-xs text-muted-foreground">{branch.location}</span>
      </div>

      {/* Metrics overview */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="bg-card">
          <CardHeader className="pb-3"><CardTitle className="text-sm">Live Metrics</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <MetricGauge label="CPU" value={branch.metrics.cpu} />
            <MetricGauge label="RAM" value={branch.metrics.ram} />
            <MetricGauge label="Disk" value={branch.metrics.disk} />
            <div className="flex gap-4 pt-2">
              {branch.services.map(s => <StatusPill key={s.name} label={s.name} status={s.status} />)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card">
          <CardHeader className="pb-3"><CardTitle className="text-sm">Metric History (60 readings)</CardTitle></CardHeader>
          <CardContent>
            <UptimeChart data={history} />
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      <Card className="bg-card">
        <CardHeader className="pb-3"><CardTitle className="text-sm">Recent Alerts</CardTitle></CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No alerts for this branch</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2">Type</th><th className="pb-2">Severity</th><th className="pb-2">Message</th><th className="pb-2">Time</th><th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map(a => (
                    <tr key={a.id} className="border-b border-border/50">
                      <td className="py-2 font-mono text-xs">{a.type}</td>
                      <td className="py-2"><AlertBadge severity={a.severity} /></td>
                      <td className="py-2 text-xs">{a.message}</td>
                      <td className="py-2 text-xs text-muted-foreground font-mono">{new Date(a.firedAt).toLocaleTimeString()}</td>
                      <td className="py-2">
                        <span className={`text-xs font-mono ${a.resolved ? "text-status-healthy" : "text-status-critical"}`}>
                          {a.resolved ? "Resolved" : "Active"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Incidents */}
      <Card className="bg-card">
        <CardHeader className="pb-3"><CardTitle className="text-sm">Incident Timeline</CardTitle></CardHeader>
        <CardContent>
          <IncidentTimeline incidents={incidents} />
        </CardContent>
      </Card>
    </div>
  );
};

export default BranchDetail;
