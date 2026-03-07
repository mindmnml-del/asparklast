"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useCreateCharacter } from "@/lib/hooks/useCharacters";
import { cn } from "@/lib/utils";
import { Save, User, Mountain, Box, Bug } from "lucide-react";
import type { CharacterSheet } from "@/lib/types/api";

type ExtractedData = Partial<CharacterSheet> & { is_character: boolean };

interface ExtractionPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  extractedData: ExtractedData;
}

const ENTITY_ICONS = {
  person: User,
  environment: Mountain,
  object: Box,
  creature: Bug,
} as const;

const BADGE_CLASS = "text-[10px] px-1.5 py-0 border-white/[0.08] text-muted-foreground capitalize";

export default function ExtractionPreviewModal({
  open,
  onOpenChange,
  extractedData,
}: ExtractionPreviewModalProps) {
  const [name, setName] = useState(extractedData.name ?? "");
  const [description, setDescription] = useState(extractedData.description ?? "");
  const createMutation = useCreateCharacter();

  const entityType = extractedData.entity_type ?? "person";
  const Icon = ENTITY_ICONS[entityType] ?? User;

  const handleSave = () => {
    if (!name.trim()) return;

    const payload: Record<string, unknown> = {
      ...extractedData,
      name: name.trim(),
      description: description.trim(),
      entity_type: entityType,
    };
    delete (payload as Record<string, unknown>).is_character;

    createMutation.mutate(payload, {
      onSuccess: () => onOpenChange(false),
    });
  };

  const personBadges = [
    extractedData.gender && extractedData.gender !== "unspecified" ? extractedData.gender : null,
    extractedData.age_range,
    extractedData.build,
    extractedData.eye_color,
    extractedData.hair_color,
  ].filter(Boolean) as string[];

  const envBadges = [
    extractedData.lighting,
    extractedData.atmosphere,
    extractedData.time_of_day,
    extractedData.architecture_style,
  ].filter(Boolean) as string[];

  const badges = entityType === "environment" ? envBadges : personBadges;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#1A1D26] border-white/[0.06] sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-[var(--personality-glow)] flex items-center justify-center">
              <Icon className="h-3.5 w-3.5 text-[var(--personality-primary)]" />
            </div>
            Save to Library
          </DialogTitle>
          <DialogDescription>
            Review extracted traits and save as a reusable character.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Entity type badge */}
          <Badge
            variant="outline"
            className="text-[var(--personality-primary)] border-[var(--personality-primary)]/30 capitalize"
          >
            {entityType}
          </Badge>

          {/* Editable fields */}
          <div className="space-y-2">
            <Label htmlFor="ext-name">Name</Label>
            <Input
              id="ext-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Character name"
              className="bg-[#0A0B0E] border-white/[0.06]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ext-desc">Description</Label>
            <Textarea
              id="ext-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description..."
              rows={2}
              className="resize-none bg-[#0A0B0E] border-white/[0.06]"
            />
          </div>

          {/* Extracted trait badges */}
          {badges.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-xs text-muted-foreground uppercase tracking-wider">
                Extracted Traits
              </span>
              <div className="flex flex-wrap gap-1.5">
                {badges.map((trait) => (
                  <Badge key={trait} variant="outline" className={BADGE_CLASS}>
                    {trait}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!name.trim() || createMutation.isPending}
            className={cn(
              "bg-[var(--personality-primary)] text-[#0A0B0E]",
              "hover:opacity-90 font-semibold"
            )}
          >
            <Save className="h-4 w-4 mr-1" />
            {createMutation.isPending ? "Saving..." : "Save to Library"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
