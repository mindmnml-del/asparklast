"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listCharacters,
  lockCharacter,
  unlockCharacter,
  createCharacter,
  deleteCharacter,
  extractCharacterTraits,
} from "@/lib/api/characters";
import { useCharacterStore } from "@/store/characterStore";
import { toast } from "sonner";
import type { CharacterSheet } from "@/lib/types/api";

const CHARACTERS_KEY = ["characters"] as const;

export function useCharacterList() {
  return useQuery({
    queryKey: CHARACTERS_KEY,
    queryFn: listCharacters,
    staleTime: 60_000,
  });
}

export function useLockCharacter() {
  const queryClient = useQueryClient();
  const sessionId = useCharacterStore((s) => s.sessionId);
  const setLocked = useCharacterStore((s) => s.lockCharacter);

  return useMutation({
    mutationFn: (character: CharacterSheet) =>
      lockCharacter(character.character_id, sessionId),
    onSuccess: (_data, character) => {
      setLocked(character);
      toast.success(`${character.name} locked to session`);
      queryClient.invalidateQueries({ queryKey: CHARACTERS_KEY });
    },
    onError: () => {
      toast.error("Failed to lock character");
    },
  });
}

export function useUnlockCharacter() {
  const queryClient = useQueryClient();
  const sessionId = useCharacterStore((s) => s.sessionId);
  const clearLocked = useCharacterStore((s) => s.unlockCharacter);

  return useMutation({
    mutationFn: () => unlockCharacter(sessionId),
    onSuccess: () => {
      clearLocked();
      toast.success("Character unlocked");
      queryClient.invalidateQueries({ queryKey: CHARACTERS_KEY });
    },
    onError: () => {
      toast.error("Failed to unlock character");
    },
  });
}

export function useCreateCharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Record<string, unknown>) => createCharacter(data),
    onSuccess: (resp) => {
      toast.success(`${resp.character.name} created`);
      queryClient.invalidateQueries({ queryKey: CHARACTERS_KEY });
    },
    onError: () => {
      toast.error("Failed to create character");
    },
  });
}

export function useExtractCharacterTraits() {
  return useMutation({
    mutationFn: (prompt: string) => extractCharacterTraits(prompt),
    onError: () => {
      toast.error("Failed to extract character traits");
    },
  });
}

export function useDeleteCharacter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (characterId: string) => deleteCharacter(characterId),
    onSuccess: () => {
      toast.success("Character deleted");
      queryClient.invalidateQueries({ queryKey: CHARACTERS_KEY });
    },
    onError: () => {
      toast.error("Failed to delete character");
    },
  });
}
