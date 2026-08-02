import type { Job, JobFilters, JobsResponse } from '../types/job';

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:5000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed: ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

function toQuery(params: Record<string, string | number | undefined>) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      q.set(key, String(value));
    }
  });
  const str = q.toString();
  return str ? `?${str}` : '';
}

export const api = {
  getJobs: (page = 1, filters: JobFilters = {}) =>
    request<JobsResponse>(
      `/api/jobs${toQuery({ page, per_page: 20, ...filters })}`,
    ),

  getJob: (id: number) => request<Job>(`/api/jobs/${id}`),

  getFilterMeta: () =>
    request<{
      categories: string[];
      experience_levels: string[];
      job_types: string[];
      date_posted: string[];
    }>('/api/jobs/meta/filters'),
};
