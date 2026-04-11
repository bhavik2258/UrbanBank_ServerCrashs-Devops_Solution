import { Progress } from "@/components/ui/progress";

interface MetricGaugeProps {
  label: string;
  value: number;
}

const getColor = (v: number) => {
  if (v >= 85) return "bg-status-critical";
  if (v >= 65) return "bg-status-warning";
  return "bg-status-healthy";
};

const MetricGauge = ({ label, value }: MetricGaugeProps) => (
  <div className="space-y-1">
    <div className="flex justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium">{value}%</span>
    </div>
    <div className="h-2 rounded-full bg-muted overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${getColor(value)}`}
        style={{ width: `${value}%` }}
      />
    </div>
  </div>
);

export default MetricGauge;
