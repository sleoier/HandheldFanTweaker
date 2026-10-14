import { SliderField } from "@decky/ui";
import { profileLabel } from "../labels";

interface Props {
  profiles: string[];
  selected: string | null;
  onSelect: (profile: string) => void;
}

export function ProfilePicker({ profiles, selected, onSelect }: Props) {
  const index = Math.max(0, selected ? profiles.indexOf(selected) : 0);
  return (
    <SliderField
      label="Profile to edit"
      description={selected ? profileLabel(selected) : undefined}
      value={index}
      min={0}
      max={Math.max(profiles.length - 1, 0)}
      step={1}
      notchCount={profiles.length}
      notchLabels={profiles.map((p, i) => ({ notchIndex: i, label: profileLabel(p) }))}
      notchTicksVisible
      onChange={(value: number) => {
        const next = profiles[value];
        if (next && next !== selected) onSelect(next);
      }}
    />
  );
}
