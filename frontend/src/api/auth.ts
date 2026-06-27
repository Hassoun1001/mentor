import { z } from 'zod';

import { apiGet, apiPost } from './client';

const loginResponse = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_at: z.string(),
});
export type LoginResponse = z.infer<typeof loginResponse>;

const statusResponse = z.object({ auth_enabled: z.boolean() });
export type StatusResponse = z.infer<typeof statusResponse>;

export async function getAuthStatus(): Promise<StatusResponse> {
  return apiGet('/auth/status', statusResponse);
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  return apiPost('/auth/login', { username, password }, loginResponse);
}
