"use client";

import { MoreHorizontal, Star, Copy, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { GeneratedPromptHistory } from "@/lib/types/api";

interface PromptCardProps {
  prompt: GeneratedPromptHistory;
  onToggleFavorite: (id: number, is_favorite: boolean) => void;
  onCopy: (id: number) => void;
  onDelete: (id: number) => void;
  isCopying?: boolean;
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMs / 3_600_000);
  const diffDay = Math.floor(diffMs / 86_400_000);

  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function PromptCard({
  prompt,
  onToggleFavorite,
  onCopy,
  onDelete,
  isCopying,
}: PromptCardProps) {
  return (
    <div
      className={cn(
        "group relative flex flex-col gap-3 p-4 rounded-xl",
        "bg-[#1A1D26] border border-white/[0.06]",
        "hover:border-[var(--personality-primary)]/20",
        "transition-all duration-200"
      )}
    >
      {/* Header row: title + actions */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-foreground line-clamp-2 flex-1">
          {prompt.title ?? "Untitled prompt"}
        </h3>

        <div className="flex items-center gap-1 shrink-0">
          {/* Favorite toggle */}
          <button
            onClick={() =>
              onToggleFavorite(prompt.id, !prompt.is_favorite)
            }
            className={cn(
              "p-1 rounded-md transition-colors",
              prompt.is_favorite
                ? "text-[var(--personality-primary)]"
                : "text-muted-foreground/40 hover:text-muted-foreground"
            )}
            aria-label={
              prompt.is_favorite
                ? "Remove from favorites"
                : "Add to favorites"
            }
          >
            <Star
              className="h-4 w-4"
              fill={prompt.is_favorite ? "currentColor" : "none"}
            />
          </button>

          {/* Actions dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-1 rounded-md text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                aria-label="Prompt actions"
              >
                <MoreHorizontal className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="bg-[#1A1D26] border-white/[0.06]"
            >
              <DropdownMenuItem
                onClick={() => onCopy(prompt.id)}
                disabled={isCopying}
              >
                <Copy className="h-4 w-4 mr-2" />
                {isCopying ? "Copying..." : "Copy prompt"}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(prompt.id)}
                className="text-red-400 focus:text-red-400"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Date */}
      <span className="text-xs text-muted-foreground">
        {formatRelativeDate(prompt.created_at)}
      </span>
    </div>
  );
}

/** Skeleton for loading state. */
export function PromptCardSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl bg-[#1A1D26] border border-white/[0.06] animate-pulse">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 space-y-2">
          <div className="h-4 w-3/4 rounded bg-white/[0.04]" />
          <div className="h-4 w-1/2 rounded bg-white/[0.04]" />
        </div>
        <div className="h-6 w-6 rounded bg-white/[0.04]" />
      </div>
      <div className="h-3 w-20 rounded bg-white/[0.04]" />
    </div>
  );
}
