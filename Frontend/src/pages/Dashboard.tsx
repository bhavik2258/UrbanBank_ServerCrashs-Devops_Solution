import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Server, AlertTriangle, TrendingUp, Building2 } from "lucide-react";
import BranchCard from "@/components/BranchCard";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import {
  fetchBranches,
  getDashboardSummary,
  simulateFailure,
  subscribeDashboardUpdates,
  triggerHeal,
} from "@/api/api";
import type { Branch } from "@/api/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

const Dashboard = () => {
  const [allBranches, setAllBranches] = useState<Branch[]>([]);
  const [selectedBank, setSelectedBank] = useState<string>("");
  const [summary, setSummary] = useState<{ totalBranches: number; activeAlerts: number; incidentsToday: number; avgUptime: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamConnected, setStreamConnected] = useState(false);

  const load = async () => {
    try {
      const [b, s] = await Promise.all([fetchBranches(), getDashboardSummary()]);
      setAllBranches(b);
      setSummary(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    let pollingTimer: ReturnType<typeof setInterval> | undefined;

    const startPolling = () => {
      if (pollingTimer) {
        return;
      }
      pollingTimer = setInterval(() => {
        void load();
      }, 5000);
    };

    const stopPolling = () => {
      if (!pollingTimer) {
        return;
      }
      clearInterval(pollingTimer);
      pollingTimer = undefined;
    };

    void load();
    startPolling();

    const unsubscribe = subscribeDashboardUpdates({
      onConnected: () => {
        if (!mounted) {
          return;
        }
        setStreamConnected(true);
        stopPolling();
      },
      onMetricsUpdated: () => {
        if (!mounted) {
          return;
        }
        void load();
      },
      onDisconnected: () => {
        if (!mounted) {
          return;
        }
        setStreamConnected(false);
        startPolling();
      },
      onError: () => {
        if (!mounted) {
          return;
        }
        setStreamConnected(false);
        startPolling();
      },
    });

    return () => {
      mounted = false;
      stopPolling();
      unsubscribe();
    };
  }, []);

  const handleFailure = async (id: string) => {
    await simulateFailure(id);
    toast.error("🔴 Failure simulated", { description: `Branch ${id} is now in critical state` });
    load();
  };

  const handleHeal = async (id: string) => {
    await triggerHeal(id);
    toast.success("🟢 Auto-heal triggered", { description: `Branch ${id} has been restored` });
    load();
  };

  // Get unique bank names for the dropdown
  const uniqueBanks = Array.from(new Set(allBranches.map((b) => b.bank_name))).sort();

  useEffect(() => {
    if (!selectedBank && uniqueBanks.length > 0) {
      setSelectedBank(uniqueBanks[0]);
    }
  }, [selectedBank, uniqueBanks]);
  
  // Filter branches based on selected bank
  const filteredBranches = selectedBank
    ? allBranches.filter((b) => b.bank_name === selectedBank)
    : allBranches;

  const stats = summary
    ? [
        { label: "Total Monitored Banks", value: uniqueBanks.length, icon: Building2 },
        { label: "Total Monitored Endpoints", value: summary.totalBranches, icon: Server },
        { label: "Active Critical Alerts", value: summary.activeAlerts, icon: AlertTriangle },
        { label: "Avg System Uptime", value: `${summary.avgUptime}%`, icon: TrendingUp },
      ]
    : [];

  return (
    <div className="container py-6 space-y-6">
      {/* Top Organization Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Organization View</h1>
          <p className="text-muted-foreground text-sm mt-1">Select a tenant to view their global branch infrastructure health.</p>
        </div>
        
        <div className="flex items-center gap-3 bg-muted/50 p-2 rounded-lg border w-full md:w-auto">
          <Label className="whitespace-nowrap font-medium text-sm text-foreground/80 pl-2">Select Bank:</Label>
          <Select value={selectedBank} onValueChange={setSelectedBank}>
            <SelectTrigger className="w-[280px] bg-background">
              <SelectValue placeholder="Choose A Bank..." />
            </SelectTrigger>
            <SelectContent>
              {uniqueBanks.map((bank) => (
                <SelectItem key={bank} value={bank}>{bank}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Bar */}
      <h2 className="text-xl font-semibold tracking-tight">{selectedBank || "Global"} Infrastructure Overview</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-border bg-card p-4 animate-pulse h-20" />
            ))
          : stats.map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-lg border border-border bg-card p-4 flex items-center gap-3 shadow-sm">
                <div className="rounded-md bg-primary/10 p-2 border border-primary/20">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold font-mono tracking-tight">{value}</p>
                  <p className="text-xs text-muted-foreground font-medium">{label}</p>
                </div>
              </div>
            ))}
      </div>

      <div className="pt-2">
        <h3 className="text-xl font-semibold tracking-tight mb-4 flex items-center gap-2">
          {selectedBank} Active Branches <span className="inline-flex items-center justify-center rounded-full bg-muted text-muted-foreground text-xs w-6 h-6">{filteredBranches.length}</span>
        </h3>
        
        {/* Branch Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
            : filteredBranches.map(b => (
                <BranchCard key={b.id} branch={b} onSimulateFailure={handleFailure} onTriggerHeal={handleHeal} />
              ))}
          
          {filteredBranches.length === 0 && !loading && (
            <div className="col-span-full py-16 text-center border rounded-lg border-dashed">
              <Building2 className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-50" />
              <h3 className="text-lg font-medium">No Branches Found</h3>
              <p className="text-sm text-muted-foreground">Select a valid bank from the dropdown above to view branches.</p>
            </div>
          )}
        </div>
      </div>

      <div className="pt-8 text-center border-t border-border/50">
        <div className="inline-flex items-center justify-center gap-2 text-xs font-medium bg-muted/50 px-3 py-1.5 rounded-full text-muted-foreground border">
          <div className={`w-1.5 h-1.5 rounded-full ${streamConnected ? "bg-green-500 animate-pulse" : "bg-amber-500"}`} />
          {streamConnected ? "Live Datastream: Connected (SSE)" : "Live Datastream: Polling every 5s (fallback)"}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
