"use client";

import { useEffect } from "react";
import { useGenerationStore } from "@/store/generationStore";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PROGRESS_PHASES = [
  { maxSeconds: 3, message: "Initializing Helios personality..." },
  { maxSeconds: 8, message: "Searching Vertex AI knowledge base..." },
  { maxSeconds: 15, message: "Analyzing prompt structure..." },
  { maxSeconds: 22, message: "Generating creative variations..." },
  { maxSeconds: 28, message: "Applying personality signature..." },
  { maxSeconds: 35, message: "Finalizing and quality-checking..." },
] as const;

export default function GenerationProgress() {
  const { isGenerating, elapsedSeconds, tick, cancelGeneration } =
    useGenerationStore();

  useEffect(() => {
    if (!isGenerating) return;

    const intervalId = setInterval(() => {
      tick();
    }, 1000);

    return () => clearInterval(intervalId);
  }, [isGenerating, tick]);

  const currentPhase =
    PROGRESS_PHASES.find((phase) => elapsedSeconds <= phase.maxSeconds) ??
    PROGRESS_PHASES[PROGRESS_PHASES.length - 1];

  const progressPercent = Math.min((elapsedSeconds / 35) * 95, 95);

  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <p
        className={cn(
          "font-mono text-sm text-[var(--personality-primary)] animate-pulse"
        )}
      >
        {currentPhase.message}
      </p>

      <div className="w-full max-w-md">
        <Progress
          value={progressPercent}
          className="h-1.5 bg-[var(--personality-glow)]"
        />
      </div>

      <span className="text-xs text-muted-foreground">{elapsedSeconds}s</span>

      <Button
        variant="ghost"
        size="sm"
        onClick={cancelGeneration}
        className="text-muted-foreground hover:text-red-400"
      >
        Cancel
      </Button>
    </div>
  );
}
