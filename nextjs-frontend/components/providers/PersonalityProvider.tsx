"use client";

import { useEffect, type ReactNode } from "react";
import { usePersonalityStore } from "@/store/personalityStore";

interface PersonalityProviderProps {
  children: ReactNode;
}

export default function PersonalityProvider({
  children,
}: PersonalityProviderProps) {
  const activePersonality = usePersonalityStore(
    (state) => state.activePersonality
  );

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-personality",
      activePersonality
    );
    document.documentElement.classList.add("dark");
  }, [activePersonality]);

  return <>{children}</>;
}
