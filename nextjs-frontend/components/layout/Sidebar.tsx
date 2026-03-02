"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Zap,
  Sparkles,
  Lock,
  BookOpen,
  Search,
  Download,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { icon: Zap, label: "Generate", href: "/generate" },
  { icon: Sparkles, label: "Helios", href: "/helios" },
  { icon: Lock, label: "Characters", href: "/characters" },
  { icon: BookOpen, label: "History", href: "/history" },
  { icon: Search, label: "Search", href: "/search" },
  { icon: Download, label: "Export", href: "/export" },
];

export default function Sidebar() {
  const [isExpanded, setIsExpanded] = useState(false);
  const pathname = usePathname() ?? "";

  return (
    <aside
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
      className={cn(
        "hidden md:flex flex-col h-screen fixed left-0 top-0 z-40",
        "bg-[#111318]/80 backdrop-blur-xl border-r border-white/[0.06]",
        "transition-all duration-300 ease-in-out",
        isExpanded ? "w-60" : "w-[72px]"
      )}
    >
      <nav className="flex-1 flex flex-col gap-1 px-3 pt-20">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg",
                "transition-colors duration-200",
                "text-muted-foreground hover:text-foreground",
                isActive &&
                  "text-[var(--personality-primary)] bg-[var(--personality-glow)]"
              )}
            >
              <Icon
                className={cn(
                  "h-5 w-5 shrink-0",
                  isActive && "text-[var(--personality-primary)]"
                )}
              />
              <span
                className={cn(
                  "text-sm font-medium whitespace-nowrap overflow-hidden",
                  "transition-opacity duration-300",
                  isExpanded ? "opacity-100" : "opacity-0 w-0"
                )}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-lg",
            "text-muted-foreground hover:text-foreground transition-colors",
            pathname === "/settings" &&
              "text-[var(--personality-primary)] bg-[var(--personality-glow)]"
          )}
        >
          <Settings className="h-5 w-5 shrink-0" />
          <span
            className={cn(
              "text-sm font-medium whitespace-nowrap overflow-hidden",
              "transition-opacity duration-300",
              isExpanded ? "opacity-100" : "opacity-0 w-0"
            )}
          >
            Settings
          </span>
        </Link>
      </div>
    </aside>
  );
}
