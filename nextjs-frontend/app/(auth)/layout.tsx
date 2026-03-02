import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0A0B0E]">
      {/* Left panel: branding — hidden on mobile */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--personality-glow)] via-transparent to-transparent opacity-40" />
        <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-[var(--personality-primary)]/5 blur-3xl" />
        <div className="absolute top-1/3 left-1/4 w-64 h-64 rounded-full bg-[var(--personality-secondary)]/5 blur-3xl" />

        {/* Logo */}
        <div className="relative z-10">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            AISpark Studio
          </h1>
        </div>

        {/* Tagline */}
        <div className="relative z-10 space-y-4">
          <blockquote className="text-lg font-medium text-foreground/80 leading-relaxed">
            &ldquo;Describe your vision. Helios will craft it.&rdquo;
          </blockquote>
          <p className="text-sm text-muted-foreground">
            AI-powered creative studio with 6 distinct creative personalities
          </p>
        </div>

        <div className="relative z-10" />
      </div>

      {/* Right panel: form */}
      <div className="flex flex-1 items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
