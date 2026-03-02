"use client";

import { create } from "zustand";
import type { CharacterSheet } from "@/lib/types/api";

interface CharacterState {
  lockedCharacter: CharacterSheet | null;
  sessionId: string;
  lockCharacter: (character: CharacterSheet) => void;
  unlockCharacter: () => void;
  getCharacterPromptContext: () => string;
}

function generateSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export const useCharacterStore = create<CharacterState>((set, get) => ({
  lockedCharacter: null,
  sessionId: generateSessionId(),

  lockCharacter: (character: CharacterSheet) =>
    set({ lockedCharacter: character }),

  unlockCharacter: () => set({ lockedCharacter: null }),

  getCharacterPromptContext: () => {
    const { lockedCharacter } = get();
    if (!lockedCharacter) return "";

    const traits: string[] = [];
    if (lockedCharacter.gender && lockedCharacter.gender !== "unspecified")
      traits.push(lockedCharacter.gender);
    if (lockedCharacter.age_range) traits.push(lockedCharacter.age_range);
    if (lockedCharacter.ethnicity) traits.push(lockedCharacter.ethnicity);
    if (lockedCharacter.skin_tone)
      traits.push(`${lockedCharacter.skin_tone} skin`);
    if (lockedCharacter.eye_color)
      traits.push(`${lockedCharacter.eye_color} eyes`);
    if (lockedCharacter.hair_color && lockedCharacter.hair_style)
      traits.push(
        `${lockedCharacter.hair_color} ${lockedCharacter.hair_style} hair`
      );
    if (lockedCharacter.build) traits.push(`${lockedCharacter.build} build`);
    if (lockedCharacter.height) traits.push(lockedCharacter.height);
    if (lockedCharacter.distinctive_features?.length)
      traits.push(lockedCharacter.distinctive_features.join(", "));

    return `${lockedCharacter.name}: ${traits.join(", ")}`;
  },
}));
