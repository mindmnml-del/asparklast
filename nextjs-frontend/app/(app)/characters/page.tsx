"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import CharacterCard, {
  CharacterCardSkeleton,
} from "@/components/character/CharacterCard";
import {
  useCharacterList,
  useDeleteCharacter,
} from "@/lib/hooks/useCharacters";
import { cn } from "@/lib/utils";

export default function CharactersPage() {
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const { data, isLoading } = useCharacterList();
  const deleteMutation = useDeleteCharacter();

  const characters = data?.characters ?? [];

  const handleDelete = () => {
    if (deleteTarget) {
      deleteMutation.mutate(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Characters
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your character library for visual consistency
          </p>
        </div>
        <Button asChild>
          <Link href="/characters/new">
            <Plus className="h-4 w-4 mr-2" />
            Create New
          </Link>
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <CharacterCardSkeleton key={i} />
          ))}
        </div>
      ) : characters.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div
            className={cn(
              "h-16 w-16 rounded-2xl flex items-center justify-center mb-4",
              "bg-[var(--personality-glow)] border border-[var(--personality-primary)]/20"
            )}
          >
            <User className="h-8 w-8 text-[var(--personality-primary)]" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-1">
            No characters yet
          </h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm">
            Create your first character to lock visual consistency across
            generations.
          </p>
          <Button asChild>
            <Link href="/characters/new">Create Character</Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {characters.map((character) => (
            <CharacterCard
              key={character.character_id}
              character={character}
              onDelete={(id) => setDeleteTarget(id)}
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
            <DialogTitle>Delete character</DialogTitle>
            <DialogDescription>
              This action cannot be undone. The character will be permanently
              removed from your library.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
