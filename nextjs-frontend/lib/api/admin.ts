import axios, { type AxiosError } from "axios";
import { ApiError } from "@/lib/api/client";
import type {
  TenantCreate,
  TenantResponse,
  ApiKeyCreate,
  ApiKeyResponseWithRaw,
  ApiKeyResponse,
} from "@/lib/types/api";

// ---------------------------------------------------------------------------
// Admin API — uses raw axios (NOT the shared apiClient which injects user JWT)
// ---------------------------------------------------------------------------

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

function adminHeaders(adminKey: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${adminKey}`,
  };
}

function handleError(err: unknown): never {
  const axErr = err as AxiosError<{ detail?: string }>;
  const status = axErr.response?.status ?? 500;
  const detail =
    axErr.response?.data?.detail ?? axErr.message ?? "Unknown error";
  throw new ApiError(status, detail);
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export async function createTenant(
  adminKey: string,
  data: TenantCreate,
): Promise<TenantResponse> {
  try {
    const { data: resp } = await axios.post<TenantResponse>(
      `${BASE_URL}/api/v2/admin/tenants`,
      data,
      { headers: adminHeaders(adminKey) },
    );
    return resp;
  } catch (err) {
    handleError(err);
  }
}

export async function getTenantApiKeys(
  adminKey: string,
  tenantId: number,
): Promise<ApiKeyResponse[]> {
  try {
    const { data } = await axios.get<ApiKeyResponse[]>(
      `${BASE_URL}/api/v2/admin/tenants/${tenantId}/api-keys`,
      { headers: adminHeaders(adminKey) },
    );
    return data;
  } catch (err) {
    handleError(err);
  }
}

export async function createApiKey(
  adminKey: string,
  tenantId: number,
  data?: ApiKeyCreate,
): Promise<ApiKeyResponseWithRaw> {
  try {
    const { data: resp } = await axios.post<ApiKeyResponseWithRaw>(
      `${BASE_URL}/api/v2/admin/tenants/${tenantId}/api-keys`,
      data ?? {},
      { headers: adminHeaders(adminKey) },
    );
    return resp;
  } catch (err) {
    handleError(err);
  }
}
