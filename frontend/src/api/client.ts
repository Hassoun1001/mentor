/**
 * Thin typed HTTP client. We deliberately avoid axios — fetch is enough,
 * and one fewer dependency means one fewer supply-chain surface.
 */
import { z } from 'zod';

import { clearToken, getToken } from '../lib/authStorage';

const API_PREFIX = '/api/v1';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly field: string | null = null
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const errorBody = z.object({
  error: z.string(),
  message: z.string(),
  field: z.string().nullable().optional(),
});

const fastApiDetailBody = z.object({ detail: z.string() });

export async function apiPost<TResp>(
  path: string,
  body: unknown,
  schema: z.ZodSchema<TResp>
): Promise<TResp> {
  return apiRequest('POST', path, schema, body);
}

export async function apiGet<TResp>(path: string, schema: z.ZodSchema<TResp>): Promise<TResp> {
  return apiRequest('GET', path, schema);
}

export async function apiDelete<TResp>(
  path: string,
  schema: z.ZodSchema<TResp>
): Promise<TResp> {
  return apiRequest('DELETE', path, schema);
}

async function apiRequest<TResp>(
  method: 'GET' | 'POST' | 'DELETE',
  path: string,
  schema: z.ZodSchema<TResp>,
  body?: unknown
): Promise<TResp> {
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  const token = getToken();
  if (token) headers.authorization = `Bearer ${token}`;

  const init: RequestInit = { method, headers };
  if (body !== undefined) init.body = JSON.stringify(body);

  const response = await fetch(`${API_PREFIX}${path}`, init);
  const text = await response.text();
  const json = text ? JSON.parse(text) : null;

  if (response.status === 401) {
    clearToken();
    throw new ApiError(
      401,
      'unauthorized',
      typeof json?.message === 'string'
        ? json.message
        : 'session expired — sign in again'
    );
  }

  if (!response.ok) {
    const structured = errorBody.safeParse(json);
    if (structured.success) {
      throw new ApiError(
        response.status,
        structured.data.error,
        structured.data.message,
        structured.data.field ?? null
      );
    }
    const detail = fastApiDetailBody.safeParse(json);
    if (detail.success) {
      throw new ApiError(response.status, 'error', detail.data.detail);
    }
    throw new ApiError(response.status, 'unknown', `HTTP ${response.status}`);
  }

  if (response.status === 204) return null as TResp;
  return schema.parse(json);
}
