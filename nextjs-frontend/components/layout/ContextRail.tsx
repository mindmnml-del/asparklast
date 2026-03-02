"use client";

import { useState } from "react";
import { PanelRightClose, PanelRightOpen } from "lucide-react";
import { usePersonalityStore } from "@/store/personalityStore";
import { cn } from "@/lib/utils";

export default function ContextRail() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const activePersonality = usePersonalityStore(
    (state) => state.activePersonality
  );

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col shrink-0",
        "bg-[#111318]/60 backdrop-blur-xl",
        "border-l border-white/[0.06]",
        "transition-all duration-300 ease-in-out",
        isCollapsed ? "w-12" : "w-80"
      )}
    >
      <div className="flex items-center justify-end p-3">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            "p-1.5 rounded-lg",
            "text-muted-foreground hover:text-foreground transition-colors"
          )}
          aria-label={
            isCollapsed ? "Expand context rail" : "Collapse context rail"
          }
        >
          {isCollapsed ? (
            <PanelRightOpen className="h-4 w-4" />
          ) : (
            <PanelRightClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-4 pt-0 space-y-6 overflow-y-auto">
          <section>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Active Personality
            </h3>
            <div
              className={cn(
                "inline-flex items-center gap-2 px-3 py-1.5 rounded-full",
                "bg-[var(--personality-glow)] border border-[var(--personality-primary)]/30"
              )}
            >
              <span className="h-2 w-2 rounded-full bg-[var(--personality-primary)]" />
              <span className="text-sm font-medium text-[var(--personality-primary)] capitalize">
                {activePersonality}
              </span>
            </div>
          </section>

          <section>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Locked Character
            </h3>
            <p className="text-sm text-muted-foreground">
              No character locked
            </p>
          </section>

          <section>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Last Prompt
            </h3>
            <p className="text-sm text-muted-foreground italic">
              No recent prompt
            </p>
          </section>

          <section>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Critic Score
            </h3>
            <p className="text-sm text-muted-foreground">&mdash;</p>
          </section>

          <section>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Credits Used
            </h3>
            <p className="text-sm text-muted-foreground">0 this session</p>
          </section>
        </div>
      )}
    </aside>
  );
}
