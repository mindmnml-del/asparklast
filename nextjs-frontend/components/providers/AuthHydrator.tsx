"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCurrentUser } from "@/lib/api/auth";
import { useAuthStore } from "@/store/authStore";

export default function AuthHydrator({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, setUser, clearAuth } = useAuthStore();

  // Always attempt hydration — the httpOnly cookie authenticates the request
  const { data, error } = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    enabled: !user,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    if (error) clearAuth();
  }, [error, clearAuth]);

  return <>{children}</>;
}
