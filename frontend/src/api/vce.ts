import { apiFetch, apiGet } from './client';

export interface ContentCategory {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  created_at: string;
}

export interface SuggestedCategory {
  category: ContentCategory;
  reason?: string | null;
  evidence_terms: string[];
  advisory_only: boolean;
}

export interface GenerateThemesResponse {
  themes: string[];
  available: boolean;
}

export function getCategories(organizationId?: number): Promise<ContentCategory[]> {
  const query = organizationId ? `?organization_id=${organizationId}` : '';
  return apiGet<ContentCategory[]>(`vce/categories${query}`);
}

export function getRecommendedCategory(organizationId: number): Promise<SuggestedCategory> {
  return apiGet<SuggestedCategory>(`vce/categories/recommended?organization_id=${organizationId}`);
}

export function generateThemes(
    params: { category_id?: number; category_name?: string; count?: number; organization_id?: number; extra_instruction?: string }

): Promise<GenerateThemesResponse> {
  return apiFetch<GenerateThemesResponse>('vce/generate-themes', {
    method: 'GET',
    params: params as Record<string, string | number | undefined>,
    timeoutMs: 15000,
  }).catch((error) => {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Theme generation timed out. You can continue with the selected category and template.');
    }
    throw error;
  });
}
