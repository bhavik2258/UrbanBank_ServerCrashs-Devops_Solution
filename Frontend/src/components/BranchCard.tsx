import { memo } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MapPin, Eye, Zap, HeartPulse } from "lucide-react";
import MetricGauge from "./MetricGauge";
import StatusPill from "./StatusPill";
import type { Branch } from "@/api/api";

const statusConfig = {
  healthy: { emoji: "🟢", label: "Healthy", glow: "glow-green border-status-healthy/30" },
  warning: { emoji: "🟡", label: "Warning", glow: "glow-yellow border-status-warning/30" },
  critical: { emoji: "🔴", label: "Critical", glow: "glow-red border-status-critical/30" },
};

interface BranchCardProps {
  branch: Branch;
  onSimulateFailure: (id: string) => void;
  onTriggerHeal: (id: string) => void;
  canOperate: boolean;
}

const BranchCard = ({ branch, onSimulateFailure, onTriggerHeal, canOperate }: BranchCardProps) => {
  const navigate = useNavigate();
  const cfg = statusConfig[branch.status];

  return (
    <Card className={`bg-card border ${cfg.glow} transition-all duration-300`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base font-semibold">{branch.name}</CardTitle>
            <p className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
              <MapPin className="h-3 w-3" /> {branch.location}
            </p>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-mono font-medium">
            {cfg.emoji} {cfg.label}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <MetricGauge label="CPU" value={branch.metrics.cpu} />
          <MetricGauge label="RAM" value={branch.metrics.ram} />
          <MetricGauge label="Disk" value={branch.metrics.disk} />
        </div>

        <div className="flex gap-3">
          {branch.services.map(s => (
            <StatusPill key={s.name} label={s.name} status={s.status} />
          ))}
        </div>

        <div className="flex gap-2 pt-1">
          <Button size="sm" variant="outline" className="flex-1 text-xs" onClick={() => navigate(`/branch/${branch.id}`)}>
            <Eye className="h-3 w-3 mr-1" /> Details
          </Button>
          {canOperate ? (
            <>
              <Button size="sm" variant="destructive" className="text-xs" onClick={() => onSimulateFailure(branch.id)}>
                <Zap className="h-3 w-3 mr-1" /> Fail
              </Button>
              <Button size="sm" className="text-xs bg-status-healthy text-primary-foreground hover:bg-status-healthy/90" onClick={() => onTriggerHeal(branch.id)}>
                <HeartPulse className="h-3 w-3 mr-1" /> Heal
              </Button>
            </>
          ) : (
            <span className="inline-flex items-center rounded-md border px-2 text-[11px] text-muted-foreground">
              Read-only role
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default memo(BranchCard);
