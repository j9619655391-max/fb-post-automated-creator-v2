import { apiDelete, apiGet, apiPost, apiPut } from './client';

export interface BrandTheme {
  id: number;
  organization_id: number;
  name: string;
  slug: string;
  description?: string | null;
  visual_style?: string | null;
  color_palette: string[];
  typography: Record<string, unknown>;
  logo_position: string;
  background_style?: string | null;
  supported_formats: string[];
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at?: string | null;
}

export type BrandThemeInput = Omit<BrandTheme, 'id' | 'organization_id' | 'created_at' | 'updated_at'>;

export function listBrandThemes(orgId: number): Promise<BrandTheme[]> {
  return apiGet<BrandTheme[]>(`organizations/${orgId}/themes`);
}

export function createBrandTheme(orgId: number, payload: BrandThemeInput): Promise<BrandTheme> {
  return apiPost<BrandTheme>(`organizations/${orgId}/themes`, payload);
}

export function updateBrandTheme(orgId: number, themeId: number, payload: BrandThemeInput): Promise<BrandTheme> {
  return apiPut<BrandTheme>(`organizations/${orgId}/themes/${themeId}`, payload);
}

export function deleteBrandTheme(orgId: number, themeId: number): Promise<void> {
  return apiDelete(`organizations/${orgId}/themes/${themeId}`);
}
