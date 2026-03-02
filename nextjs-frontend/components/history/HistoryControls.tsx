"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type FilterTab = "all" | "favorites";

interface HistoryControlsProps {
  search: string;
  onSearchChange: (value: string) => void;
  activeFilter: FilterTab;
  onFilterChange: (filter: FilterTab) => void;
}

const TABS: { value: FilterTab; label: string }[] = [
  { value: "all", label: "All" },
  { value: "favorites", label: "Favorites" },
];

export default function HistoryControls({
  search,
  onSearchChange,
  activeFilter,
  onFilterChange,
}: HistoryControlsProps) {
  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-start sm:items-center gap-3",
        "bg-[#111318]/80 backdrop-blur-xl",
        "border border-white/[0.06] rounded-lg p-3"
      )}
    >
      {/* Search */}
      <div className="relative flex-1 w-full sm:max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search prompts..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9 bg-[#0A0B0E] border-white/[0.06]"
        />
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 rounded-lg bg-[#0A0B0E] p-1">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onFilterChange(tab.value)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200",
              activeFilter === tab.value
                ? "bg-[var(--personality-glow)] text-[var(--personality-primary)]"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}
