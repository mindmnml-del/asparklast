"use client";

import { useState, useCallback, type KeyboardEvent } from "react";
import { useGeneration } from "@/lib/hooks/useGeneration";
import { useGenerationStore } from "@/store/generationStore";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Copy, RotateCcw, AlertTriangle, Hexagon, MessageSquareWarning } from "lucide-react";
import { useCharacterStore } from "@/store/characterStore";
import { useCritic } from "@/lib/hooks/useCritic";
import CriticPanel from "@/components/critic/CriticPanel";
import type { GenerationRequest } from "@/lib/types/api";

const PROMPT_TYPES = ["image", "video", "universal"] as const;
type PromptType = (typeof PROMPT_TYPES)[number];

export default function GenerationForm() {
  const [promptText, setPromptText] = useState("");
  const [selectedType, setSelectedType] = useState<PromptType>("image");
  const [ragEnabled, setRagEnabled] = useState(true);
  const [copied, setCopied] = useState(false);

  const { mutate, data, reset } = useGeneration();
  const { isGenerating, error, isCreditsError } = useGenerationStore();
  const getCharacterPromptContext = useCharacterStore(
    (s) => s.getCharacterPromptContext
  );
  const criticMutation = useCritic();

  const handleSubmit = useCallback(() => {
    if (!promptText.trim() || isGenerating) return;

    const charContext = getCharacterPromptContext();
    const finalPrompt = charContext
      ? `[Character: ${charContext}]\n\n${promptText.trim()}`
      : promptText.trim();

    const request: GenerationRequest = {
      prompt: finalPrompt,
      type: selectedType,
      rag_enabled: ragEnabled,
    };

    mutate(request);
  }, [promptText, selectedType, ragEnabled, isGenerating, mutate, getCharacterPromptContext]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const handleCopy = useCallback(async () => {
    if (!data?.paragraphPrompt) return;
    await navigator.clipboard.writeText(data.paragraphPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [data]);

  const handleNewGeneration = useCallback(() => {
    reset();
    criticMutation.reset();
    setPromptText("");
    setCopied(false);
  }, [reset, criticMutation]);

  const handleCritique = useCallback(() => {
    if (!data?.paragraphPrompt) return;

    const analysisTypeMap = {
      image: "photo",
      video: "video",
      universal: "both",
    } as const;

    criticMutation.mutate({
      prompt: data.paragraphPrompt,
      negative_prompt: data.negativePrompt || undefined,
      analysis_type: analysisTypeMap[selectedType],
    });
  }, [data, selectedType, criticMutation]);

  const handleApplyImproved = useCallback(
    (improvedPrompt: string) => {
      setPromptText(improvedPrompt);
      criticMutation.reset();
      reset();
    },
    [criticMutation, reset]
  );

  const handleDismissCritic = useCallback(() => {
    criticMutation.reset();
  }, [criticMutation]);

  return (
    <div className="space-y-4">
      {/* Textarea */}
      <Textarea
        value={promptText}
        onChange={(e) => setPromptText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe your creative vision..."
        rows={5}
        disabled={isGenerating}
        className={cn(
          "resize-none bg-[#111318] border-white/[0.06]",
          "focus:border-[var(--personality-primary)]/50",
          "placeholder:text-muted-foreground/50",
          "text-base leading-relaxed"
        )}
      />

      {/* Controls row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Type selector */}
        <div className="flex rounded-lg border border-white/[0.06] overflow-hidden">
          {PROMPT_TYPES.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              disabled={isGenerating}
              className={cn(
                "px-3 py-1.5 text-xs font-medium capitalize transition-colors",
                selectedType === type
                  ? "bg-[var(--personality-glow)] text-[var(--personality-primary)]"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {type}
            </button>
          ))}
        </div>

        {/* RAG toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={ragEnabled}
            onChange={(e) => setRagEnabled(e.target.checked)}
            disabled={isGenerating}
            className="accent-[var(--personality-primary)]"
          />
          <span className="text-xs text-muted-foreground">
            RAG Knowledge Base
          </span>
        </label>

        {/* Submit button */}
        <Button
          onClick={handleSubmit}
          disabled={!promptText.trim() || isGenerating}
          className={cn(
            "ml-auto",
            "bg-[var(--personality-primary)] text-[#0A0B0E]",
            "hover:opacity-90 font-semibold"
          )}
        >
          <Hexagon className="h-4 w-4 mr-2" />
          Generate — 1 Spark
        </Button>
      </div>

      <p className="text-[11px] text-muted-foreground/50">
        Ctrl+Enter to generate
      </p>

      {/* Error banner */}
      {error && (
        <div
          className={cn(
            "flex items-start gap-3 rounded-lg border p-4",
            isCreditsError
              ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
              : "border-red-500/30 bg-red-500/10 text-red-300"
          )}
        >
          <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p>{error}</p>
            {isCreditsError && (
              <p className="mt-1 text-xs opacity-75">
                Your prompt has been saved. Get more Sparks to continue
                generating.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {data && !isGenerating && (
        <div className="space-y-4 pt-2">
          <div className="rounded-lg border border-white/[0.06] bg-[#111318] p-5">
            <div className="flex items-center justify-between mb-3">
              <Badge
                variant="outline"
                className="text-[var(--personality-primary)] border-[var(--personality-primary)]/30"
              >
                Generated Prompt
              </Badge>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Copy className="h-4 w-4 mr-1" />
                  {copied ? "Copied!" : "Copy"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCritique}
                  disabled={criticMutation.isPending}
                  className="text-muted-foreground hover:text-[var(--personality-primary)]"
                >
                  <MessageSquareWarning className="h-4 w-4 mr-1" />
                  {criticMutation.isPending ? "Analyzing..." : "Get Critique"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNewGeneration}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <RotateCcw className="h-4 w-4 mr-1" />
                  New
                </Button>
              </div>
            </div>

            <p className="font-serif text-base leading-relaxed text-foreground/90">
              {data.paragraphPrompt}
            </p>
          </div>

          {/* Structured prompt details */}
          {data.structuredPrompt && (
            <details className="rounded-lg border border-white/[0.06] bg-[#111318]">
              <summary className="px-4 py-3 text-sm text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
                Structured Prompt Details
              </summary>
              <div className="px-4 pb-4 grid gap-2">
                {Object.entries(data.structuredPrompt).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-xs font-mono text-[var(--personality-primary)] min-w-[120px] capitalize">
                      {key}:
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </details>
          )}

          {/* Negative prompt */}
          {data.negativePrompt && (
            <div className="rounded-lg border border-white/[0.06] bg-[#111318] px-4 py-3">
              <p className="text-xs font-mono text-muted-foreground">
                <span className="text-red-400">Negative:</span>{" "}
                {data.negativePrompt}
              </p>
            </div>
          )}

          {/* Critic Panel */}
          {(criticMutation.data || criticMutation.isPending || criticMutation.error) && (
            <CriticPanel
              analysis={criticMutation.data}
              isPending={criticMutation.isPending}
              error={criticMutation.error}
              onApplyImproved={handleApplyImproved}
              onDismiss={handleDismissCritic}
            />
          )}
        </div>
      )}
    </div>
  );
}
