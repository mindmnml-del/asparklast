"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createTenant,
  getTenantApiKeys,
  createApiKey,
} from "@/lib/api/admin";
import { toast } from "sonner";
import type { TenantCreate, ApiKeyCreate } from "@/lib/types/api";

const ADMIN_KEYS_KEY = ["admin", "api-keys"] as const;

export function useCreateTenant(adminKey: string) {
  return useMutation({
    mutationFn: (data: TenantCreate) => createTenant(adminKey, data),
    onSuccess: (resp) => {
      toast.success(`Tenant "${resp.name}" created (ID: ${resp.id})`);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to create tenant");
    },
  });
}

export function useTenantApiKeys(adminKey: string, tenantId: number | null) {
  return useQuery({
    queryKey: [...ADMIN_KEYS_KEY, tenantId],
    queryFn: () => getTenantApiKeys(adminKey, tenantId!),
    enabled: !!adminKey && tenantId !== null,
    staleTime: 30_000,
  });
}

export function useCreateApiKey(adminKey: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      data,
    }: {
      tenantId: number;
      data?: ApiKeyCreate;
    }) => createApiKey(adminKey, tenantId, data),
    onSuccess: (_resp, variables) => {
      toast.success("API key generated — save it now!");
      queryClient.invalidateQueries({
        queryKey: [...ADMIN_KEYS_KEY, variables.tenantId],
      });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to generate API key");
    },
  });
}
