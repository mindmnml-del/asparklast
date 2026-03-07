"use client";

import { MoreHorizontal, Trash2, User, Mountain, Box, Bug } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CharacterSheet } from "@/lib/types/api";

interface CharacterCardProps {
  character: CharacterSheet;
  onDelete: (id: string) => void;
}

const ENTITY_ICONS = {
  person: User,
  environment: Mountain,
  object: Box,
  creature: Bug,
} as const;

export default function CharacterCard({
  character,
  onDelete,
}: CharacterCardProps) {
  const entityType = character.entity_type ?? "person";
  const Icon = ENTITY_ICONS[entityType] ?? User;

  return (
    <div
      className={cn(
        "group relative flex flex-col gap-3 p-4 rounded-xl",
        "bg-[#1A1D26] border border-white/[0.06]",
        "hover:border-[var(--personality-primary)]/20",
        "transition-all duration-200"
      )}
    >
      {/* Header: avatar + name + actions */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-9 w-9 rounded-full bg-[var(--personality-glow)] flex items-center justify-center shrink-0">
            <Icon className="h-4 w-4 text-[var(--personality-primary)]" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-medium text-foreground truncate">
              {character.name}
            </h3>
            {character.description && (
              <p className="text-xs text-muted-foreground line-clamp-1">
                {character.description}
              </p>
            )}
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="p-1 rounded-md text-muted-foreground/40 hover:text-muted-foreground transition-colors"
              aria-label="Character actions"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="bg-[#1A1D26] border-white/[0.06]"
          >
            <DropdownMenuItem
              onClick={() => onDelete(character.character_id)}
              className="text-red-400 focus:text-red-400"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Trait badges */}
      <div className="flex flex-wrap gap-1.5">
        {entityType === "environment" ? (
          <>
            {character.lighting && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground capitalize">
                {character.lighting}
              </Badge>
            )}
            {character.atmosphere && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground capitalize">
                {character.atmosphere}
              </Badge>
            )}
          </>
        ) : (
          <>
            {character.gender && character.gender !== "unspecified" && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground capitalize">
                {character.gender}
              </Badge>
            )}
            {character.age_range && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground">
                {character.age_range}
              </Badge>
            )}
            {character.build && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground capitalize">
                {character.build}
              </Badge>
            )}
          </>
        )}
      </div>

      {/* Usage */}
      <span className="text-xs text-muted-foreground">
        Used {character.times_used} {character.times_used === 1 ? "time" : "times"}
      </span>
    </div>
  );
}

export function CharacterCardSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl bg-[#1A1D26] border border-white/[0.06] animate-pulse">
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-full bg-white/[0.04] shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-2/3 rounded bg-white/[0.04]" />
          <div className="h-3 w-1/2 rounded bg-white/[0.04]" />
        </div>
      </div>
      <div className="flex gap-1.5">
        <div className="h-4 w-12 rounded bg-white/[0.04]" />
        <div className="h-4 w-16 rounded bg-white/[0.04]" />
      </div>
      <div className="h-3 w-16 rounded bg-white/[0.04]" />
    </div>
  );
}
