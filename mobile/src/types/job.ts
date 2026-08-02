export type Job = {
  id: number;
  external_id?: string | null;
  title: string;
  company: string;
  company_logo?: string | null;
  description?: string;
  apply_url: string;
  category?: string | null;
  experience_level?: string | null;
  job_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  tags: string[];
  source?: string | null;
  is_remote: boolean;
  pakistan_friendly?: boolean;
  haunsla_score?: number | null;
  is_featured: boolean;
  posted_at?: string | null;
  created_at?: string | null;
};

export type JobsResponse = {
  items: Job[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
};

export type JobFilters = {
  q?: string;
  category?: string;
  experience?: string;
  job_type?: string;
  salary_min?: number;
  date_posted?: string;
};
