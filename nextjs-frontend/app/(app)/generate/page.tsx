"use client";

import PersonalitySelector from "@/components/studio/PersonalitySelector";
import GenerationForm from "@/components/studio/GenerationForm";
import GenerationProgress from "@/components/studio/GenerationProgress";
import { useGenerationStore } from "@/store/generationStore";

export default function GeneratePage() {
  const isGenerating = useGenerationStore((s) => s.isGenerating);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">The Studio</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Describe your vision. Helios will craft it.
        </p>
      </div>

      <PersonalitySelector />

      {isGenerating && <GenerationProgress />}

      <GenerationForm />
    </div>
  );
}
