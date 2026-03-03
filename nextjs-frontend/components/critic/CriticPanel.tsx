"use client";

import { cn } from "@/lib/utils";
import ScoreRing from "@/components/critic/ScoreRing";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Check,
  X,
  Lightbulb,
  Wand2,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import type { CriticAnalysis } from "@/lib/types/api";
import type { ApiError } from "@/lib/api/client";

interface CriticPanelProps {
  analysis: CriticAnalysis | undefined;
  isPending: boolean;
  error: ApiError | null;
  onApplyImproved: (improvedPrompt: string) => void;
  onDismiss: () => void;
}

function formatCategoryName(key: string): string {
  return key
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getCategoryBarColor(score: number, max: number): string {
  const pct = (score / max) * 100;
  if (pct < 50) return "bg-red-500";
  if (pct < 80) return "bg-amber-500";
  return "bg-emerald-500";
}

export default function CriticPanel({
  analysis,
  isPending,
  error,
  onApplyImproved,
  onDismiss,
}: CriticPanelProps) {
  // Loading state
  if (isPending) {
    return (
      <div className="rounded-lg border border-white/[0.06] bg-[#111318] p-6 flex flex-col items-center gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--personality-primary)]" />
        <p className="text-sm text-[var(--personality-primary)] animate-pulse">
          Analyzing prompt quality...
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
        <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-red-300" />
        <div className="flex-1 text-sm text-red-300">
          <p>{error.detail || "Critic analysis failed. Please try again."}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="text-red-300 hover:text-red-200 shrink-0"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  // No data yet
  if (!analysis) return null;

  const categoryEntries = Object.entries(analysis.category_scores);

  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#1A1D26] p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Badge
          variant="outline"
          className="text-[var(--personality-primary)] border-[var(--personality-primary)]/30"
        >
          Critic Analysis
        </Badge>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="text-muted-foreground hover:text-foreground h-7 w-7 p-0"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Score + Assessment */}
      <div className="flex items-start gap-5">
        <ScoreRing score={analysis.overall_score} />
        <p className="text-sm text-foreground/80 leading-relaxed flex-1">
          {analysis.assessment}
        </p>
      </div>

      {/* Category Scores */}
      {categoryEntries.length > 0 && (
        <details className="rounded-lg border border-white/[0.06] bg-[#111318]">
          <summary className="px-4 py-3 text-sm text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
            Category Scores
          </summary>
          <div className="px-4 pb-4 space-y-2">
            {categoryEntries.map(([key, score]) => (
              <div key={key} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground min-w-[140px]">
                  {formatCategoryName(key)}
                </span>
                <div className="flex-1 h-1.5 rounded-full bg-white/[0.06]">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      getCategoryBarColor(score, 20)
                    )}
                    style={{ width: `${Math.min(100, (score / 20) * 100)}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-muted-foreground w-8 text-right">
                  {score}/20
                </span>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Strengths */}
        {analysis.strengths.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400/80">
              Strengths
            </p>
            <ul className="space-y-1.5">
              {analysis.strengths.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground/80">
                  <Check className="h-4 w-4 shrink-0 text-emerald-400 mt-0.5" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Weaknesses */}
        {analysis.weaknesses.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-red-400/80">
              Areas for Improvement
            </p>
            <ul className="space-y-1.5">
              {analysis.weaknesses.map((w, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground/80">
                  <X className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Top Suggestion */}
      {analysis.top_suggestion && (
        <div className="rounded-lg bg-[var(--personality-glow)] border border-[var(--personality-primary)]/20 p-4 flex gap-3">
          <Lightbulb className="h-5 w-5 shrink-0 text-[var(--personality-primary)] mt-0.5" />
          <p className="text-sm font-medium text-foreground/90">
            {analysis.top_suggestion}
          </p>
        </div>
      )}

      {/* Apply Improved Prompt */}
      {analysis.improved_prompt && (
        <Button
          onClick={() => onApplyImproved(analysis.improved_prompt!)}
          className={cn(
            "w-full",
            "bg-[var(--personality-primary)] text-[#0A0B0E]",
            "hover:opacity-90 font-semibold"
          )}
        >
          <Wand2 className="h-4 w-4 mr-2" />
          Apply Improved Prompt
        </Button>
      )}
    </div>
  );
}
