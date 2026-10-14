export type Point = [temp_c: number, pwm: number];

export interface Telemetry {
  curve_temp_c: number | null;
  hottest_c: number | null;
  fan_pwm: number | null;
  fan_rpm: number | null;
}

export interface Limits {
  pwm_max: number;
  min_points: number;
  max_points: number;
  temp_min_c: number;
  temp_max_c: number;
  full_speed_by_c: number;
}

export interface PluginState {
  backend: string | null;
  editable: boolean;
  reason: string | null;
  profile_order: string[];
  profiles: Record<string, Point[]>;
  factory: Record<string, Point[]>;
  active_profile: string | null;
  telemetry: Telemetry;
  limits: Limits;
}

export type Result<T> = { ok: true; value: T } | { ok: false; error: string };
