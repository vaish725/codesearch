export type HealthResponse = {
  status: "ok" | "error";
  timestamp: string;
};

export function getHealthRoute(): string {
  return "/api/health";
}

export function getAuthRoute(): string {
  return "/api/auth/login";
}
