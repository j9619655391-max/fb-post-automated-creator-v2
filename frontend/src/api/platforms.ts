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
