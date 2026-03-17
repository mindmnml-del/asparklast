import apiClient from "@/lib/api/client";
import type {
  CharacterListResponse,
  CharacterResponse,
  CharacterLockResponse,
  SessionCharacterResponse,
  CharacterExtractionResponse,
} from "@/lib/types/api";

export async function createCharacter(
  data: Record<string, unknown>
): Promise<CharacterResponse> {
  const { data: resp } = await apiClient.post<CharacterResponse>(
    "/characters/create",
    data
  );
  return resp;
}

export async function deleteCharacter(
  characterId: string
): Promise<{ success: boolean }> {
  const { data } = await apiClient.delete<{ success: boolean }>(
    `/characters/${characterId}`
  );
  return data;
}

export async function listCharacters(): Promise<CharacterListResponse> {
  const { data } = await apiClient.get<CharacterListResponse>(
    "/characters/list"
  );
  return data;
}

export async function getCharacter(
  characterId: string
): Promise<CharacterResponse> {
  const { data } = await apiClient.get<CharacterResponse>(
    `/characters/${characterId}`
  );
  return data;
}

export async function lockCharacter(
  characterId: string,
  sessionId: string
): Promise<CharacterLockResponse> {
  const { data } = await apiClient.post<CharacterLockResponse>(
    `/characters/${characterId}/lock`,
    null,
    { headers: { "X-Session-ID": sessionId } }
  );
  return data;
}

export async function unlockCharacter(
  sessionId: string
): Promise<CharacterLockResponse> {
  const { data } = await apiClient.delete<CharacterLockResponse>(
    "/characters/unlock",
    { headers: { "X-Session-ID": sessionId } }
  );
  return data;
}

export async function extractCharacterTraits(
  prompt: string
): Promise<CharacterExtractionResponse> {
  const { data } = await apiClient.post<CharacterExtractionResponse>(
    "/characters/extract-from-prompt",
    { prompt }
  );
  return data;
}

export async function getSessionCharacter(
  sessionId: string
): Promise<SessionCharacterResponse> {
  const { data } = await apiClient.get<SessionCharacterResponse>(
    "/characters/session/current",
    { headers: { "X-Session-ID": sessionId } }
  );
  return data;
}
