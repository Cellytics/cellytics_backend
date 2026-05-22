/**
 * DASHBOARD TYPES
 * 
 * These will be extended as we build each dashboard.
 * For now, we define the basic structure.
 */

export interface DashboardStats {
  totalMembers: number;
  activeMembers: number;
  meetings: number;
  growth: number;
}

export interface DashboardResponse {
  stats: DashboardStats;
  // We'll add more as we build each dashboard
}
