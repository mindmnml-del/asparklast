"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Bell, LogOut, User } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Topbar() {
  const { isAuthenticated, credits, user } = useAuthStore();
  const { logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [dropdownOpen]);

  const userInitial =
    user?.full_name?.[0]?.toUpperCase() ??
    user?.email?.[0]?.toUpperCase() ??
    "U";

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 h-16",
        "bg-[#0A0B0E]/80 backdrop-blur-xl",
        "border-b border-white/[0.06]",
        "flex items-center justify-between px-6",
        "md:pl-[calc(72px+1.5rem)]"
      )}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-foreground tracking-tight">
          AISpark Studio
        </span>
      </div>

      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            {/* Credits Orb */}
            <div
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full",
                "bg-[var(--personality-glow)] border border-[var(--personality-primary)]/30",
                "text-sm font-medium text-[var(--personality-primary)]",
                "transition-shadow duration-300",
                "hover:shadow-[0_0_16px_var(--personality-glow)]"
              )}
            >
              <span className="text-xs animate-pulse">&#x2B22;</span>
              <span>{credits} Sparks</span>
            </div>

            {/* Notifications */}
            <button
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
            </button>

            {/* Avatar + Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen((prev) => !prev)}
                className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center",
                  "bg-[var(--personality-primary)]/20 border border-[var(--personality-primary)]/30",
                  "transition-colors hover:bg-[var(--personality-primary)]/30"
                )}
                aria-label="User menu"
              >
                <span className="text-sm font-medium text-[var(--personality-primary)]">
                  {userInitial}
                </span>
              </button>

              {dropdownOpen && (
                <div
                  className={cn(
                    "absolute right-0 top-full mt-2 w-56 py-2",
                    "bg-[#1A1D26] border border-white/[0.06] rounded-lg shadow-xl",
                    "animate-in fade-in slide-in-from-top-2 duration-200"
                  )}
                >
                  <div className="px-3 py-2 border-b border-white/[0.06]">
                    <p className="text-sm font-medium text-foreground truncate">
                      {user?.full_name ?? "User"}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {user?.email}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                    }}
                    className={cn(
                      "flex items-center gap-2 w-full px-3 py-2 mt-1",
                      "text-sm text-muted-foreground",
                      "hover:text-foreground hover:bg-white/[0.04] transition-colors"
                    )}
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <Button asChild variant="ghost" size="sm">
            <Link href="/login" className="text-[var(--personality-primary)]">
              <User className="h-4 w-4 mr-2" />
              Sign In
            </Link>
          </Button>
        )}
      </div>
    </header>
  );
}
