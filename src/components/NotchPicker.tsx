import { SliderField } from "@decky/ui";

interface Props {
  label: string;
  options: string[];
  selected: string | null;
  labelFor: (option: string) => string;
  description?: string;
  disabled?: boolean;
  onSelect: (option: string) => void;
}

export function NotchPicker({ label, options, selected, labelFor, description, disabled, onSelect }: Props) {
  const index = Math.max(0, selected ? options.indexOf(selected) : 0);
  return (
    <SliderField
      label={label}
      description={description ?? (selected ? labelFor(selected) : undefined)}
      value={index}
      min={0}
      max={Math.max(options.length - 1, 0)}
      step={1}
      notchCount={options.length}
      notchLabels={options.map((o, i) => ({ notchIndex: i, label: labelFor(o) }))}
      notchTicksVisible
      disabled={disabled}
      onChange={(value: number) => {
        const next = options[value];
        if (next && next !== selected) onSelect(next);
      }}
    />
  );
}
