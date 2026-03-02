"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getPrompts,
  getPromptById,
  toggleFavorite,
  deletePrompt,
  exportPrompts,
  type GetPromptsParams,
  type ExportFormat,
} from "@/lib/api/history";
import type { ApiError } from "@/lib/api/client";
import type { GeneratedPromptHistory } from "@/lib/types/api";

const PROMPTS_KEY = ["prompts"] as const;

/** Fetch the user's prompt history list. */
export function usePrompts(params?: GetPromptsParams) {
  return useQuery({
    queryKey: [...PROMPTS_KEY, params ?? {}],
    queryFn: () => getPrompts(params),
    staleTime: 60_000,
  });
}

/** Toggle a prompt's favorite status with optimistic update. */
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation<
    unknown,
    ApiError,
    { id: number; is_favorite: boolean }
  >({
    mutationFn: ({ id, is_favorite }) => toggleFavorite(id, is_favorite),

    onMutate: async ({ id, is_favorite }) => {
      // Cancel in-flight refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: PROMPTS_KEY });

      // Snapshot every prompts query in the cache
      const previousQueries = queryClient.getQueriesData<
        GeneratedPromptHistory[]
      >({ queryKey: PROMPTS_KEY });

      // Optimistically update all matching caches
      queryClient.setQueriesData<GeneratedPromptHistory[]>(
        { queryKey: PROMPTS_KEY },
        (old) =>
          old?.map((p) => (p.id === id ? { ...p, is_favorite } : p))
      );

      return { previousQueries };
    },

    onError: (_err, _vars, context) => {
      // Roll back to the snapshot on failure
      const ctx = context as {
        previousQueries: [
          readonly unknown[],
          GeneratedPromptHistory[] | undefined,
        ][];
      } | undefined;
      ctx?.previousQueries.forEach(([key, data]) => {
        queryClient.setQueryData(key, data);
      });
      toast.error("Failed to update favorite");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: PROMPTS_KEY });
    },
  });
}

/** Delete a prompt. */
export function useDeletePrompt() {
  const queryClient = useQueryClient();

  return useMutation<unknown, ApiError, number>({
    mutationFn: (id) => deletePrompt(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROMPTS_KEY });
      toast.success("Prompt deleted");
    },
    onError: () => {
      toast.error("Failed to delete prompt");
    },
  });
}

/** Copy a prompt's paragraph text to clipboard (fetches full prompt first). */
export function useCopyPrompt() {
  return useMutation<void, ApiError, number>({
    mutationFn: async (id) => {
      const prompt = await getPromptById(id);
      const text =
        (prompt.raw_response as Record<string, unknown>)
          ?.paragraphPrompt as string | undefined;
      if (!text) throw new Error("No prompt text found");
      await navigator.clipboard.writeText(text);
    },
    onSuccess: () => {
      toast.success("Prompt copied to clipboard");
    },
    onError: () => {
      toast.error("Failed to copy prompt");
    },
  });
}

/** Export prompts as a downloadable file. */
export function useExportPrompts() {
  return useMutation<
    Blob,
    ApiError,
    { format: ExportFormat; favoritesOnly: boolean }
  >({
    mutationFn: ({ format, favoritesOnly }) =>
      exportPrompts(format, favoritesOnly),
    onSuccess: (blob, { format }) => {
      const date = new Date().toISOString().slice(0, 10);
      const filename = `aispark_prompts_${date}.${format}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(`Exported as ${format.toUpperCase()}`);
    },
    onError: (error) => {
      toast.error(error.detail || "Export failed");
    },
  });
}
