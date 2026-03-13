/**
 * Installation mode: "main" (no welcome page, root = members) or "erebor" (welcome at /, at myip/erebor/).
 * Set VITE_BASE_PATH=/erebor/ when building the erebor deployment.
 */
const base = (import.meta.env.BASE_URL || "/").replace(/\/$/, "") || "/";
export const IS_EREBOR = base === "/erebor";
