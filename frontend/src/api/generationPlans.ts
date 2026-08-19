import { apiGet, apiPost } from './client';

export type GenerationPlanStatus = 'active' | 'paused';
export type GenerationRecurrence = 'daily' | 'weekly';

export interface GenerationPlan {
  id: number;
  name: string;
  organization_id?: number | null;
  created_by_id: number;
  category_id?: number | null;
  category_name?: string | null;
  recurrence: GenerationRecurrence;
  approval_mode: 'required' | 'controlled';
  status: GenerationPlanStatus;
  next_run_at: string;
  last_run_at?: string | null;
  active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface GenerationPlanCreate {
  name: string;
  category_name?: string;
  extra_instruction?: string;
  organization_id?: number;
  recurrence: GenerationRecurrence;
  approval_mode: 'required' | 'controlled';
  next_run_at: string;
}

export function listGenerationPlans(): Promise<GenerationPlan[]> {
  return apiGet<GenerationPlan[]>('generation-plans/');
}

export function createGenerationPlan(data: GenerationPlanCreate): Promise<GenerationPlan> {
  return apiPost<GenerationPlan>('generation-plans/', data);
}

export function pauseGenerationPlan(id: number): Promise<GenerationPlan> {
  return apiPost<GenerationPlan>(`generation-plans/${id}/pause`);
}

export function resumeGenerationPlan(id: number): Promise<GenerationPlan> {
  return apiPost<GenerationPlan>(`generation-plans/${id}/resume`);
}

export function runGenerationPlanNow(id: number): Promise<GenerationPlan> {
  return apiPost<GenerationPlan>(`generation-plans/${id}/run-now`);
}
