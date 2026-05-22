export interface ZoneDashboardRaw {
  dashboard_type: string;
  zone_id: string;
  zone_name: string;
  week_start: string;
  week_end: string;
  total_cells?: number;
  cells_reported?: number;
  submission_rate_percent?: number;
  total_attendance?: number;
  total_souls_won?: number;
  total_finances?: number;
  stats?: Partial<ZoneDashboardStats>;
  fellowships?: Partial<FellowshipCard>[];
  attendance_trend?: AttendanceTrendPoint[];
  submission_status?: SubmissionStatus;
}

export interface ZoneDashboardStats {
  total_fellowships: number;
  total_senior_cells: number;
  total_cells: number;
  total_attendance: number;
  total_souls_won: number;
  total_finances: number;
  submission_rate_percent: number;
  cells_reported: number;
}

export interface FellowshipCard {
  id: string;
  name: string;
  location?: string | null;
  zone_id?: string;
  senior_cells_count: number;
  cells_count: number;
  cells_reported: number;
  submission_rate: number;
  total_attendance: number;
  souls_won: number;
  pastor_name?: string;
  created_at?: string;
}

export interface AttendanceTrendPoint {
  week: string;
  active_members: number;
  first_timers: number;
}

export interface SubmissionStatus {
  on_time: number;
  late: number;
  not_submitted: number;
}

export interface ZoneDashboardResponse {
  dashboard_type: string;
  zone_id: string;
  zone_name: string;
  week_start: string;
  week_end: string;
  stats: ZoneDashboardStats;
  fellowships: FellowshipCard[];
  attendance_trend: AttendanceTrendPoint[];
  submission_status: SubmissionStatus;
}

export interface CreateFellowshipRequest {
  name: string;
  location?: string;
  zone_id: string;
}

export interface FellowshipResponse {
  id: string;
  name: string;
  location?: string | null;
  zone_id: string;
  created_at: string;
}

export interface SeniorCellResponse {
  id: string;
  name: string;
  fellowship_id: string;
  leader_name?: string | null;
  created_at: string;
}

export interface CellResponse {
  id: string;
  name: string;
  senior_cell_id: string;
  leader_name?: string | null;
  default_meeting_day?: string;
  meeting_time?: string | null;
  created_at: string;
}

export interface ZoneReport {
  id: string;
  cell_id: string;
  cell_name?: string | null;
  senior_cell_id?: string | null;
  senior_cell_name?: string | null;
  fellowship_id?: string | null;
  fellowship_name?: string | null;
  status: string;
  submitted_at: string | null;
  week_start_date: string;
  total_attendance: number;
  first_timers?: number;
  filled_holy_ghost?: number;
  new_members?: number;
  number_saved?: number;
  souls_won: number;
  finance_oblation?: number;
  finance_offerings?: number;
  finance_tithes?: number;
  finance_thanksgiving?: number;
  finance_seed?: number;
  finance_partnership?: number;
  finance_first_fruits?: number;
  finance_total: number;
}

export interface ReportsResponse {
  count: number;
  offset: number;
  limit: number;
  reports: ZoneReport[];
}

export interface ZoneUser {
  id: string;
  phone: string;
  name: string;
  role: string;
  zone_id: string | null;
  fellowship_id: string | null;
  senior_cell_id: string | null;
  cell_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SeniorCellSummary {
  id: string;
  name: string;
  leader_name?: string | null;
  total_cells: number;
  reports_submitted: number;
  total_attendance: number;
  total_first_timers: number;
  total_filled_holy_ghost: number;
  total_souls_won: number;
  total_finances: number;
  submission_rate: number;
  cells: Array<CellResponse & {
    reports_submitted: number;
    total_attendance: number;
    total_first_timers: number;
    total_filled_holy_ghost: number;
    total_souls_won: number;
    total_finances: number;
  }>;
}

export interface FellowshipSummary extends FellowshipCard {
  pastor_name?: string;
  pastor_phone?: string;
  reports_submitted: number;
  total_finances: number;
  total_first_timers: number;
  total_filled_holy_ghost: number;
  senior_cells: SeniorCellSummary[];
}

export interface ZoneExecutiveData {
  dashboard: ZoneDashboardResponse;
  fellowships: FellowshipSummary[];
  reports: ZoneReport[];
  users: ZoneUser[];
}
