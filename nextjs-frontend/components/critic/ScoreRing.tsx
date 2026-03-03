"use client";

import { cn } from "@/lib/utils";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

function getScoreColor(score: number): string {
  if (score < 50) return "rgb(239 68 68)";   // red-500
  if (score < 80) return "rgb(245 158 11)";  // amber-500
  return "rgb(16 185 129)";                   // emerald-500
}

function getScoreLabel(score: number): string {
  if (score < 50) return "Needs Work";
  if (score < 80) return "Good";
  return "Excellent";
}

export default function ScoreRing({
  score,
  size = 80,
  strokeWidth = 6,
  className,
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const dashOffset = circumference - (clampedScore / 100) * circumference;
  const color = getScoreColor(clampedScore);

  return (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="block"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />
        {/* Foreground arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      {/* Score text overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-lg font-bold leading-none"
          style={{ color }}
        >
          {clampedScore}
        </span>
        <span className="text-[9px] text-muted-foreground mt-0.5">
          {getScoreLabel(clampedScore)}
        </span>
      </div>
    </div>
  );
}
