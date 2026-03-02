"use client";

import { create } from "zustand";
import type { PersonalityType } from "@/lib/types/api";

interface PersonalityState {
  activePersonality: PersonalityType;
  setPersonality: (personality: PersonalityType) => void;
}

export const usePersonalityStore = create<PersonalityState>((set) => ({
  activePersonality: "zeus",
  setPersonality: (personality: PersonalityType) =>
    set({ activePersonality: personality }),
}));
