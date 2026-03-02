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
  const { isAuthenticated, user, setUser, clearAuth } = useAuthStore();

  const { data, error } = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    enabled: isAuthenticated && !user,
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
