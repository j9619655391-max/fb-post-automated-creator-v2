import { apiPost } from './client';

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
