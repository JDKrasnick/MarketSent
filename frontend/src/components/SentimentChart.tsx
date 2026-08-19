import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import type { TrendDataPoint } from "../types";

interface SentimentChartProps {
    data: TrendDataPoint[];
    height?: number;
}

export function SentimentChart({ data, height = 300 }: SentimentChartProps) {
    // Format data for the chart
    const chartData = data.map((point) => ({
        date: new Date(point.date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
        }),
        positive: (point.avg_positive || 0) * 100,
        negative: (point.avg_negative || 0) * 100,
        neutral: (point.avg_neutral || 0) * 100,
        posts: point.post_count,
    }));

    return (
        <div
            className="sentiment-chart"
            style={{ height }}
            role="img"
            aria-label={`Stacked sentiment trend chart with ${chartData.length} daily data points`}
        >
            <ResponsiveContainer>
                <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: "#404040" }}
                        tickLine={false}
                    />
                    <YAxis
                        tick={{ fontSize: 12, fill: "#404040" }}
                        tickLine={false}
                        domain={[0, 100]}
                        tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                        contentStyle={{
                            background: "#fff",
                            border: "1px solid #e0e0e0",
                            fontSize: "12px",
                        }}
                        formatter={(value) => `${Number(value ?? 0).toFixed(1)}%`}
                    />
                    <Area
                        type="monotone"
                        dataKey="positive"
                        stackId="1"
                        stroke="#00b894"
                        fill="#55efc4"
                        name="Positive"
                        isAnimationActive={false}
                    />
                    <Area
                        type="monotone"
                        dataKey="neutral"
                        stackId="1"
                        stroke="#0984e3"
                        fill="#74b9ff"
                        name="Neutral"
                        isAnimationActive={false}
                    />
                    <Area
                        type="monotone"
                        dataKey="negative"
                        stackId="1"
                        stroke="#d63031"
                        fill="#ff7675"
                        name="Negative"
                        isAnimationActive={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
