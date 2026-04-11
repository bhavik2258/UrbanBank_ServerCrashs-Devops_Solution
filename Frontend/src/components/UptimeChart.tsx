import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { MetricReading } from "@/api/api";

interface UptimeChartProps {
  data: MetricReading[];
}

const UptimeChart = ({ data }: UptimeChartProps) => {
  const formatted = data.map(d => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }));

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "hsl(215 20% 55%)" }} interval={9} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(215 20% 55%)" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(222 47% 9%)",
              border: "1px solid hsl(217 33% 18%)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="cpu" stroke="hsl(142 72% 50%)" strokeWidth={2} dot={false} name="CPU %" />
          <Line type="monotone" dataKey="ram" stroke="hsl(45 93% 58%)" strokeWidth={2} dot={false} name="RAM %" />
          <Line type="monotone" dataKey="disk" stroke="hsl(200 80% 60%)" strokeWidth={2} dot={false} name="Disk %" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UptimeChart;
