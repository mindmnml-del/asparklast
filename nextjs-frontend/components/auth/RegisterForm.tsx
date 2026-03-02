"use client";

import { useState, useMemo, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { Loader2, AlertCircle, Sparkles, Check, X } from "lucide-react";

/** Client-side validation mirroring backend AuthManager.validate_password_strength */
function validatePassword(password: string) {
  return {
    minLength: password.length >= 8,
    hasUpper: /[A-Z]/.test(password),
    hasLower: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };
}

const PASSWORD_RULES = [
  { key: "minLength", label: "8+ characters" },
  { key: "hasUpper", label: "Uppercase" },
  { key: "hasLower", label: "Lowercase" },
  { key: "hasNumber", label: "Number" },
  { key: "hasSpecial", label: "Special char" },
] as const;

export default function RegisterForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const { register, isRegistering, registerError } = useAuth();

  const passwordChecks = useMemo(() => validatePassword(password), [password]);
  const isPasswordValid = Object.values(passwordChecks).every(Boolean);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !isPasswordValid) return;
    register({
      email: email.trim(),
      password,
      full_name: fullName.trim() || undefined,
    });
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
          Create your account
        </h2>
        <p className="text-sm text-muted-foreground">
          Start creating with 3 free Sparks and 6 AI personalities
        </p>
      </div>

      {/* Error banner */}
      {registerError && (
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg border p-3",
            "border-red-500/30 bg-red-500/10 text-red-300 text-sm"
          )}
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{registerError.detail || "Registration failed"}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="fullName">Name (optional)</Label>
          <Input
            id="fullName"
            type="text"
            placeholder="Your name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            disabled={isRegistering}
            autoComplete="name"
            className="bg-[#111318] border-white/[0.06]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="reg-email">Email</Label>
          <Input
            id="reg-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isRegistering}
            required
            autoComplete="email"
            className="bg-[#111318] border-white/[0.06]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="reg-password">Password</Label>
          <Input
            id="reg-password"
            type="password"
            placeholder="Create a strong password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isRegistering}
            required
            autoComplete="new-password"
            className="bg-[#111318] border-white/[0.06]"
          />

          {/* Password strength indicators */}
          {password.length > 0 && (
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1">
              {PASSWORD_RULES.map(({ key, label }) => {
                const passed = passwordChecks[key];
                return (
                  <div key={key} className="flex items-center gap-1.5 text-xs">
                    {passed ? (
                      <Check className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <X className="h-3 w-3 text-muted-foreground/50" />
                    )}
                    <span
                      className={
                        passed
                          ? "text-emerald-400"
                          : "text-muted-foreground/50"
                      }
                    >
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <Button
          type="submit"
          disabled={isRegistering || !email.trim() || !isPasswordValid}
          className={cn(
            "w-full",
            "bg-[var(--personality-primary)] text-[#0A0B0E]",
            "hover:opacity-90 font-semibold"
          )}
        >
          {isRegistering ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Creating account...
            </>
          ) : (
            "Create Account"
          )}
        </Button>
      </form>

      {/* Footer */}
      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/login"
          className="text-[var(--personality-primary)] hover:underline font-medium"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
