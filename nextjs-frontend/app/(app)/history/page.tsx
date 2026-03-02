"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { BookOpen, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import HistoryControls from "@/components/history/HistoryControls";
import PromptCard, {
  PromptCardSkeleton,
} from "@/components/history/PromptCard";
import {
  usePrompts,
  useToggleFavorite,
  useDeletePrompt,
  useCopyPrompt,
} from "@/lib/hooks/useHistory";
import { cn } from "@/lib/utils";

type FilterTab = "all" | "favorites";

export default function HistoryPage() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);

  // Data fetching
  const { data: prompts, isLoading } = usePrompts({
    favorites_only: activeFilter === "favorites",
  });

  // Mutations
  const toggleFavorite = useToggleFavorite();
  const deletePrompt = useDeletePrompt();
  const copyPrompt = useCopyPrompt();

  // Client-side search filter
  const filtered = useMemo(() => {
    if (!prompts) return [];
    if (!search.trim()) return prompts;
    const q = search.toLowerCase();
    return prompts.filter((p) =>
      (p.title ?? "").toLowerCase().includes(q)
    );
  }, [prompts, search]);

  const handleDelete = () => {
    if (deleteTarget !== null) {
      deletePrompt.mutate(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          The Library
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Browse, search, and manage your generated prompts
        </p>
      </div>

      {/* Controls */}
      <HistoryControls
        search={search}
        onSearchChange={setSearch}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
      />

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <PromptCardSkeleton key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          hasPrompts={!!prompts && prompts.length > 0}
          isFiltered={activeFilter === "favorites" || search.trim().length > 0}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((prompt) => (
            <PromptCard
              key={prompt.id}
              prompt={prompt}
              onToggleFavorite={(id, is_favorite) =>
                toggleFavorite.mutate({ id, is_favorite })
              }
              onCopy={(id) => copyPrompt.mutate(id)}
              onDelete={(id) => setDeleteTarget(id)}
              isCopying={
                copyPrompt.isPending &&
                copyPrompt.variables === prompt.id
              }
            />
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent className="bg-[#1A1D26] border-white/[0.06]">
          <DialogHeader>
            <DialogTitle>Delete prompt</DialogTitle>
            <DialogDescription>
              This action cannot be undone. The prompt will be permanently
              removed from your library.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setDeleteTarget(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deletePrompt.isPending}
            >
              {deletePrompt.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function EmptyState({
  hasPrompts,
  isFiltered,
}: {
  hasPrompts: boolean;
  isFiltered: boolean;
}) {
  if (isFiltered) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <BookOpen className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-muted-foreground">
          {hasPrompts
            ? "No matching prompts found"
            : "No favorites yet"}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div
        className={cn(
          "h-16 w-16 rounded-2xl flex items-center justify-center mb-4",
          "bg-[var(--personality-glow)] border border-[var(--personality-primary)]/20"
        )}
      >
        <Sparkles className="h-8 w-8 text-[var(--personality-primary)]" />
      </div>
      <h3 className="text-lg font-medium text-foreground mb-1">
        No prompts yet
      </h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">
        Generate your first prompt in the Studio and it will appear here.
      </p>
      <Button asChild>
        <Link href="/generate">Go to Studio</Link>
      </Button>
    </div>
  );
}
