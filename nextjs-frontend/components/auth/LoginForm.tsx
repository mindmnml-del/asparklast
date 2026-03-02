"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { Loader2, AlertCircle, Sparkles } from "lucide-react";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoggingIn, loginError } = useAuth();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    login({ email: email.trim(), password });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 mb-6">
          <Sparkles className="h-6 w-6 text-[var(--personality-primary)]" />
          <span className="text-xl font-semibold lg:hidden">AISpark Studio</span>
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Welcome back
        </h2>
        <p className="text-sm text-muted-foreground">
          Sign in to your account to continue creating
        </p>
      </div>

      {/* Error banner */}
      {loginError && (
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg border p-3",
            "border-red-500/30 bg-red-500/10 text-red-300 text-sm"
          )}
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{loginError.detail || "Invalid credentials"}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoggingIn}
            required
            autoComplete="email"
            className="bg-[#111318] border-white/[0.06]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoggingIn}
            required
            autoComplete="current-password"
            className="bg-[#111318] border-white/[0.06]"
          />
        </div>

        <Button
          type="submit"
          disabled={isLoggingIn || !email.trim() || !password}
          className={cn(
            "w-full",
            "bg-[var(--personality-primary)] text-[#0A0B0E]",
            "hover:opacity-90 font-semibold"
          )}
        >
          {isLoggingIn ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </Button>
      </form>

      {/* Footer */}
      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="text-[var(--personality-primary)] hover:underline font-medium"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
