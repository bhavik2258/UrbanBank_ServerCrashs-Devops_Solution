interface StatusPillProps {
  status: "UP" | "DOWN";
  label: string;
}

const StatusPill = ({ status, label }: StatusPillProps) => (
  <div className="flex items-center gap-1.5">
    <span className="text-xs text-muted-foreground">{label}</span>
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-mono font-bold ${
        status === "UP"
          ? "bg-status-healthy/15 text-status-healthy"
          : "bg-status-critical/15 text-status-critical"
      }`}
    >
      {status}
    </span>
  </div>
);

export default StatusPill;
