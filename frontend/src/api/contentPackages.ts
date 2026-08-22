import { apiPost } from './client';

export type ContentPackagePlatform = 'facebook' | 'instagram' | 'linkedin';

export interface ContentPackage {
  id: number;
  organization_id?: number | null;
  source_content_id: number;
  theme_id?: number | null;
  opportunity_id?: number | null;
  platform: ContentPackagePlatform;
  headline?: string | null;
  caption: string;
  cta?: string | null;
  hashtags: string[];
  source_urls: string[];
  media_variant_ids: number[];
  status: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ContentPackageInput {
  platforms: ContentPackagePlatform[];
  theme_id?: number;
  opportunity_id?: number;
}

export function createContentPackages(contentId: number, organizationId: number, payload: ContentPackageInput): Promise<ContentPackage[]> {
  return apiPost<ContentPackage[]>(`content/${contentId}/packages?organization_id=${organizationId}`, payload);
}
