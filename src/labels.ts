export const PROFILE_LABELS: Record<string, string> = {
  silent: "Silent",
  balanced: "Balanced",
  turbo: "Turbo",
};

export const profileLabel = (profile: string) => PROFILE_LABELS[profile] ?? profile;
