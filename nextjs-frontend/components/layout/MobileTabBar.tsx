"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Sparkles, BookOpen, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const mobileNavItems = [
  { icon: Zap, label: "Generate", href: "/generate" },
  { icon: Sparkles, label: "Helios", href: "/helios" },
  { icon: BookOpen, label: "History", href: "/history" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export default function MobileTabBar() {
  const pathname = usePathname() ?? "";

  return (
    <nav
      className={cn(
        "md:hidden fixed bottom-0 left-0 right-0 z-50",
        "bg-[#0A0B0E]/90 backdrop-blur-xl",
        "border-t border-white/[0.06]",
        "flex items-center justify-around h-16 px-2"
      )}
    >
      {mobileNavItems.map((item) => {
        const isActive = pathname.startsWith(item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-1 py-2 px-3 rounded-lg",
              "text-muted-foreground transition-colors",
              isActive && "text-[var(--personality-primary)]"
            )}
          >
            <Icon className="h-5 w-5" />
            <span className="text-[10px] font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
