"use client";

import { useState } from "react";
import { Search, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ExportFormat } from "@/lib/api/history";

type FilterTab = "all" | "favorites";

interface HistoryControlsProps {
  search: string;
  onSearchChange: (value: string) => void;
  activeFilter: FilterTab;
  onFilterChange: (filter: FilterTab) => void;
  onExport: (format: ExportFormat) => void;
  isExporting: boolean;
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
  onExport,
  isExporting,
}: HistoryControlsProps) {
  const [exportFormat, setExportFormat] = useState<ExportFormat>("json");

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

      {/* Export controls */}
      <div className="flex items-center gap-2 sm:ml-auto">
        <Select
          value={exportFormat}
          onValueChange={(v) => setExportFormat(v as ExportFormat)}
        >
          <SelectTrigger className="w-[90px] h-9 bg-[#0A0B0E] border-white/[0.06] text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-[#1A1D26] border-white/[0.06]">
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="csv">CSV</SelectItem>
            <SelectItem value="txt">TXT</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onExport(exportFormat)}
          disabled={isExporting}
          className="border-white/[0.06] text-muted-foreground hover:text-foreground"
        >
          <Download className="h-3.5 w-3.5 mr-1.5" />
          {isExporting ? "Exporting..." : "Export"}
        </Button>
      </div>
    </div>
  );
}
