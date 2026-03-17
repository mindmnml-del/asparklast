// ============================================================
// AISpark Studio API Types
// Manually typed from backend/core/schemas.py
// ============================================================

// --- Auth ---

export interface UserCreate {
  email: string;
  password: string;
  full_name?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  credits: number;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface TokenData {
  email: string | null;
}

// --- Generation ---

export interface StudioRequest {
  subject_action: string;
  environment_setting?: string;
  shot_type?: string;
  lighting?: string;
  mood?: string;
  color_palette?: string;
  artistic_styles?: string[];
  negative_prompts?: string;
  prompt_type?: "image" | "video";
  target_model: string;
  use_rag?: boolean;
  user_language?: string;
}

export interface GenerationRequest {
  prompt: string;
  negative_prompt?: string;
  style?: string;
  type?: "image" | "video" | "universal";
  tool?: string;
  diversity_enabled?: boolean;
  rag_enabled?: boolean;
}

export interface PromptStructure {
  subject: string;
  setting: string;
  lighting: string;
  composition: string;
  styleAndMedium: string;
  technicalDetails: string;
  mood: string;
}

export interface AIResponse {
  structuredPrompt: PromptStructure;
  paragraphPrompt: string;
  negativePrompt: string;
  tool: string;
  type: string;
  _metadata?: Record<string, unknown>;
}

export interface Feedback {
  id: number;
  liked: boolean;
  comment: string | null;
  user_id: number;
  created_at: string;
}

export interface FeedbackCreate {
  liked: boolean;
  comment?: string;
}

export interface GeneratedPrompt {
  id: number;
  raw_response: Record<string, unknown>;
  title: string | null;
  is_favorite: boolean;
  created_at: string;
  owner_id: number;
  feedback: Feedback[];
}

export interface GeneratedPromptHistory {
  id: number;
  title: string | null;
  is_favorite: boolean;
  created_at: string;
}

// --- Critic ---

export interface CriticAnalysisRequest {
  prompt: string;
  negative_prompt?: string;
  analysis_type?: "photo" | "video" | "both";
}

export interface CriticAnalysis {
  overall_score: number;
  category_scores: Record<string, number>;
  assessment: string;
  strengths: string[];
  weaknesses: string[];
  top_suggestion: string;
  improved_prompt: string | null;
}

// --- Character Lock ---

export type EntityType = "person" | "environment" | "object" | "creature";

export type GenderType = "male" | "female" | "non-binary" | "unspecified";

export type AgeRange =
  | "child (5-12)"
  | "teenager (13-19)"
  | "young adult (20-35)"
  | "middle-aged (36-55)"
  | "senior (55+)";

export type BuildType =
  | "slim"
  | "athletic"
  | "average"
  | "muscular"
  | "curvy"
  | "heavy-set";

export interface CharacterSheet {
  name: string;
  character_id: string;
  description: string;
  gender: GenderType;
  age_range: AgeRange;
  ethnicity: string;
  skin_tone: string;
  face_shape: string;
  eye_color: string;
  eye_shape: string;
  eyebrow_style: string;
  nose_shape: string;
  lip_shape: string;
  hair_color: string;
  hair_style: string;
  hair_length: string;
  facial_hair: string;
  height: string;
  build: BuildType;
  distinctive_features: string[];
  clothing_style: string;
  typical_outfit: string;
  accessories: string[];
  color_palette: string[];
  personality_traits: string[];
  mannerisms: string[];
  voice_characteristics: string;
  created_at: string;
  updated_at: string;
  version: string;
  tags: string[];
  reference_images: string[];
  times_used: number;
  last_used: string | null;
  successful_generations: number;
  // Multi-entity fields
  entity_type?: EntityType;
  lighting?: string;
  atmosphere?: string;
  time_of_day?: string;
  architecture_style?: string;
}

export interface CharacterResponse {
  success: boolean;
  character: CharacterSheet;
  message?: string;
}

export interface CharacterListResponse {
  success: boolean;
  characters: CharacterSheet[];
  total: number;
}

export interface CharacterLockResponse {
  success: boolean;
  message: string;
  session_id: string;
  character_id?: string;
}

export interface SessionCharacterResponse {
  success: boolean;
  character: CharacterSheet | null;
  message?: string;
  session_id?: string;
}

export interface CharacterExtractionRequest {
  prompt: string;
}

export interface CharacterExtractionResponse {
  success: boolean;
  extracted: Partial<CharacterSheet> & { is_character: boolean };
  is_character: boolean;
}

export interface CharacterStatsResponse {
  success: boolean;
  stats: {
    total_characters: number;
    active_locks: number;
    total_usage: number;
    successful_generations: number;
    success_rate: number;
    most_used_character: string | null;
  };
}

// --- Helios Personalities ---

export type PersonalityType =
  | "prometheus"
  | "zeus"
  | "poseidon"
  | "artemis"
  | "dionysus"
  | "athena";

export interface PersonalityProfile {
  name: string;
  symbol: string;
  title: string;
  specialization: string;
  traits: string[];
  signature_elements: string[];
  language_style: string;
  strengths: string[];
}

export interface PersonalityListResponse {
  success: boolean;
  personalities: Record<string, PersonalityProfile>;
  total_count: number;
}

export interface PersonalityDetailResponse {
  success: boolean;
  personality: PersonalityProfile & { type: PersonalityType };
}

export interface HeliosAnalyzeRequest {
  prompt: string;
  context?: Record<string, unknown>;
}

export interface HeliosAnalyzeResponse {
  success: boolean;
  analysis: Record<string, unknown>;
  personality_selection: {
    primary: {
      type: PersonalityType;
      profile: PersonalityProfile;
    };
    secondary: Array<{
      type: PersonalityType;
      profile: PersonalityProfile;
    }>;
    reasoning: string;
  };
}

export interface HeliosEnhanceRequest {
  prompt: string;
  personality?: string;
}

export interface HeliosEnhanceResponse {
  success: boolean;
  original_prompt: string;
  enhanced_prompt: string;
  personality: {
    name: string;
    profile: PersonalityProfile;
  };
  signature_elements: string[];
  personality_context: string;
}

export interface HeliosStatsResponse {
  success: boolean;
  stats: {
    total_selections: number;
    personality_usage: Record<string, number>;
    avg_scores: Record<string, number>;
    most_used: string | null;
  };
  system_info: {
    total_personalities: number;
    personality_names: string[];
  };
}

// --- Utility Types ---

export interface ErrorResponse {
  error: boolean;
  message: string;
  details?: string;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  invalid_value: unknown;
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  services: Record<string, string>;
  version: string;
}

export interface ServiceStatus {
  configured: boolean;
  model_name: string | null;
  request_count: number;
  avg_response_time: number;
  cache_stats: Record<string, unknown>;
  last_error: string | null;
}

export interface UsageStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_response_time: number;
  most_popular_styles: string[];
  user_count: number;
}

export interface CacheStats {
  enabled: boolean;
  size: number;
  max_size: number;
  hits: number;
  misses: number;
  hit_rate: number;
  evictions: number;
  ttl_seconds: number;
}

// --- Admin / B2B ---

export interface TenantCreate {
  name: string;
}

export interface TenantResponse {
  id: number;
  name: string;
  created_at: string;
  is_active: boolean;
}

export interface ApiKeyCreate {
  name?: string;
}

export interface ApiKeyResponseWithRaw {
  id: number;
  prefix: string;
  name: string | null;
  tenant_id: number;
  created_at: string;
  raw_key: string;
}

export interface ApiKeyResponse {
  id: number;
  prefix: string;
  name: string | null;
  tenant_id: number;
  is_active: boolean;
  created_at: string;
}
