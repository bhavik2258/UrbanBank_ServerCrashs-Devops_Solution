export type UserRole = "platform_admin" | "operations_analyst" | "auditor";

export type Permission =
  | "simulate_incident"
  | "trigger_heal"
  | "resolve_alert"
  | "export_incidents"
  | "manage_account"
  | "manage_kubernetes";

export interface AuthSession {
  name: string;
  email: string;
  role: UserRole;
  roleLabel: string;
  accessToken: string;
}

export const AUTH_SESSION_KEY = "urbanbank.auth";

const ROLE_LABELS: Record<UserRole, string> = {
  platform_admin: "Platform Admin",
  operations_analyst: "Operations Analyst",
  auditor: "Read-Only Auditor",
};

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  platform_admin: ["simulate_incident", "trigger_heal", "resolve_alert", "export_incidents", "manage_account", "manage_kubernetes"],
  operations_analyst: ["simulate_incident", "trigger_heal", "resolve_alert", "export_incidents", "manage_account"],
  auditor: [],
};

export function getRoleLabel(role: UserRole): string {
  return ROLE_LABELS[role];
}

export function getSession(): AuthSession | null {
  const raw = sessionStorage.getItem(AUTH_SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed?.email || !parsed?.role) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function setSession(user: { name: string; email: string; role: UserRole; accessToken: string }): AuthSession {
  const session: AuthSession = {
    name: user.name,
    email: user.email,
    role: user.role,
    roleLabel: getRoleLabel(user.role),
    accessToken: user.accessToken,
  };

  sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session));
  return session;
}

export function clearSession(): void {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}

export function isAuthenticated(): boolean {
  return getSession()?.accessToken !== undefined;
}

export function getAccessToken(): string | null {
  return getSession()?.accessToken ?? null;
}

export function hasPermission(permission: Permission): boolean {
  const session = getSession();
  if (!session) {
    return false;
  }

  return ROLE_PERMISSIONS[session.role].includes(permission);
}
