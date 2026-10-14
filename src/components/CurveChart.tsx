import type { Limits, Point } from "../types";
import { pwmAt } from "../curve";

const W = 260;
const H = 150;
const PAD = { left: 30, right: 8, top: 8, bottom: 22 };
const ACCENT = "#1a9fff";
const MUTED = "rgba(255,255,255,0.35)";
const GRID = "rgba(255,255,255,0.08)";
const SAVED = "rgba(255,255,255,0.45)";

interface Props {
  points: Point[];
  saved?: Point[];
  limits: Limits;
  currentTemp: number | null;
}

export function CurveChart({ points, saved, limits, currentTemp }: Props) {
  const tMin = limits.temp_min_c + 10;
  const tMax = limits.temp_max_c - 5;
  const x = (t: number) => PAD.left + ((Math.min(Math.max(t, tMin), tMax) - tMin) / (tMax - tMin)) * (W - PAD.left - PAD.right);
  const y = (pwm: number) => PAD.top + (1 - pwm / limits.pwm_max) * (H - PAD.top - PAD.bottom);
  const path = (pts: Point[]) => {
    if (pts.length === 0) return "";
    const ext: Point[] = [[tMin, pts[0][1]], ...pts, [tMax, pts[pts.length - 1][1]]];
    return ext.map(([t, p], i) => `${i ? "L" : "M"}${x(t).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
  };
  const xTicks = [40, 60, 80, 100].filter((t) => t > tMin && t < tMax);
  const yTicks = [0, 25, 50, 75, 100];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Fan curve">
      {yTicks.map((pct) => {
        const yy = y((pct / 100) * limits.pwm_max);
        return (
          <g key={`y${pct}`}>
            <line x1={PAD.left} x2={W - PAD.right} y1={yy} y2={yy} stroke={GRID} />
            <text x={PAD.left - 4} y={yy + 3} fontSize="8" textAnchor="end" fill={MUTED}>{pct}%</text>
          </g>
        );
      })}
      {xTicks.map((t) => (
        <g key={`x${t}`}>
          <line x1={x(t)} x2={x(t)} y1={PAD.top} y2={H - PAD.bottom} stroke={GRID} />
          <text x={x(t)} y={H - PAD.bottom + 11} fontSize="8" textAnchor="middle" fill={MUTED}>{t}°</text>
        </g>
      ))}
      {saved && <path d={path(saved)} fill="none" stroke={SAVED} strokeWidth="1" strokeDasharray="3 3" />}
      <path d={path(points)} fill="none" stroke={ACCENT} strokeWidth="2" />
      {points.map(([t, p], i) => (
        <circle key={i} cx={x(t)} cy={y(p)} r="3" fill={ACCENT} />
      ))}
      {currentTemp !== null && (
        <g>
          <line x1={x(currentTemp)} x2={x(currentTemp)} y1={PAD.top} y2={H - PAD.bottom} stroke="#ffb547" strokeWidth="1" />
          <circle cx={x(currentTemp)} cy={y(pwmAt(points, currentTemp))} r="4" fill="none" stroke="#ffb547" strokeWidth="1.5" />
        </g>
      )}
    </svg>
  );
}
