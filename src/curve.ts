import type { Limits, Point } from "./types";

export const pwmToPercent = (pwm: number, max: number) => Math.round((pwm / max) * 100);
export const percentToPwm = (pct: number, max: number) => Math.round((pct / 100) * max);

export function pwmAt(points: Point[], temp: number): number {
  if (points.length === 0) return 0;
  if (temp <= points[0][0]) return points[0][1];
  for (let i = 1; i < points.length; i++) {
    const [t1, p1] = points[i];
    if (temp <= t1) {
      const [t0, p0] = points[i - 1];
      const ratio = t1 === t0 ? 1 : (temp - t0) / (t1 - t0);
      return Math.round(p0 + ratio * (p1 - p0));
    }
  }
  return points[points.length - 1][1];
}

export function firstProblem(points: Point[], limits: Limits): string | null {
  if (points.length < limits.min_points || points.length > limits.max_points) {
    return `Use between ${limits.min_points} and ${limits.max_points} points.`;
  }
  for (let i = 1; i < points.length; i++) {
    if (points[i][0] <= points[i - 1][0]) return `Point ${i + 1} has to be hotter than point ${i}.`;
    if (points[i][1] < points[i - 1][1]) return `Point ${i + 1} can't be slower than point ${i}.`;
  }
  const reachesFull = points.some(([t, p]) => p === limits.pwm_max && t <= limits.full_speed_by_c);
  if (!reachesFull) return `The curve has to reach 100 % at ${limits.full_speed_by_c} °C or lower.`;
  return null;
}

export function withExtraPoint(points: Point[], limits: Limits): Point[] {
  if (points.length >= limits.max_points || points.length < 2) return points;
  const last = points[points.length - 1];
  const prev = points[points.length - 2];
  const temp = Math.round((prev[0] + last[0]) / 2);
  if (temp <= prev[0] || temp >= last[0]) return points;
  const pwm = Math.round((prev[1] + last[1]) / 2);
  return [...points.slice(0, -1), [temp, pwm], last];
}

export function withoutPoint(points: Point[], index: number, limits: Limits): Point[] {
  if (points.length <= limits.min_points) return points;
  return points.filter((_, i) => i !== index);
}

export const samePoints = (a: Point[], b: Point[]) =>
  a.length === b.length && a.every(([t, p], i) => t === b[i][0] && p === b[i][1]);
