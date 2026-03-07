// Shared mock data for E2E tests — shapes match lib/types/api.ts

export const mockUser = {
  id: 1,
  email: "test@aispark.studio",
  full_name: "Test User",
  is_active: true,
  credits: 50,
  created_at: "2026-01-01T00:00:00Z",
};

export const mockToken = {
  access_token: "mock-jwt-token-abc123",
  token_type: "bearer",
};

export const mockAIResponse = {
  structuredPrompt: {
    subject: "A lone astronaut floating in deep space",
    setting: "Vast cosmic nebula with purple and blue hues",
    lighting: "Bioluminescent glow from distant stars",
    composition: "Wide angle, centered subject with rule of thirds",
    styleAndMedium: "Cinematic, photorealistic digital art",
    technicalDetails: "8K resolution, volumetric lighting, depth of field",
    mood: "Awe-inspiring solitude and wonder",
  },
  paragraphPrompt:
    "A lone astronaut floating gracefully in deep space, surrounded by a vast cosmic nebula awash in purple and blue hues. Bioluminescent glow from distant stars illuminates the scene with ethereal light. Shot in wide angle with centered subject following the rule of thirds. Cinematic, photorealistic digital art rendered at 8K resolution with volumetric lighting and depth of field. The mood conveys awe-inspiring solitude and wonder.",
  negativePrompt:
    "blurry, low quality, distorted, watermark, text, logo, cartoon, anime",
  tool: "midjourney",
  type: "image",
  id: 42,
  created_at: "2026-03-04T12:00:00Z",
};

export const mockCharacter = {
  name: "Elena Voss",
  character_id: "char-001",
  description: "A cyberpunk detective with augmented eyes",
  gender: "female" as const,
  age_range: "young adult (20-35)" as const,
  ethnicity: "Eastern European",
  skin_tone: "fair",
  face_shape: "angular",
  eye_color: "cybernetic blue",
  eye_shape: "almond",
  eyebrow_style: "arched",
  nose_shape: "straight",
  lip_shape: "thin",
  hair_color: "silver-white",
  hair_style: "asymmetric bob",
  hair_length: "medium",
  facial_hair: "none",
  height: "170cm",
  build: "athletic" as const,
  distinctive_features: ["cybernetic eye implant", "scar on left cheek"],
  clothing_style: "tech-noir",
  typical_outfit: "Black synth-leather jacket, tactical vest",
  accessories: ["neural interface headband", "holographic wrist display"],
  color_palette: ["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
  personality_traits: ["analytical", "resourceful"],
  mannerisms: ["adjusts neural interface when thinking"],
  voice_characteristics: "low, measured cadence",
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-03-01T08:00:00Z",
  version: "1.0",
  tags: ["cyberpunk", "detective"],
  reference_images: [],
  times_used: 12,
  last_used: "2026-03-01T08:00:00Z",
  successful_generations: 10,
  entity_type: "person" as const,
};

export const mockCharacterList = {
  success: true,
  characters: [mockCharacter],
  total: 1,
};

export const mockCriticAnalysis = {
  overall_score: 82,
  category_scores: {
    clarity: 85,
    specificity: 78,
    creativity: 90,
    technical_accuracy: 75,
  },
  assessment:
    "Strong cinematic prompt with vivid imagery. Could benefit from more specific technical details.",
  strengths: [
    "Vivid color description",
    "Clear compositional direction",
    "Strong mood conveyance",
  ],
  weaknesses: [
    "Missing camera lens specification",
    "Lighting could be more precise",
  ],
  top_suggestion:
    "Add specific camera lens (e.g., 35mm) and film grain type for enhanced photorealism.",
  improved_prompt:
    "A lone astronaut floating gracefully in deep space, captured with a 35mm wide-angle lens. Surrounded by a vast cosmic nebula awash in purple and blue hues with fine film grain texture.",
};

export const mockExtractionResponse = {
  success: true,
  extracted: {
    is_character: true,
    name: "Astronaut",
    description: "A lone astronaut floating in deep space",
    entity_type: "person" as const,
    gender: "unspecified" as const,
    build: "average" as const,
    distinctive_features: ["space suit", "reflective visor"],
  },
  is_character: true,
};
