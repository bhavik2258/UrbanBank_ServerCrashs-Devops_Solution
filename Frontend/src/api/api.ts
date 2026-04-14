// Centralized API layer for UrbanBank backend integration.

export interface BranchMetrics {
  cpu: number;
  ram: number;
  disk: number;
}

export interface ServiceStatus {
  name: string;
  status: "UP" | "DOWN";
}

export interface Branch {
  id: string;
  name: string;
  bank_name: string;
  location: string;
  status: "healthy" | "warning" | "critical";
  metrics: BranchMetrics;
  services: ServiceStatus[];
  uptimePercent: number;
}

export interface Alert {
  id: string;
  branchId: string;
  branchName: string;
  type: string;
  severity: "critical" | "warning" | "info";
  message: string;
  firedAt: string;
  resolved: boolean;
}

export interface Incident {
  id: string;
  branchId: string;
  branchName: string;
  description: string;
  autoHealed: boolean;
  healAction: string;
  duration: string;
  startTime: string;
  endTime: string;
}

export interface MetricReading {
  timestamp: string;
  cpu: number;
  ram: number;
  disk: number;
}

type BackendBranchStatus = "healthy" | "warning" | "critical";

interface BackendMetric {
  id: number;
  branch_id: number;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  core_banking_service_up: boolean;
  postgres_db_up: boolean;
  network_up: boolean;
  recorded_at: string;
}

interface BackendBranch {
  id: number;
  name: string;
  bank_name: string;
  ip_address: string;
  location: string;
  status: BackendBranchStatus;
  created_at: string;
  uptime_percent: number;
  latest_metric: BackendMetric | null;
}

interface BackendAlert {
  id: number;
  branch_id: number;
  alert_type: string;
  message: string;
  severity: "critical" | "warning" | "info";
  is_resolved: boolean;
  fired_at: string;
  resolved_at: string | null;
}

interface BackendIncident {
  id: number;
  branch_id: number;
  alert_id: number | null;
  description: string;
  auto_healed: boolean;
  heal_action: string;
  started_at: string;
  resolved_at: string | null;
  duration_minutes: number | null;
}

interface BackendIncidentPage {
  items: BackendIncident[];
  total: number;
  page: number;
  page_size: number;
}

interface BackendDashboardSummary {
  total_branches: number;
  active_alerts: number;
  incidents_today: number;
  avg_uptime_percent: number;
}

interface DashboardStreamCallbacks {
  onConnected?: () => void;
  onMetricsUpdated?: () => void;
  onDisconnected?: () => void;
  onError?: (event: Event) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status} ${response.statusText}: ${text}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function normalizeType(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatDuration(durationMinutes: number | null, resolvedAt: string | null): string {
  if (durationMinutes == null) {
    return resolvedAt ? "resolved" : "ongoing";
  }
  const totalSeconds = Math.max(0, Math.round(durationMinutes * 60));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

async function getBranchNameMap(): Promise<Map<number, string>> {
  const branches = await request<BackendBranch[]>("/branches");
  return new Map<number, string>(branches.map((branch) => [branch.id, branch.name]));
}

function mapBranch(branch: BackendBranch): Branch {
  const metric = branch.latest_metric;
  return {
    id: String(branch.id),
    name: branch.name,
    bank_name: branch.bank_name,
    location: branch.location,
    status: branch.status,
    metrics: {
      cpu: metric?.cpu_usage ?? 0,
      ram: metric?.ram_usage ?? 0,
      disk: metric?.disk_usage ?? 0,
    },
    services: [
      {
        name: "core-banking-svc",
        status: metric?.core_banking_service_up === false ? "DOWN" : "UP",
      },
      {
        name: "postgres-db",
        status: metric?.postgres_db_up === false ? "DOWN" : "UP",
      },
    ],
    uptimePercent: Number((branch.uptime_percent ?? 100).toFixed(2)),
  };
}

function mapAlert(alert: BackendAlert, branchName: string): Alert {
  return {
    id: String(alert.id),
    branchId: String(alert.branch_id),
    branchName,
    type: normalizeType(alert.alert_type),
    severity: alert.severity,
    message: alert.message,
    firedAt: alert.fired_at,
    resolved: alert.is_resolved,
  };
}

function mapIncident(incident: BackendIncident, branchName: string): Incident {
  return {
    id: String(incident.id),
    branchId: String(incident.branch_id),
    branchName,
    description: incident.description,
    autoHealed: incident.auto_healed,
    healAction: incident.heal_action,
    duration: formatDuration(incident.duration_minutes, incident.resolved_at),
    startTime: incident.started_at,
    endTime: incident.resolved_at ?? "",
  };
}

function toBranchId(value: string): number {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    throw new Error(`Invalid branch id: ${value}`);
  }
  return parsed;
}

export const fetchBranches = async (): Promise<Branch[]> => {
  const backendBranches = await request<BackendBranch[]>("/branches");
  return backendBranches.map((branch) => mapBranch(branch));
};

export const fetchBranch = async (id: string): Promise<Branch | undefined> => {
  const branchId = toBranchId(id);
  try {
    const backendBranch = await request<BackendBranch>(`/branches/${branchId}`);
    return mapBranch(backendBranch);
  } catch (error) {
    if (error instanceof Error && error.message.includes("404")) {
      return undefined;
    }
    throw error;
  }
};

export const fetchMetricHistory = async (branchId: string): Promise<MetricReading[]> => {
  const id = toBranchId(branchId);
  const metrics = await request<BackendMetric[]>(`/metrics/${id}/history`);
  return metrics.map((metric) => ({
    timestamp: metric.recorded_at,
    cpu: metric.cpu_usage,
    ram: metric.ram_usage,
    disk: metric.disk_usage,
  }));
};

export const fetchAlerts = async (): Promise<Alert[]> => {
  const [alerts, branchNameMap] = await Promise.all([
    request<BackendAlert[]>("/alerts?limit=500"),
    getBranchNameMap(),
  ]);
  return alerts.map((alert) => mapAlert(alert, branchNameMap.get(alert.branch_id) ?? `Branch ${alert.branch_id}`));
};

export const fetchAlertsByBranch = async (branchId: string): Promise<Alert[]> => {
  const id = toBranchId(branchId);
  const [alerts, branchDetails] = await Promise.all([
    request<BackendAlert[]>(`/alerts?branch_id=${id}&limit=200`),
    request<BackendBranch>(`/branches/${id}`),
  ]);
  return alerts.map((alert) => mapAlert(alert, branchDetails.name));
};

export const resolveAlert = async (alertId: string): Promise<void> => {
  const id = Number.parseInt(alertId, 10);
  if (Number.isNaN(id)) {
    throw new Error(`Invalid alert id: ${alertId}`);
  }
  await request(`/alerts/${id}/resolve`, { method: "PATCH" });
};

export const fetchIncidents = async (): Promise<Incident[]> => {
  const [incidentResponse, branchNameMap] = await Promise.all([
    request<BackendIncidentPage | BackendIncident[]>("/incidents?page=1&page_size=100"),
    getBranchNameMap(),
  ]);
  const incidents = Array.isArray(incidentResponse) ? incidentResponse : incidentResponse.items;
  return incidents.map((incident) =>
    mapIncident(incident, branchNameMap.get(incident.branch_id) ?? `Branch ${incident.branch_id}`)
  );
};

export const fetchIncidentsByBranch = async (branchId: string): Promise<Incident[]> => {
  const id = toBranchId(branchId);
  const [incidents, branchDetails] = await Promise.all([
    request<BackendIncident[]>(`/incidents/${id}`),
    request<BackendBranch>(`/branches/${id}`),
  ]);
  return incidents.map((incident) => mapIncident(incident, branchDetails.name));
};

export const simulateFailure = async (branchId: string): Promise<void> => {
  const id = toBranchId(branchId);
  await request(`/simulate/incident/${id}`, { method: "POST" });
};

export const triggerHeal = async (branchId: string): Promise<void> => {
  const id = toBranchId(branchId);
  await request(`/simulate/heal/${id}`, { method: "POST" });
};

export const subscribeDashboardUpdates = (callbacks: DashboardStreamCallbacks): (() => void) => {
  const source = new EventSource(`${API_BASE_URL}/dashboard/stream`);
  let closedByClient = false;

  source.addEventListener("connected", () => {
    callbacks.onConnected?.();
  });

  source.addEventListener("metrics_updated", () => {
    callbacks.onMetricsUpdated?.();
  });

  source.onerror = (event) => {
    callbacks.onError?.(event);
    if (!closedByClient) {
      callbacks.onDisconnected?.();
    }
  };

  return () => {
    closedByClient = true;
    source.close();
    callbacks.onDisconnected?.();
  };
};

export const getDashboardSummary = async () => {
  const summary = await request<BackendDashboardSummary>("/dashboard/summary");
  return {
    totalBranches: summary.total_branches,
    activeAlerts: summary.active_alerts,
    incidentsToday: summary.incidents_today,
    avgUptime: summary.avg_uptime_percent,
  };
};
