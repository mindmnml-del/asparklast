"use client";

import { useState, type FormEvent } from "react";
import { Shield, Key, Plus, Copy, Building2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useCreateTenant,
  useTenantApiKeys,
  useCreateApiKey,
} from "@/lib/hooks/useAdmin";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export default function AdminPage() {
  // Admin key — stored only in local React state, never persisted
  const [adminKey, setAdminKey] = useState("");

  // Create Tenant form
  const [tenantName, setTenantName] = useState("");
  const createTenant = useCreateTenant(adminKey);

  // API Keys management
  const [tenantIdInput, setTenantIdInput] = useState("");
  const [activeTenantId, setActiveTenantId] = useState<number | null>(null);
  const apiKeysQuery = useTenantApiKeys(adminKey, activeTenantId);
  const createApiKey = useCreateApiKey(adminKey);

  // Raw key display (shown once after generation)
  const [rawKey, setRawKey] = useState<string | null>(null);

  const isAuthed = adminKey.length > 0;

  function handleCreateTenant(e: FormEvent) {
    e.preventDefault();
    if (!tenantName.trim()) return;
    createTenant.mutate(
      { name: tenantName.trim() },
      { onSuccess: () => setTenantName("") },
    );
  }

  function handleLoadKeys(e: FormEvent) {
    e.preventDefault();
    const id = parseInt(tenantIdInput, 10);
    if (isNaN(id) || id <= 0) {
      toast.error("Enter a valid tenant ID");
      return;
    }
    setRawKey(null);
    setActiveTenantId(id);
  }

  function handleGenerateKey() {
    if (activeTenantId === null) return;
    setRawKey(null);
    createApiKey.mutate(
      { tenantId: activeTenantId },
      { onSuccess: (resp) => setRawKey(resp.raw_key) },
    );
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Failed to copy");
    }
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
          <Shield className="h-6 w-6" />
          Admin Dashboard
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage B2B tenants and API keys
        </p>
      </div>

      {/* Admin Key Input */}
      <Card className="bg-[#111318] border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4" />
            Authentication
          </CardTitle>
          <CardDescription>
            Enter your Admin API Key to access management functions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end">
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="admin-key">Admin API Key</Label>
              <Input
                id="admin-key"
                type="password"
                placeholder="Enter admin key..."
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                className="bg-[#0D0F14] border-white/[0.06] focus:border-[var(--personality-primary)]/50"
              />
            </div>
            {isAuthed && (
              <Badge variant="outline" className="mb-1 border-green-500/30 text-green-400">
                Key Set
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Create Tenant */}
      <Card className={cn("bg-[#111318] border-white/[0.06]", !isAuthed && "opacity-50 pointer-events-none")}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Create New Tenant
          </CardTitle>
          <CardDescription>
            Register a new B2B organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateTenant} className="flex gap-3 items-end">
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="tenant-name">Organization Name</Label>
              <Input
                id="tenant-name"
                placeholder="Acme Corp"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                disabled={!isAuthed}
                className="bg-[#0D0F14] border-white/[0.06] focus:border-[var(--personality-primary)]/50"
              />
            </div>
            <Button
              type="submit"
              disabled={!isAuthed || createTenant.isPending || !tenantName.trim()}
            >
              <Plus className="h-4 w-4 mr-2" />
              {createTenant.isPending ? "Creating..." : "Create"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Manage API Keys */}
      <Card className={cn("bg-[#111318] border-white/[0.06]", !isAuthed && "opacity-50 pointer-events-none")}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4" />
            Manage API Keys
          </CardTitle>
          <CardDescription>
            View and generate API keys for a tenant
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Tenant ID input + Load */}
          <form onSubmit={handleLoadKeys} className="flex gap-3 items-end">
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="tenant-id">Tenant ID</Label>
              <Input
                id="tenant-id"
                type="number"
                placeholder="e.g. 1"
                min={1}
                value={tenantIdInput}
                onChange={(e) => setTenantIdInput(e.target.value)}
                disabled={!isAuthed}
                className="bg-[#0D0F14] border-white/[0.06] focus:border-[var(--personality-primary)]/50"
              />
            </div>
            <Button type="submit" variant="secondary" disabled={!isAuthed || !tenantIdInput}>
              Load Keys
            </Button>
          </form>

          {/* Raw Key Alert */}
          {rawKey && (
            <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-medium text-sm">
                <AlertTriangle className="h-4 w-4" />
                Save this key now — it will never be shown again
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm font-mono text-amber-200 bg-black/30 rounded px-3 py-2 break-all select-all">
                  {rawKey}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(rawKey)}
                  className="shrink-0"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Keys table */}
          {activeTenantId !== null && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-foreground">
                  Keys for Tenant #{activeTenantId}
                </h3>
                <Button
                  size="sm"
                  onClick={handleGenerateKey}
                  disabled={createApiKey.isPending}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  {createApiKey.isPending ? "Generating..." : "Generate New Key"}
                </Button>
              </div>

              {apiKeysQuery.isLoading ? (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  Loading keys...
                </div>
              ) : apiKeysQuery.isError ? (
                <div className="text-sm text-destructive py-4 text-center">
                  {apiKeysQuery.error?.message || "Failed to load keys"}
                </div>
              ) : apiKeysQuery.data && apiKeysQuery.data.length > 0 ? (
                <div className="rounded-lg border border-white/[0.06] overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                        <th className="text-left py-2 px-3 font-medium text-muted-foreground">Prefix</th>
                        <th className="text-left py-2 px-3 font-medium text-muted-foreground">Name</th>
                        <th className="text-left py-2 px-3 font-medium text-muted-foreground">Created</th>
                        <th className="text-left py-2 px-3 font-medium text-muted-foreground">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiKeysQuery.data.map((key) => (
                        <tr key={key.id} className="border-b border-white/[0.04] last:border-0">
                          <td className="py-2 px-3 font-mono text-xs">{key.prefix}</td>
                          <td className="py-2 px-3 text-muted-foreground">{key.name ?? "—"}</td>
                          <td className="py-2 px-3 text-muted-foreground">
                            {new Date(key.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-2 px-3">
                            <Badge
                              variant={key.is_active ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {key.is_active ? "Active" : "Revoked"}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground py-4 text-center">
                  No API keys found for this tenant
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
