"use client";

import { Flame, Zap, Waves, Target, Palette, Brain } from "lucide-react";
import { usePersonalityStore } from "@/store/personalityStore";
import { cn } from "@/lib/utils";
import type { PersonalityType } from "@/lib/types/api";

const personalities: Array<{
  type: PersonalityType;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}> = [
  { type: "prometheus", icon: Flame, label: "Prometheus" },
  { type: "zeus", icon: Zap, label: "Zeus" },
  { type: "poseidon", icon: Waves, label: "Poseidon" },
  { type: "artemis", icon: Target, label: "Artemis" },
  { type: "dionysus", icon: Palette, label: "Dionysus" },
  { type: "athena", icon: Brain, label: "Athena" },
];

export default function PersonalitySelector() {
  const { activePersonality, setPersonality } = usePersonalityStore();

  return (
    <div className="flex items-center justify-center gap-2">
      {personalities.map(({ type, icon: Icon, label }) => {
        const isActive = activePersonality === type;
        return (
          <button
            key={type}
            onClick={() => setPersonality(type)}
            aria-label={`Select ${label} personality`}
            aria-pressed={isActive}
            className={cn(
              "flex flex-col items-center gap-1 px-3 py-2 rounded-xl",
              "transition-all duration-200",
              isActive
                ? "text-[var(--personality-primary)] bg-[var(--personality-glow)] ring-1 ring-[var(--personality-primary)]/30 shadow-[0_0_12px_var(--personality-glow)]"
                : "text-muted-foreground hover:text-foreground hover:scale-110"
            )}
          >
            <Icon className="h-6 w-6" />
            <span className="text-[10px] font-medium leading-none">
              {label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
