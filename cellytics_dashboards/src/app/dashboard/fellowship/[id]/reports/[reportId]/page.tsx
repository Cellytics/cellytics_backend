'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ErrorAlert } from '@/components/ErrorAlert';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/Button';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { AUTH_TOKEN_KEY } from '@/utils/constants';
import { SuccessAlert } from '@/components/SuccessAlert';

interface CellReport {
  id: string;
  cell_id: string;
  cell_name: string;
  meeting_date: string;
  week_start_date: string;
  status: string;
  total_attendance: number;
  first_timers: number;
  souls_won: number;
  new_members: number;
  finance_total: number;
  finance_offerings: number;
  finance_tithes: number;
  finance_seed: number;
  testimonies: string;
  challenges: string;
  submitted_by: string;
  submitted_at: string;
  pastors_remarks: string;
}

const formatNumber = (value: number) => value.toLocaleString();
const formatMoney = (value: number) => `XAF ${Math.round(value).toLocaleString()}`;

export default function CellReportDetailPage() {
  const { isLoading: authLoading } = useAuth();
  const params = useParams();
  const fellowshipId = params?.id as string;
  const reportId = params?.reportId as string;

  const [report, setReport] = useState<CellReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [remarks, setRemarks] = useState('');

  useEffect(() => {
    if (!reportId) return;

    const loadReport = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // This would call an endpoint to get the report
        // For now, we'll show the structure
        setReport(null);
        setError('Report not found');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report');
      } finally {
        setIsLoading(false);
      }
    };

    loadReport();
  }, [reportId]);

  const handleAddComment = async () => {
    if (!comment.trim() || !reportId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/reports/${reportId}/comments`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY)}`,
          },
          body: JSON.stringify({
            comment: comment.trim(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add comment');
      }

      setComment('');
      setSuccessMessage('Comment added successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add comment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleValidateReport = async () => {
    if (!reportId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/reports/${reportId}/validate`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            remarks: remarks.trim(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to validate report');
      }

      setSuccessMessage('Report validated successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate report');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="p-5">
        <ErrorAlert message={error} />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-5">
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
          <p className="text-slate-500">Report not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto w-full max-w-[1200px] px-4 py-5 sm:px-6 lg:px-7">
        {successMessage && <SuccessAlert message={successMessage} onClose={() => setSuccessMessage(null)} />}
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

        <div className="mb-5">
          <Link href={`/dashboard/fellowship/${fellowshipId}/cells`}>
            <Button variant="secondary" className="mb-4">← Back to Cells</Button>
          </Link>
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h1 className="font-serif text-2xl font-bold text-navy">{report.cell_name}</h1>
            <p className="mt-1 text-slate-500">
              Week of {new Date(report.week_start_date).toLocaleDateString()}
            </p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-5">
            {/* Report Status */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="font-serif text-base font-bold text-navy">Report Status</h2>
                <span className={`rounded-full px-4 py-2 font-bold ${
                  report.status === 'submitted' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {report.status.toUpperCase()}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Submitted by {report.submitted_by} on {new Date(report.submitted_at).toLocaleString()}
              </p>
            </div>

            {/* Report Metrics */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 font-serif text-base font-bold text-navy">Meeting Metrics</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs text-slate-500">Total Attendance</p>
                  <p className="mt-1 text-2xl font-bold text-navy">{formatNumber(report.total_attendance)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">First Timers</p>
                  <p className="mt-1 text-2xl font-bold text-navy">{formatNumber(report.first_timers)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Souls Won</p>
                  <p className="mt-1 text-2xl font-bold text-navy">{formatNumber(report.souls_won)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">New Members</p>
                  <p className="mt-1 text-2xl font-bold text-navy">{formatNumber(report.new_members)}</p>
                </div>
              </div>
            </div>

            {/* Finances */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 font-serif text-base font-bold text-navy">Finances</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                  <p className="text-slate-600">Offerings</p>
                  <p className="font-semibold text-navy">{formatMoney(report.finance_offerings)}</p>
                </div>
                <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                  <p className="text-slate-600">Tithes</p>
                  <p className="font-semibold text-navy">{formatMoney(report.finance_tithes)}</p>
                </div>
                <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                  <p className="text-slate-600">Seed</p>
                  <p className="font-semibold text-navy">{formatMoney(report.finance_seed)}</p>
                </div>
                <div className="flex items-center justify-between pt-3 bg-slate-50 px-3 py-2 rounded">
                  <p className="font-semibold text-slate-700">Total</p>
                  <p className="text-lg font-bold text-navy">{formatMoney(report.finance_total)}</p>
                </div>
              </div>
            </div>

            {/* Testimonies & Challenges */}
            {(report.testimonies || report.challenges) && (
              <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 font-serif text-base font-bold text-navy">Notes</h2>
                {report.testimonies && (
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-slate-500 uppercase">Testimonies</p>
                    <p className="mt-2 text-slate-700">{report.testimonies}</p>
                  </div>
                )}
                {report.challenges && (
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase">Challenges</p>
                    <p className="mt-2 text-slate-700">{report.challenges}</p>
                  </div>
                )}
              </div>
            )}

            {/* Comments Section */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 font-serif text-base font-bold text-navy">Comments</h2>
              <div className="mb-4 space-y-3">
                {/* Comments would be listed here */}
                <p className="text-sm text-slate-500">No comments yet</p>
              </div>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment..."
                className="w-full rounded-lg border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gold"
                rows={3}
              />
              <Button
                onClick={handleAddComment}
                disabled={isSubmitting}
                className="mt-3 w-full"
              >
                Add Comment
              </Button>
            </div>
          </div>

          {/* Sidebar - Validation */}
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm h-fit sticky top-5">
            <h2 className="mb-4 font-serif text-base font-bold text-navy">Validation</h2>
            <div className="mb-4 space-y-3">
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add validation remarks..."
                className="w-full rounded-lg border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-gold"
                rows={4}
              />
            </div>
            <Button
              onClick={handleValidateReport}
              disabled={isSubmitting}
              className="w-full mb-3"
            >
              Validate Report
            </Button>
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => {
                // Implement ping functionality
              }}
            >
              Send Message to Leader
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
