import { apiGet, apiFetch } from './client';

export type ScheduledPostStatus = 'pending' | 'processing' | 'retrying' | 'posted' | 'partially_failed' | 'cancelled' | 'failed' | 'dead_letter';

export interface ScheduledPost {
  id: number;
  content_id: number;
  meta_page_id: number;
  scheduled_at: string;
  status: ScheduledPostStatus;
  posted_at: string | null;
  failure_reason: string | null;
  created_at: string;
}

export function listScheduledPosts(
  params?: { status?: string; meta_page_id?: number; skip?: number; limit?: number }
): Promise<ScheduledPost[]> {
  return apiGet<ScheduledPost[]>('scheduled-posts/', params as Record<string, string | number | undefined>);
}

export function cancelScheduledPost(scheduledPostId: number): Promise<{ cancelled: boolean }> {
  return apiFetch<{ cancelled: boolean }>(`scheduled-posts/${scheduledPostId}/cancel`, {
    method: 'PATCH'
  });
}

export interface PostingPreference {
  id: number;
  meta_page_id: number;
  cooldown_minutes: number;
  max_posts_per_day: number;
}

export function getPostingPreference(metaPageId: number): Promise<PostingPreference> {
  return apiFetch<PostingPreference>(`scheduled-posts/preferences/${metaPageId}`, {
    method: 'GET'
  });
}

export function updatePostingPreference(
  metaPageId: number,
  data: { cooldown_minutes: number; max_posts_per_day: number }
): Promise<PostingPreference> {
  return apiFetch<PostingPreference>(`scheduled-posts/preferences/${metaPageId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  } as any);
}
