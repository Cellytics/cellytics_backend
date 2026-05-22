import { apiClient } from '@/lib/api';
import type {
  CellResponse,
  CreateFellowshipRequest,
  FellowshipCard,
  FellowshipResponse,
  FellowshipSummary,
  ReportsResponse,
  SeniorCellResponse,
  SeniorCellSummary,
  ZoneDashboardRaw,
  ZoneDashboardResponse,
  ZoneExecutiveData,
  ZoneReport,
  ZoneUser,
} from '@/types/zone';

type FellowshipLike = Partial<FellowshipCard> & Partial<FellowshipResponse>;

const toNumber = (value: unknown): number => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

const normalizeFellowship = (fellowship: FellowshipLike): FellowshipCard => ({
  id: fellowship.id || '',
  name: fellowship.name || 'Unnamed Fellowship',
  location: fellowship.location || null,
  zone_id: fellowship.zone_id,
  senior_cells_count: toNumber(fellowship.senior_cells_count),
  cells_count: toNumber(fellowship.cells_count),
  cells_reported: toNumber(fellowship.cells_reported),
  submission_rate: toNumber(fellowship.submission_rate),
  total_attendance: toNumber(fellowship.total_attendance),
  souls_won: toNumber(fellowship.souls_won),
  pastor_name: fellowship.pastor_name,
  created_at: fellowship.created_at,
});

const normalizeDashboard = (
  dashboard: ZoneDashboardRaw,
  fellowships: FellowshipResponse[] = []
): ZoneDashboardResponse => {
  const dashboardFellowships = dashboard.fellowships?.map(normalizeFellowship) || [];
  const fellowshipCards = dashboardFellowships.length > 0
    ? dashboardFellowships
    : fellowships.map(normalizeFellowship);

  const stats = dashboard.stats || {};
  const totalCells = toNumber(stats.total_cells ?? dashboard.total_cells);
  const cellsReported = toNumber(stats.cells_reported ?? dashboard.cells_reported);
  const submissionRate = toNumber(stats.submission_rate_percent ?? dashboard.submission_rate_percent);

  return {
    dashboard_type: dashboard.dashboard_type,
    zone_id: dashboard.zone_id,
    zone_name: dashboard.zone_name,
    week_start: dashboard.week_start,
    week_end: dashboard.week_end,
    stats: {
      total_fellowships: toNumber(stats.total_fellowships) || fellowshipCards.length,
      total_senior_cells: toNumber(stats.total_senior_cells),
      total_cells: totalCells,
      total_attendance: toNumber(stats.total_attendance ?? dashboard.total_attendance),
      total_souls_won: toNumber(stats.total_souls_won ?? dashboard.total_souls_won),
      total_finances: toNumber(stats.total_finances ?? dashboard.total_finances),
      submission_rate_percent: submissionRate,
      cells_reported: cellsReported,
    },
    fellowships: fellowshipCards,
    attendance_trend: dashboard.attendance_trend || [],
    submission_status: dashboard.submission_status || {
      on_time: cellsReported,
      late: 0,
      not_submitted: Math.max(totalCells - cellsReported, 0),
    },
  };
};

export const zoneService = {
  getZoneDashboard: async (zoneId: string): Promise<ZoneDashboardResponse> => {
    const [dashboardResponse, fellowshipsResponse] = await Promise.all([
      apiClient.get<ZoneDashboardRaw>(`/api/dashboards/zone/${zoneId}`),
      apiClient.get<FellowshipResponse[]>('/api/admin/fellowships', {
        params: { zone_id: zoneId },
      }),
    ]);

    return normalizeDashboard(dashboardResponse.data, fellowshipsResponse.data);
  },

  createFellowship: async (data: CreateFellowshipRequest): Promise<FellowshipResponse> => {
    const response = await apiClient.post<FellowshipResponse>('/api/admin/fellowships', data);
    return response.data;
  },

  updateFellowship: async (
    fellowshipId: string,
    data: { name?: string; location?: string }
  ): Promise<FellowshipResponse> => {
    const response = await apiClient.patch<FellowshipResponse>(
      `/api/admin/fellowships/${fellowshipId}`,
      data
    );
    return response.data;
  },

  deleteFellowship: async (fellowshipId: string): Promise<void> => {
    await apiClient.delete(`/api/admin/fellowships/${fellowshipId}`);
  },

  getZoneFellowships: async (zoneId: string): Promise<FellowshipCard[]> => {
    const response = await apiClient.get<FellowshipResponse[]>('/api/admin/fellowships', {
      params: { zone_id: zoneId },
    });
    return response.data.map(normalizeFellowship);
  },

  getZoneReports: async (): Promise<ZoneReport[]> => {
    const response = await apiClient.get<ReportsResponse>('/api/reports');
    return response.data.reports || [];
  },

  getZoneUsers: async (zoneId: string): Promise<ZoneUser[]> => {
    const response = await apiClient.get<ZoneUser[]>('/api/admin/users', {
      params: { zone_id: zoneId },
    });
    return response.data;
  },

  getZoneExecutiveData: async (zoneId: string): Promise<ZoneExecutiveData> => {
    const [dashboardResponse, fellowshipsResponse, reportsResponse, usersResponse] = await Promise.all([
      apiClient.get<ZoneDashboardRaw>(`/api/dashboards/zone/${zoneId}`),
      apiClient.get<FellowshipResponse[]>('/api/admin/fellowships', {
        params: { zone_id: zoneId },
      }),
      apiClient.get<ReportsResponse>('/api/reports'),
      apiClient
        .get<ZoneUser[]>('/api/admin/users', { params: { zone_id: zoneId } })
        .catch(() => ({ data: [] as ZoneUser[] })),
    ]);

    const fellowships = fellowshipsResponse.data;
    const reports = reportsResponse.data.reports || [];
    const users = usersResponse.data;

    const seniorCellGroups = await Promise.all(
      fellowships.map(async (fellowship) => {
        const response = await apiClient.get<SeniorCellResponse[]>('/api/admin/senior-cells', {
          params: { fellowship_id: fellowship.id },
        });
        return { fellowshipId: fellowship.id, seniorCells: response.data };
      })
    );

    const allSeniorCells = seniorCellGroups.flatMap((group) => group.seniorCells);
    const cellGroups = await Promise.all(
      allSeniorCells.map(async (seniorCell) => {
        const response = await apiClient.get<CellResponse[]>('/api/admin/cells', {
          params: { senior_cell_id: seniorCell.id },
        });
        return { seniorCellId: seniorCell.id, cells: response.data };
      })
    );

    const cellsBySeniorCell = new Map<string, CellResponse[]>();
    cellGroups.forEach((group) => cellsBySeniorCell.set(group.seniorCellId, group.cells));

    const reportsByCell = new Map<string, ZoneReport[]>();
    reports.forEach((report) => {
      const existing = reportsByCell.get(report.cell_id) || [];
      existing.push(report);
      reportsByCell.set(report.cell_id, existing);
    });

    const summaries: FellowshipSummary[] = fellowships.map((fellowship) => {
      const seniorCells = seniorCellGroups.find((group) => group.fellowshipId === fellowship.id)?.seniorCells || [];
      const pastor = users.find(
        (user) => user.role === 'fellowship_pastor' && user.fellowship_id === fellowship.id
      );

      const seniorCellSummaries: SeniorCellSummary[] = seniorCells.map((seniorCell) => {
        const cells = cellsBySeniorCell.get(seniorCell.id) || [];
        const summarizedCells = cells.map((cell) => {
          const cellReports = reportsByCell.get(cell.id) || [];
          return {
            ...cell,
            reports_submitted: cellReports.length,
            total_attendance: cellReports.reduce((sum, report) => sum + toNumber(report.total_attendance), 0),
            total_first_timers: cellReports.reduce((sum, report) => sum + toNumber(report.first_timers), 0),
            total_filled_holy_ghost: cellReports.reduce((sum, report) => sum + toNumber(report.filled_holy_ghost), 0),
            total_souls_won: cellReports.reduce((sum, report) => sum + toNumber(report.souls_won), 0),
            total_finances: cellReports.reduce((sum, report) => sum + toNumber(report.finance_total), 0),
          };
        });

        const reportsSubmitted = summarizedCells.reduce((sum, cell) => sum + cell.reports_submitted, 0);
        const totalCells = summarizedCells.length;

        return {
          id: seniorCell.id,
          name: seniorCell.name,
          leader_name: seniorCell.leader_name,
          total_cells: totalCells,
          reports_submitted: reportsSubmitted,
          total_attendance: summarizedCells.reduce((sum, cell) => sum + cell.total_attendance, 0),
          total_first_timers: summarizedCells.reduce((sum, cell) => sum + cell.total_first_timers, 0),
          total_filled_holy_ghost: summarizedCells.reduce((sum, cell) => sum + cell.total_filled_holy_ghost, 0),
          total_souls_won: summarizedCells.reduce((sum, cell) => sum + cell.total_souls_won, 0),
          total_finances: summarizedCells.reduce((sum, cell) => sum + cell.total_finances, 0),
          submission_rate: totalCells > 0 ? Math.round((reportsSubmitted / totalCells) * 100) : 0,
          cells: summarizedCells,
        };
      });

      const cellsCount = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_cells, 0);
      const reportsSubmitted = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.reports_submitted, 0);
      const totalAttendance = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_attendance, 0);
      const totalFirstTimers = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_first_timers, 0);
      const totalFilledHolyGhost = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_filled_holy_ghost, 0);
      const totalSoulsWon = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_souls_won, 0);
      const totalFinances = seniorCellSummaries.reduce((sum, seniorCell) => sum + seniorCell.total_finances, 0);

      return {
        ...normalizeFellowship(fellowship),
        pastor_name: pastor?.name,
        pastor_phone: pastor?.phone,
        senior_cells_count: seniorCellSummaries.length,
        cells_count: cellsCount,
        cells_reported: reportsSubmitted,
        reports_submitted: reportsSubmitted,
        submission_rate: cellsCount > 0 ? Math.round((reportsSubmitted / cellsCount) * 100) : 0,
        total_attendance: totalAttendance,
        souls_won: totalSoulsWon,
        total_finances: totalFinances,
        total_first_timers: totalFirstTimers,
        total_filled_holy_ghost: totalFilledHolyGhost,
        senior_cells: seniorCellSummaries,
      };
    });

    const dashboard = normalizeDashboard(dashboardResponse.data, fellowships);
    dashboard.fellowships = summaries;
    dashboard.stats.total_fellowships = summaries.length;
    dashboard.stats.total_senior_cells = summaries.reduce((sum, fellowship) => sum + fellowship.senior_cells_count, 0);

    return {
      dashboard,
      fellowships: summaries,
      reports,
      users,
    };
  },
};
