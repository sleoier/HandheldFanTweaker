import { callable } from "@decky/api";
import type { PluginState, Point, Result, Telemetry } from "./types";

export const getState = callable<[], Result<PluginState>>("get_state");
export const getTelemetry = callable<[], Result<Telemetry>>("get_telemetry");
export const setCurve = callable<[profile: string, points: Point[]], Result<Point[]>>("set_curve");
export const resetCurve = callable<[profile: string], Result<Point[]>>("reset_curve");
