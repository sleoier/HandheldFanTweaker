import { toaster } from "@decky/api";
import { Field, PanelSection, PanelSectionRow } from "@decky/ui";
import { useEffect, useState } from "react";

import { getUnderclock, setUnderclock } from "../api";
import { underclockHint, underclockLabel } from "../labels";
import type { UnderclockState } from "../types";
import { NotchPicker } from "./NotchPicker";

const mhz = (khz: number | null) => (khz == null ? "?" : `${Math.round(khz / 1000)} MHz`);

export function UnderclockSection() {
  const [state, setState] = useState<UnderclockState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getUnderclock().then((res) => (res.ok ? setState(res.value) : setError(res.error)));
  }, []);

  if (error) {
    return (
      <PanelSection title="CPU underclock">
        <PanelSectionRow>
          <Field label="Couldn't read the CPU clusters" description={error} />
        </PanelSectionRow>
      </PanelSection>
    );
  }
  if (!state || state.clusters.length === 0) return null;

  const choose = async (level: string) => {
    setBusy(true);
    const res = await setUnderclock(level);
    setBusy(false);
    if (!res.ok) {
      toaster.toast({ title: "Underclock not applied", body: res.error });
      return;
    }
    setState(res.value);
    toaster.toast({ title: `Underclock: ${underclockLabel(level)}`, body: underclockHint(level) });
  };

  return (
    <PanelSection title="CPU underclock">
      <PanelSectionRow>
        <NotchPicker
          label="Level"
          options={state.levels}
          selected={state.level}
          labelFor={underclockLabel}
          description={underclockHint(state.level)}
          disabled={busy}
          onSelect={choose}
        />
      </PanelSectionRow>
      {state.clusters.map((c) => (
        <PanelSectionRow key={c.name}>
          <Field
            label={`Cores ${c.cpus.split(" ").join(", ")}`}
            description={`Max ${mhz(c.current_max_khz)} of ${mhz(c.max_khz)}`}
          />
        </PanelSectionRow>
      ))}
    </PanelSection>
  );
}
