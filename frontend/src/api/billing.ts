import { apiGet, apiPost } from './client';

export interface CheckoutRequest {
    organization_id: number;
    price_id: string;
    success_url: string;
    cancel_url: string;
}

export interface PortalRequest {
    organization_id: number;
    return_url: string;
}

export async function createCheckout(req: CheckoutRequest): Promise<{ url: string }> {
    return apiPost<{ url: string }>('billing/checkout', req);
}

export interface GenerationUsageModel {
    provider: string;
    model: string;
    requests: number;
    total_tokens: number;
    estimated_cost_usd: number;
}

export interface GenerationUsageSummary {
    organization_id: number;
    requests: number;
    prompt_tokens: number;
    candidates_tokens: number;
    thoughts_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
    by_model: GenerationUsageModel[];
    recent: Array<{
        id: number;
        generation_job_id: number;
        provider: string;
        model: string;
        total_tokens: number;
        estimated_cost_usd: number;
        created_at: string;
    }>;
}

export async function createPortal(req: PortalRequest): Promise<{ url: string }> {
    return apiPost<{ url: string }>('billing/portal', req);
}

export async function getGenerationUsage(organizationId: number): Promise<GenerationUsageSummary> {
    return apiGet<GenerationUsageSummary>('billing/usage', { organization_id: organizationId });
}
