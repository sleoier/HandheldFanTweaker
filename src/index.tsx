import { definePlugin, toaster } from "@decky/api";
import { ButtonItem, Field, PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getState, getTelemetry, resetCurve, setCurve } from "./api";
import { CurveChart } from "./components/CurveChart";
import { NotchPicker } from "./components/NotchPicker";
import { PointEditor } from "./components/PointEditor";
import { UnderclockSection } from "./components/UnderclockSection";
import { firstProblem, pwmToPercent, samePoints, withExtraPoint, withoutPoint } from "./curve";
import { profileLabel } from "./labels";
import type { PluginState, Point, Telemetry } from "./types";

const TELEMETRY_EVERY_MS = 2000;

function Content() {
  const [state, setState] = useState<PluginState | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [profile, setProfile] = useState<string | null>(null);
  const [draft, setDraft] = useState<Point[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (keepProfile?: string | null) => {
    const res = await getState();
    if (!res.ok) {
      setLoadError(res.error);
      return;
    }
    const s = res.value;
    setState(s);
    setTelemetry(s.telemetry);
    const chosen = keepProfile ?? s.active_profile ?? s.profile_order.find((p) => s.profiles[p]) ?? null;
    setProfile(chosen);
    setDraft(chosen ? s.profiles[chosen] ?? [] : []);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const timer = setInterval(async () => {
      const res = await getTelemetry();
      if (res.ok) setTelemetry(res.value);
    }, TELEMETRY_EVERY_MS);
    return () => clearInterval(timer);
  }, []);

  const saved = useMemo(() => (state && profile ? state.profiles[profile] ?? [] : []), [state, profile]);
  const dirty = !samePoints(draft, saved);
  const problem = state ? firstProblem(draft, state.limits) : null;

  if (loadError) {
    return (
      <PanelSection title="HandheldFanTweaker">
        <PanelSectionRow>
          <Field label="Couldn't read the fan state" description={loadError} />
        </PanelSectionRow>
      </PanelSection>
    );
  }
  if (!state) {
    return (
      <PanelSection>
        <PanelSectionRow>
          <Field label="Loading…" />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  const apply = async () => {
    if (!profile || problem) return;
    setBusy(true);
    const res = await setCurve(profile, draft);
    setBusy(false);
    if (!res.ok) {
      toaster.toast({ title: "Curve not applied", body: res.error });
      return;
    }
    toaster.toast({ title: "Curve applied", body: `${profileLabel(profile)} profile` });
    await load(profile);
  };

  const restore = async () => {
    if (!profile) return;
    setBusy(true);
    const res = await resetCurve(profile);
    setBusy(false);
    if (!res.ok) {
      toaster.toast({ title: "Couldn't restore the curve", body: res.error });
      return;
    }
    toaster.toast({ title: "Original curve restored", body: `${profileLabel(profile)} profile` });
    await load(profile);
  };

  const temp = telemetry?.curve_temp_c ?? null;
  const fanPct = telemetry?.fan_pwm != null ? pwmToPercent(telemetry.fan_pwm, state.limits.pwm_max) : null;
  const factory = profile ? state.factory[profile] : undefined;

  return (
    <>
      <PanelSection title="Now">
        <PanelSectionRow>
          <Field
            label="Curve temperature"
            description={temp != null ? `${temp} °C (hottest ${telemetry?.hottest_c ?? "?"} °C)` : "No reading"}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <Field
            label="Fan"
            description={fanPct != null ? `${fanPct} %${telemetry?.fan_rpm ? ` · ${telemetry.fan_rpm} RPM` : ""}` : "No reading"}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <Field label="Active profile" description={state.active_profile ? profileLabel(state.active_profile) : "Unknown"} />
        </PanelSectionRow>
      </PanelSection>

      <UnderclockSection />

      {!state.editable ? (
        <PanelSection title="Curves">
          <PanelSectionRow>
            <Field label="Editing isn't available on this device" description={state.reason ?? ""} />
          </PanelSectionRow>
        </PanelSection>
      ) : (
        <PanelSection title="Curves">
          <PanelSectionRow>
            <NotchPicker
              label="Profile to edit"
              options={state.profile_order}
              selected={profile}
              labelFor={profileLabel}
              onSelect={(p) => {
                setProfile(p);
                setDraft(state.profiles[p] ?? []);
              }}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <CurveChart points={draft} saved={dirty ? saved : undefined} limits={state.limits} currentTemp={temp} />
          </PanelSectionRow>
          {problem && (
            <PanelSectionRow>
              <Field label="Check the curve" description={problem} />
            </PanelSectionRow>
          )}
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy || !dirty || !!problem} onClick={apply}>
              Apply
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy || !dirty} onClick={() => setDraft(saved)}>
              Discard changes
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={busy || !factory || samePoints(saved, factory)} onClick={restore}>
              Restore original curve
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )}

      {state.editable && profile && (
        <PanelSection title="Points">
          {draft.map((point, i) => (
            <PointEditor
              key={i}
              index={i}
              point={point}
              limits={state.limits}
              canRemove={draft.length > state.limits.min_points}
              onChange={(next) => setDraft(draft.map((p, j) => (j === i ? next : p)))}
              onRemove={() => setDraft(withoutPoint(draft, i, state.limits))}
            />
          ))}
          {draft.length < state.limits.max_points && (
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={() => setDraft(withExtraPoint(draft, state.limits))}>
                Add point
              </ButtonItem>
            </PanelSectionRow>
          )}
        </PanelSection>
      )}
    </>
  );
}

function FanIcon() {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true">
      <circle cx="12" cy="12" r="2" />
      <path d="M12 3c2.5 0 3.5 2.2 2.6 4.4L13.5 10h-3L9.6 7C8.9 4.9 9.8 3 12 3zm9 9c0 2.5-2.2 3.5-4.4 2.6L14 13.5v-3l3-.9c2.1-.7 4 .2 4 2.4zM12 21c-2.5 0-3.5-2.2-2.6-4.4l1.1-2.6h3l.9 3c.7 2.1-.2 4-2.4 4zM3 12c0-2.5 2.2-3.5 4.4-2.6l2.6 1.1v3l-3 .9C4.9 15.1 3 14.2 3 12z" />
    </svg>
  );
}

export default definePlugin(() => ({
  name: "HandheldFanTweaker",
  titleView: <div className={staticClasses.Title}>HandheldFanTweaker</div>,
  content: <Content />,
  icon: <FanIcon />,
}));
