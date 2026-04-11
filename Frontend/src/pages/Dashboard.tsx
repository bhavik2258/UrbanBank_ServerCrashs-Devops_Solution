import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Server, AlertTriangle, Activity, TrendingUp } from "lucide-react";
import BranchCard from "@/components/BranchCard";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import { fetchBranches, getDashboardSummary, simulateFailure, triggerHeal } from "@/api/api";
import type { Branch } from "@/api/api";

const Dashboard = () => {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [summary, setSummary] = useState<{ totalBranches: number; activeAlerts: number; incidentsToday: number; avgUptime: number } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const [b, s] = await Promise.all([fetchBranches(), getDashboardSummary()]);
    setBranches(b);
    setSummary(s);
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
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

  const stats = summary
    ? [
        { label: "Total Branches", value: summary.totalBranches, icon: Server },
        { label: "Active Alerts", value: summary.activeAlerts, icon: AlertTriangle },
        { label: "Incidents Today", value: summary.incidentsToday, icon: Activity },
        { label: "Avg Uptime", value: `${summary.avgUptime}%`, icon: TrendingUp },
      ]
    : [];

  return (
    <div className="container py-6 space-y-6">
      {/* Summary Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-border bg-card p-4 animate-pulse h-20" />
            ))
          : stats.map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-lg border border-border bg-card p-4 flex items-center gap-3">
                <div className="rounded-md bg-accent p-2">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold font-mono">{value}</p>
                  <p className="text-xs text-muted-foreground">{label}</p>
                </div>
              </div>
            ))}
      </div>

      {/* Branch Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)
          : branches.map(b => (
              <BranchCard key={b.id} branch={b} onSimulateFailure={handleFailure} onTriggerHeal={handleHeal} />
            ))}
      </div>

      <p className="text-[10px] text-muted-foreground text-center font-mono">
        Auto-refreshing every 15s · Live backend simulation data
      </p>
    </div>
  );
};

export default Dashboard;
