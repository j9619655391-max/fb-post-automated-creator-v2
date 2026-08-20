import { apiDelete, apiGet, apiPost, apiPut } from './client';

export type WorkspaceSourceType = 'website' | 'facebook_page' | 'instagram_account' | 'linkedin_page' | 'whatsapp_business' | 'manual';

export interface WorkspaceProfile {
  id: number;
  organization_id: number;
  business_description?: string | null;
  mission?: string | null;
  industry?: string | null;
  services: string[];
  products: string[];
  target_audience?: string | null;
  locations: string[];
  brand_voice?: string | null;
  tone?: string | null;
  keywords: string[];
  preferred_languages: string[];
  contact_email?: string | null;
  contact_phone?: string | null;
  whatsapp_display_phone?: string | null;
  whatsapp_business_account_id?: string | null;
  website_url?: string | null;
  linkedin_url?: string | null;
  facebook_url?: string | null;
  instagram_url?: string | null;
  whatsapp_url?: string | null;
  approved_claims: string[];
  prohibited_claims: string[];
  last_refreshed_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface WorkspaceSource {
  id: number;
  organization_id: number;
  source_type: WorkspaceSourceType;
  provider?: string | null;
  url?: string | null;
  external_id?: string | null;
  title?: string | null;
  content_text?: string | null;
  excerpt?: string | null;
  metadata: Record<string, unknown>;
  trust_level: string;
  review_status: string;
  is_active: boolean;
  last_fetched_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface WorkspaceIntelligence {
  profile: WorkspaceProfile | null;
  sources: WorkspaceSource[];
  source_count: number;
  approved_source_count: number;
}

export type WorkspaceProfileInput = Omit<WorkspaceProfile, 'id' | 'organization_id' | 'last_refreshed_at' | 'created_at' | 'updated_at'>;

export interface WorkspaceSourceInput {
  source_type: WorkspaceSourceType;
  provider?: string;
  url?: string;
  external_id?: string;
  title?: string;
  content_text?: string;
  excerpt?: string;
  metadata?: Record<string, unknown>;
  trust_level?: string;
  review_status?: string;
}

export function getWorkspaceIntelligence(orgId: number): Promise<WorkspaceIntelligence> {
  return apiGet<WorkspaceIntelligence>(`organizations/${orgId}/intelligence`);
}

export function saveWorkspaceProfile(orgId: number, payload: WorkspaceProfileInput): Promise<WorkspaceProfile> {
  return apiPut<WorkspaceProfile>(`organizations/${orgId}/intelligence/profile`, payload);
}

export function addWorkspaceSource(orgId: number, payload: WorkspaceSourceInput): Promise<WorkspaceSource> {
  return apiPost<WorkspaceSource>(`organizations/${orgId}/intelligence/sources`, payload);
}

export function refreshWorkspaceSource(orgId: number, sourceId: number): Promise<WorkspaceSource> {
  return apiPost<WorkspaceSource>(`organizations/${orgId}/intelligence/sources/${sourceId}/refresh`);
}

export function refreshWorkspaceSources(orgId: number): Promise<{ refreshed_source_ids: number[]; errors: string[]; refreshed_count: number }> {
  return apiPost<{ refreshed_source_ids: number[]; errors: string[]; refreshed_count: number }>(`organizations/${orgId}/intelligence/refresh`);
}

export function removeWorkspaceSource(orgId: number, sourceId: number): Promise<void> {
  return apiDelete(`organizations/${orgId}/intelligence/sources/${sourceId}`);
}
