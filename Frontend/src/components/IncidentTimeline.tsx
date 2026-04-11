import type { Incident } from "@/api/api";
import { CheckCircle, XCircle } from "lucide-react";

interface IncidentTimelineProps {
  incidents: Incident[];
}

const IncidentTimeline = ({ incidents }: IncidentTimelineProps) => (
  <div className="space-y-3">
    {incidents.map(inc => (
      <div
        key={inc.id}
        className={`flex items-start gap-3 rounded-lg border p-3 ${
          inc.autoHealed
            ? "border-status-healthy/20 bg-status-healthy/5"
            : "border-status-critical/20 bg-status-critical/5"
        }`}
      >
        {inc.autoHealed ? (
          <CheckCircle className="h-5 w-5 mt-0.5 text-status-healthy shrink-0" />
        ) : (
          <XCircle className="h-5 w-5 mt-0.5 text-status-critical shrink-0" />
        )}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{inc.description}</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {inc.healAction} · {inc.duration}
          </p>
          <p className="text-[10px] text-muted-foreground font-mono mt-1">
            {new Date(inc.startTime).toLocaleString()}
          </p>
        </div>
      </div>
    ))}
    {incidents.length === 0 && (
      <p className="text-sm text-muted-foreground text-center py-6">No incidents recorded</p>
    )}
  </div>
);

export default IncidentTimeline;
