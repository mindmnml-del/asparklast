"use client";

import { useState } from "react";
import { Lock, Unlock, User, ChevronDown } from "lucide-react";
import { useCharacterStore } from "@/store/characterStore";
import { useCharacterList, useLockCharacter, useUnlockCharacter } from "@/lib/hooks/useCharacters";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { CharacterSheet } from "@/lib/types/api";

export default function CharacterLockWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const lockedCharacter = useCharacterStore((s) => s.lockedCharacter);
  const { data, isLoading } = useCharacterList();
  const lockMutation = useLockCharacter();
  const unlockMutation = useUnlockCharacter();

  const characters = data?.characters ?? [];

  const handleLock = (character: CharacterSheet) => {
    lockMutation.mutate(character);
    setIsOpen(false);
  };

  const handleUnlock = () => {
    unlockMutation.mutate();
  };

  if (lockedCharacter) {
    return (
      <div
        className={cn(
          "rounded-xl p-3 space-y-2",
          "bg-[#1A1D26] border border-[var(--personality-primary)]/20"
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <Lock className="h-3.5 w-3.5 shrink-0 text-[var(--personality-primary)]" />
            <span className="text-sm font-medium text-foreground truncate">
              {lockedCharacter.name}
            </span>
          </div>
          <Badge
            variant="outline"
            className="shrink-0 text-[10px] px-1.5 py-0 text-[var(--personality-primary)] border-[var(--personality-primary)]/30 bg-[var(--personality-glow)]"
          >
            LOCKED
          </Badge>
        </div>

        <div className="text-xs text-muted-foreground space-y-0.5">
          {lockedCharacter.eye_color && lockedCharacter.hair_color && (
            <p>
              {lockedCharacter.eye_color} eyes, {lockedCharacter.hair_color} hair
            </p>
          )}
          {lockedCharacter.build && lockedCharacter.height && (
            <p>
              {lockedCharacter.height}, {lockedCharacter.build} build
            </p>
          )}
          {lockedCharacter.distinctive_features?.length > 0 && (
            <p className="italic">
              {lockedCharacter.distinctive_features.slice(0, 2).join(", ")}
            </p>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleUnlock}
          disabled={unlockMutation.isPending}
          className="w-full text-xs text-muted-foreground hover:text-foreground"
        >
          <Unlock className="h-3 w-3 mr-1.5" />
          {unlockMutation.isPending ? "Unlocking..." : "Unlock"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center justify-between gap-2",
          "px-3 py-2 rounded-lg text-sm",
          "bg-white/[0.04] border border-white/[0.06]",
          "text-muted-foreground hover:text-foreground transition-colors"
        )}
      >
        <span className="flex items-center gap-2">
          <User className="h-3.5 w-3.5" />
          Select character
        </span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div
          className={cn(
            "rounded-xl overflow-hidden",
            "bg-[#1A1D26] border border-white/[0.06]",
            "max-h-48 overflow-y-auto"
          )}
        >
          {isLoading && (
            <p className="px-3 py-4 text-xs text-muted-foreground text-center">
              Loading...
            </p>
          )}

          {!isLoading && characters.length === 0 && (
            <p className="px-3 py-4 text-xs text-muted-foreground text-center">
              No characters yet
            </p>
          )}

          {characters.map((char) => (
            <button
              key={char.character_id}
              onClick={() => handleLock(char)}
              disabled={lockMutation.isPending}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 text-left",
                "hover:bg-white/[0.04] transition-colors",
                "border-b border-white/[0.03] last:border-b-0"
              )}
            >
              <div className="h-7 w-7 rounded-full bg-[var(--personality-glow)] flex items-center justify-center shrink-0">
                <User className="h-3.5 w-3.5 text-[var(--personality-primary)]" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {char.name}
                </p>
                {char.description && (
                  <p className="text-[11px] text-muted-foreground truncate">
                    {char.description}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
