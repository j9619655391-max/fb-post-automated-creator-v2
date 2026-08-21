import { apiGet, apiPost } from './client';

export interface GeneratedDraft {

  id: number;
  title: string;
  body: string;
  status: string;
  organization_id?: number | null;
  generated_by_ai: boolean;
  generation_job_id?: number | null;
  media_id?: number | null;
}

export interface GenerateDraftRequest {
  category_id?: number;
  category_name?: string;
  extra_instruction?: string;
  organization_id?: number;
  idempotency_key?: string;
}

export function generateDraft(data: GenerateDraftRequest): Promise<GeneratedDraft> {
  return apiPost<GeneratedDraft>('generation/draft', data);
}


export interface AIProviderStatus {
  provider: string;
  model: string | null;
  configured: boolean;
  free_model: boolean;
  fallback_enabled: boolean;
  error?: string;
}

export function getAIProviderStatus(): Promise<AIProviderStatus> {
  return apiGet<AIProviderStatus>('generation/provider');
}


export interface AIProviderHealth {
  provider: string;
  model: string | null;
  configured: boolean;
  fallback_enabled: boolean;
  window_minutes: number;
  failed_jobs: number;
  retrying_plans: number;
  alert: boolean;
  alert_reason: string | null;
  latest_failure: {
    job_id: number;
    provider: string | null;
    model: string | null;
    error_code: string | null;
    completed_at: string | null;
  } | null;
  checked_at: string;
}

export function getAIProviderHealth(): Promise<AIProviderHealth> {
  return apiGet<AIProviderHealth>('generation/health');
}
