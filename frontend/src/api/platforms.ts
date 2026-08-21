import { apiGet, apiPost } from './client';

export interface PlatformStatus {
    platform: string;
    connected: boolean;
    accounts_count: number;
    configured: boolean;

}

export interface LinkedInAccount {
    id: number;
    linkedin_id: string;
    name: string;
    account_type: string;
}

export function getPlatformsStatus(): Promise<PlatformStatus[]> {
    return apiGet<PlatformStatus[]>('platforms/status');
}

export function listLinkedInAccounts(): Promise<LinkedInAccount[]> {
    return apiGet<LinkedInAccount[]>('platforms/linkedin/accounts');
}

export function syncLinkedInAccounts(): Promise<{ synced: number }> {
    return apiPost<{ synced: number }>('platforms/linkedin/sync');
}


export interface PlatformSandboxReadiness {
    facebook: {
        configured: boolean;
        connected: boolean;
        remote_check: string;
        pages_count: number;
        publish_ready: boolean;
        reason: string | null;
    };
    instagram: {
        configured: boolean;
        connected: boolean;
        remote_check: string;
        publish_ready: boolean;
        reason: string | null;
        meta_dependency: string;
    };
    linkedin: {
        configured: boolean;
        connected: boolean;
        remote_check: string;
        accounts_count: number;
        organization_accounts_count: number;
        publish_ready: boolean;
        reason: string | null;
    };
    publishing_attempted: boolean;
}

export function getPlatformSandboxReadiness(): Promise<PlatformSandboxReadiness> {
    return apiGet<PlatformSandboxReadiness>('platforms/sandbox-readiness');
}
