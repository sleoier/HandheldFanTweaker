export const PROFILE_LABELS: Record<string, string> = {
  silent: "Silent",
  balanced: "Balanced",
  turbo: "Turbo",
};

export const profileLabel = (profile: string) => PROFILE_LABELS[profile] ?? profile;

const UNDERCLOCK_LABELS: Record<string, string> = { off: "Off", low: "Low", medium: "Medium", high: "High" };

const UNDERCLOCK_HINTS: Record<string, string> = {
  off: "Stock clocks.",
  low: "Trims the least efficient top clocks. Barely noticeable in games.",
  medium: "Cooler and longer battery; fine for most emulation.",
  high: "Biggest savings; demanding games may lose frames.",
};

export const underclockLabel = (level: string) => UNDERCLOCK_LABELS[level] ?? level;
export const underclockHint = (level: string) => UNDERCLOCK_HINTS[level] ?? "";
