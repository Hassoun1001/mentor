import { z } from 'zod';

import { apiDelete, apiGet, apiPatch, apiPost } from './client';

const loginResponse = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_at: z.string(),
  username: z.string(),
  is_admin: z.boolean(),
  tabs: z.array(z.string()).nullable(), // null = every tab
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

// ---------- me / privileges ----------

const meResponse = z.object({
  username: z.string(),
  is_admin: z.boolean(),
  tabs: z.array(z.string()).nullable(),
  all_tabs: z.array(z.string()),
});
export type MeResponse = z.infer<typeof meResponse>;

export async function getMe(): Promise<MeResponse> {
  return apiGet('/auth/me', meResponse);
}

// ---------- password + user management ----------

const okResponse = z.object({ ok: z.boolean(), message: z.string() });
export type OkResponse = z.infer<typeof okResponse>;

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<OkResponse> {
  return apiPost(
    '/auth/change-password',
    { current_password: currentPassword, new_password: newPassword },
    okResponse
  );
}

const userDto = z.object({
  username: z.string(),
  is_admin: z.boolean(),
  tabs: z.array(z.string()).nullable(),
  created_at: z.string(),
});
export type UserDto = z.infer<typeof userDto>;

export async function listUsers(): Promise<UserDto[]> {
  return apiGet('/auth/users', z.array(userDto));
}

export async function createUser(input: {
  username: string;
  password: string;
  is_admin: boolean;
  tabs: string[] | null;
}): Promise<UserDto> {
  return apiPost('/auth/users', input, userDto);
}

export async function updateUserTabs(
  username: string,
  tabs: string[] | null
): Promise<UserDto> {
  const body = tabs === null ? { grant_all_tabs: true } : { tabs };
  return apiPatch(`/auth/users/${encodeURIComponent(username)}`, body, userDto);
}

export async function deleteUser(username: string): Promise<OkResponse> {
  return apiDelete(`/auth/users/${encodeURIComponent(username)}`, okResponse);
}
