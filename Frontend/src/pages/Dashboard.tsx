import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { toast } from "sonner";
import { Server, AlertTriangle, TrendingUp, Building2 } from "lucide-react";
import BranchCard from "@/components/BranchCard";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import {
  fetchBranches,
  getBankOpsKpis,
  getDashboardSummary,
  simulateFailure,
  subscribeDashboardUpdates,
  triggerHeal,
} from "@/api/api";
import type { BankOpsKpis, Branch } from "@/api/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { hasPermission } from "@/lib/auth";

const Dashboard = () => {
  const INITIAL_VISIBLE_BRANCHES = 24;
  const [allBranches, setAllBranches] = useState<Branch[]>([]);
  const [selectedBank, setSelectedBank] = useState<string>("");
  const [summary, setSummary] = useState<{ totalBranches: number; activeAlerts: number; incidentsToday: number; avgUptime: number } | null>(null);
  const [bankOpsKpis, setBankOpsKpis] = useState<BankOpsKpis | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamConnected, setStreamConnected] = useState(false);
  const [visibleBranchCount, setVisibleBranchCount] = useState(INITIAL_VISIBLE_BRANCHES);
  const [isSwitchingBank, startBankTransition] = useTransition();
  const canOperate = hasPermission("simulate_incident") && hasPermission("trigger_heal");

  const handleBankChange = useCallback((value: string) => {
    startBankTransition(() => {
      setSelectedBank(value);
    });
  }, []);

  const load = useCallback(async () => {
    try {
      const [b, s, k] = await Promise.all([fetchBranches(), getDashboardSummary(), getBankOpsKpis()]);
      setAllBranches(b);
      setSummary(s);
      setBankOpsKpis(k);
    } catch (error) {
      const description = error instanceof Error ? error.message : "Unexpected network error";
      toast.error("Failed to load dashboard data", { description });
    } finally {
      setLoading(false);
    }
  }, []);

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
  }, [load]);

  const handleFailure = useCallback(async (id: string) => {
    if (!canOperate) {
      toast.info("Read-only role", { description: "Your role does not allow incident simulation." });
      return;
    }
    await simulateFailure(id);
    toast.error("🔴 Failure simulated", { description: `Branch ${id} is now in critical state` });
    void load();
  }, [canOperate, load]);

  const handleHeal = useCallback(async (id: string) => {
    if (!canOperate) {
      toast.info("Read-only role", { description: "Your role does not allow heal operations." });
      return;
    }
    await triggerHeal(id);
    toast.success("🟢 Auto-heal triggered", { description: `Branch ${id} has been restored` });
    void load();
  }, [canOperate, load]);

  const uniqueBanks = useMemo(
    () => Array.from(new Set(allBranches.map((branch) => branch.bank_name))).sort(),
    [allBranches]
  );

  useEffect(() => {
    if (!selectedBank && uniqueBanks.length > 0) {
      setSelectedBank(uniqueBanks[0]);
    }
  }, [selectedBank, uniqueBanks]);

  useEffect(() => {
    setVisibleBranchCount(INITIAL_VISIBLE_BRANCHES);
  }, [selectedBank]);

  const filteredBranches = useMemo(
    () => (selectedBank ? allBranches.filter((branch) => branch.bank_name === selectedBank) : allBranches),
    [allBranches, selectedBank]
  );

  const displayedBranches = useMemo(
    () => filteredBranches.slice(0, visibleBranchCount),
    [filteredBranches, visibleBranchCount]
  );

  const hasMoreBranches = displayedBranches.length < filteredBranches.length;

  const stats = useMemo(
    () =>
      summary
        ? [
            { label: "Total Monitored Banks", value: uniqueBanks.length, icon: Building2 },
            { label: "Total Monitored Endpoints", value: summary.totalBranches, icon: Server },
            { label: "Active Critical Alerts", value: summary.activeAlerts, icon: AlertTriangle },
            { label: "Avg System Uptime", value: `${summary.avgUptime}%`, icon: TrendingUp },
          ]
        : [],
    [summary, uniqueBanks.length]
  );

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
          <Select value={selectedBank} onValueChange={handleBankChange}>
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
      {isSwitchingBank ? <p className="text-xs text-muted-foreground">Optimizing view update...</p> : null}
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

      <div className="space-y-3">
        <h3 className="text-lg font-semibold tracking-tight">Bank Operations KPIs</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Core Txn Success Rate</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? `${bankOpsKpis.transactionSuccessRatePercent}%` : "--"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Auth Failures (Last Hour)</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? bankOpsKpis.authenticationFailuresLastHour : "--"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Transfer P95 Latency</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? `${bankOpsKpis.transferP95LatencyMs} ms` : "--"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Transfer Error Rate</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? `${bankOpsKpis.transferErrorRatePercent}%` : "--"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">ATM/POS/Network Uptime</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? `${bankOpsKpis.atmPosNetworkUptimePercent}%` : "--"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">DB Replication Lag</p>
            <p className="text-2xl font-bold font-mono mt-1">{bankOpsKpis ? `${bankOpsKpis.dbReplicationLagSeconds}s` : "--"}</p>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm font-semibold mb-3">Alert Volume By Branch And Severity (24h)</p>
          {!bankOpsKpis || bankOpsKpis.alertVolumeByBranch.length === 0 ? (
            <p className="text-sm text-muted-foreground">No alerts in last 24 hours.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground uppercase">
                    <th className="py-2 pr-3">Branch</th>
                    <th className="py-2 pr-3">Critical</th>
                    <th className="py-2 pr-3">Warning</th>
                    <th className="py-2 pr-3">Info</th>
                    <th className="py-2 pr-3">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {bankOpsKpis.alertVolumeByBranch.map((row) => (
                    <tr key={row.branchId} className="border-b border-border/50">
                      <td className="py-2 pr-3">{row.branchName}</td>
                      <td className="py-2 pr-3 font-mono">{row.critical}</td>
                      <td className="py-2 pr-3 font-mono">{row.warning}</td>
                      <td className="py-2 pr-3 font-mono">{row.info}</td>
                      <td className="py-2 pr-3 font-mono font-semibold">{row.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="pt-2">
        <h3 className="text-xl font-semibold tracking-tight mb-4 flex items-center gap-2">
          {selectedBank} Active Branches <span className="inline-flex items-center justify-center rounded-full bg-muted text-muted-foreground text-xs w-6 h-6">{filteredBranches.length}</span>
        </h3>
        
        {/* Branch Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
            : displayedBranches.map((b) => (
                <BranchCard
                  key={b.id}
                  branch={b}
                  onSimulateFailure={handleFailure}
                  onTriggerHeal={handleHeal}
                  canOperate={canOperate}
                />
              ))}
          
          {filteredBranches.length === 0 && !loading && (
            <div className="col-span-full py-16 text-center border rounded-lg border-dashed">
              <Building2 className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-50" />
              <h3 className="text-lg font-medium">No Branches Found</h3>
              <p className="text-sm text-muted-foreground">Select a valid bank from the dropdown above to view branches.</p>
            </div>
          )}
        </div>

        {hasMoreBranches && !loading && (
          <div className="mt-4 flex justify-center">
            <button
              type="button"
              className="inline-flex items-center rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
              onClick={() => setVisibleBranchCount((count) => count + INITIAL_VISIBLE_BRANCHES)}
            >
              Show More Branches ({filteredBranches.length - displayedBranches.length} remaining)
            </button>
          </div>
        )}
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
