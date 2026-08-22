import { apiGet, apiPost, apiPut } from './client';

export interface SocialSignal {
  id: number;
  organization_id: number;
  signal_type: 'mention' | 'competitor' | 'audience' | 'trend';
  source_type: string;
  source_url?: string | null;
  title: string;
  excerpt?: string | null;
  publisher?: string | null;
  published_at?: string | null;
  sentiment: 'positive' | 'neutral' | 'negative' | 'mixed';
  sentiment_score?: number | null;
  relevance_score: number;
  engagement_count: number;
  metadata: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface SignalSummary {
  organization_id: number;
  signal_count: number;
  sentiments: Record<string, number>;
  signal_types: Record<string, number>;
  average_relevance: number;
  latest_published_at?: string | null;
}

export interface AnalyticsSummary {
  organization_id: number;
  metric_count: number;
  totals: Record<string, number>;
  by_platform: Record<string, { metric_count: number; impressions: number; reach: number; engagements: number; engagement_rate: number }>;
  top_content: Array<{ content_id: number; title: string; risk_tier: string; engagements: number; reach: number }>;
}

export interface AutomationPolicy {
  id: number;
  organization_id: number;
  approval_mode: 'required' | 'controlled';
  autopilot_enabled: boolean;
  emergency_stop: boolean;
  emergency_stop_reason?: string | null;
  max_autopilot_risk_tier: 'low' | 'medium' | 'high' | 'critical';
  max_autopilot_posts_per_day: number;
  max_approval_batch_size: number;
  approval_batch_window_minutes: number;
  max_daily_generated_drafts: number;
}

export interface BrandedMediaVariant {
  id: number;
  filename: string;
  mime_type: string;
  file_size: number;
  url: string;
}

export interface BrandedMediaComposeRequest {
  source_media_id: number;
  theme_id?: number;
  template_family: 'fashion-editorial' | 'product-catalog' | 'quote-card' | 'collection-story';
  headline: string;
  body: string;
  cta: string;
  website?: string;
  handle?: string;
  phone?: string;
  whatsapp?: string;
  location?: string;
}

export interface AutomationDecision {
  content_id: number;
  risk_score: number;
  risk_tier: string;
  risk_flags: string[];
  autopilot_allowed: boolean;
  reason: string;
}

export function listSignals(orgId: number, signalType?: string): Promise<SocialSignal[]> {
  const suffix = signalType ? `?signal_type=${encodeURIComponent(signalType)}` : '';
  return apiGet<SocialSignal[]>(`organizations/${orgId}/signals${suffix}`);
}

export function collectSignals(orgId: number): Promise<SocialSignal[]> {
  return apiPost<SocialSignal[]>(`organizations/${orgId}/signals/collect`);
}

export function getSignalSummary(orgId: number): Promise<SignalSummary> {
  return apiGet<SignalSummary>(`organizations/${orgId}/signals/summary`);
}

export function getAnalyticsSummary(orgId: number): Promise<AnalyticsSummary> {
  return apiGet<AnalyticsSummary>(`organizations/${orgId}/analytics`);
}

export function getAutomationPolicy(orgId: number): Promise<AutomationPolicy> {
  return apiGet<AutomationPolicy>(`organizations/${orgId}/automation/policy`);
}

export function updateAutomationPolicy(orgId: number, policy: Partial<AutomationPolicy>): Promise<AutomationPolicy> {
  return apiPut<AutomationPolicy>(`organizations/${orgId}/automation/policy`, policy);
}

export function triggerEmergencyStop(orgId: number, reason: string): Promise<AutomationPolicy> {
  return apiPost<AutomationPolicy>(`organizations/${orgId}/automation/emergency-stop?reason=${encodeURIComponent(reason)}`);
}

export function clearEmergencyStop(orgId: number): Promise<AutomationPolicy> {
  return apiPost<AutomationPolicy>(`organizations/${orgId}/automation/emergency-stop/clear`);
}

export function composeBrandedMedia(orgId: number, request: BrandedMediaComposeRequest): Promise<BrandedMediaVariant[]> {
  return apiPost<BrandedMediaVariant[]>(`organizations/${orgId}/media/compose`, request);
}

export function getAutomationDecision(orgId: number, contentId: number): Promise<AutomationDecision> {
  return apiGet<AutomationDecision>(`organizations/${orgId}/automation/content/${contentId}/decision`);
}
