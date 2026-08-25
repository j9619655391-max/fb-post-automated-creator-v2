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
  image_text?: string | null;
  caption: string;
  alt_text?: string | null;
  cta?: string | null;
  objective?: string | null;
  creative_archetype?: string | null;
  hashtags: string[];
  tags: string[];
  source_urls: string[];
  source_refs?: string[];
  claim_refs?: string[];
  visual_brief?: Record<string, unknown>;
  asset_provenance?: Record<string, unknown>;
  media_variant_ids: number[];
  visual_qa_status?: string;
  visual_qa_flags?: string[];
  media_variant_urls?: string[];
  status: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ContentPackageInput {
  platforms: ContentPackagePlatform[];
  theme_id?: number;
  opportunity_id?: number;
  image_text?: string;
  alt_text?: string;
  objective?: string;
  creative_archetype?: string;
  source_refs?: string[];
  claim_refs?: string[];
  visual_brief?: Record<string, unknown>;
  asset_provenance?: Record<string, unknown>;
}

export function createContentPackages(contentId: number, organizationId: number, payload: ContentPackageInput): Promise<ContentPackage[]> {
  return apiPost<ContentPackage[]>(`content/${contentId}/packages?organization_id=${organizationId}`, payload);
}
