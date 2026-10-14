import { ButtonItem, PanelSectionRow, SliderField } from "@decky/ui";
import type { Limits, Point } from "../types";
import { percentToPwm, pwmToPercent } from "../curve";

interface Props {
  index: number;
  point: Point;
  limits: Limits;
  canRemove: boolean;
  onChange: (point: Point) => void;
  onRemove: () => void;
}

export function PointEditor({ index, point, limits, canRemove, onChange, onRemove }: Props) {
  const [temp, pwm] = point;
  return (
    <>
      <PanelSectionRow>
        <SliderField
          label={`Point ${index + 1}: temperature`}
          description={`${temp} °C`}
          value={temp}
          min={limits.temp_min_c}
          max={limits.temp_max_c}
          step={1}
          onChange={(value: number) => onChange([value, pwm])}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={`Point ${index + 1}: fan speed`}
          description={`${pwmToPercent(pwm, limits.pwm_max)} % (PWM ${pwm})`}
          value={pwmToPercent(pwm, limits.pwm_max)}
          min={0}
          max={100}
          step={1}
          onChange={(value: number) => onChange([temp, percentToPwm(value, limits.pwm_max)])}
        />
      </PanelSectionRow>
      {canRemove && (
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={onRemove}>
            Remove point {index + 1}
          </ButtonItem>
        </PanelSectionRow>
      )}
    </>
  );
}
