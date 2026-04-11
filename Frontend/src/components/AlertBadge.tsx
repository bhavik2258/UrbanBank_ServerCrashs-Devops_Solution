import { Badge } from "@/components/ui/badge";

interface AlertBadgeProps {
  severity: "critical" | "warning" | "info";
}

const styles: Record<string, string> = {
  critical: "bg-status-critical/20 text-status-critical border-status-critical/30",
  warning: "bg-status-warning/20 text-status-warning border-status-warning/30",
  info: "bg-primary/20 text-primary border-primary/30",
};

const AlertBadge = ({ severity }: AlertBadgeProps) => (
  <Badge variant="outline" className={`uppercase text-[10px] font-mono font-bold ${styles[severity]}`}>
    {severity}
  </Badge>
);

export default AlertBadge;
