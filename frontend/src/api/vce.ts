import { apiGet } from './client';

export interface ContentCategory {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  created_at: string;
}

export interface GenerateThemesResponse {
  themes: string[];
  available: boolean;
}

export function getCategories(): Promise<ContentCategory[]> {
  return apiGet<ContentCategory[]>('vce/categories');
}

export function generateThemes(
    params: { category_id?: number; category_name?: string; count?: number; organization_id?: number; extra_instruction?: string }

): Promise<GenerateThemesResponse> {
  return apiGet<GenerateThemesResponse>('vce/generate-themes', params as Record<string, string | number | undefined>);
}
