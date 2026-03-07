"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateCharacter } from "@/lib/hooks/useCharacters";
import { cn } from "@/lib/utils";
import type { GenderType, AgeRange, BuildType, EntityType } from "@/lib/types/api";

const GENDER_OPTIONS: GenderType[] = [
  "male",
  "female",
  "non-binary",
  "unspecified",
];

const AGE_OPTIONS: AgeRange[] = [
  "child (5-12)",
  "teenager (13-19)",
  "young adult (20-35)",
  "middle-aged (36-55)",
  "senior (55+)",
];

const BUILD_OPTIONS: BuildType[] = [
  "slim",
  "athletic",
  "average",
  "muscular",
  "curvy",
  "heavy-set",
];

const ENTITY_TYPE_OPTIONS: EntityType[] = [
  "person",
  "environment",
  "object",
  "creature",
];

export default function CreateCharacterPage() {
  const router = useRouter();
  const createMutation = useCreateCharacter();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entityType, setEntityType] = useState<EntityType>("person");
  const [gender, setGender] = useState<GenderType>("unspecified");
  const [ageRange, setAgeRange] = useState<AgeRange>("young adult (20-35)");
  const [build, setBuild] = useState<BuildType>("average");
  const [lighting, setLighting] = useState("");
  const [atmosphere, setAtmosphere] = useState("");
  const [timeOfDay, setTimeOfDay] = useState("");
  const [architectureStyle, setArchitectureStyle] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload: Record<string, unknown> = {
      name: name.trim(),
      description: description.trim(),
      entity_type: entityType,
    };

    if (entityType === "person" || entityType === "creature") {
      payload.gender = gender;
      payload.age_range = ageRange;
      payload.build = build;
    } else if (entityType === "environment") {
      payload.lighting = lighting.trim();
      payload.atmosphere = atmosphere.trim();
      payload.time_of_day = timeOfDay.trim();
      payload.architecture_style = architectureStyle.trim();
    }

    createMutation.mutate(payload, {
      onSuccess: () => router.push("/characters"),
    });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/characters">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Create Character
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Define a character for visual consistency across generations
          </p>
        </div>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className={cn(
          "space-y-5 rounded-xl p-6",
          "bg-[#1A1D26] border border-white/[0.06]"
        )}
      >
        <div className="space-y-2">
          <Label>Entity Type</Label>
          <Select value={entityType} onValueChange={(v) => setEntityType(v as EntityType)}>
            <SelectTrigger className="bg-[#0A0B0E] border-white/[0.06]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#1A1D26] border-white/[0.06]">
              {ENTITY_TYPE_OPTIONS.map((opt) => (
                <SelectItem key={opt} value={opt} className="capitalize">
                  {opt}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Character name"
            required
            className="bg-[#0A0B0E] border-white/[0.06]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief character description..."
            rows={3}
            className="resize-none bg-[#0A0B0E] border-white/[0.06]"
          />
        </div>

        {/* Person / Creature fields */}
        {(entityType === "person" || entityType === "creature") && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Gender</Label>
              <Select value={gender} onValueChange={(v) => setGender(v as GenderType)}>
                <SelectTrigger className="bg-[#0A0B0E] border-white/[0.06]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1D26] border-white/[0.06]">
                  {GENDER_OPTIONS.map((opt) => (
                    <SelectItem key={opt} value={opt} className="capitalize">
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Age Range</Label>
              <Select value={ageRange} onValueChange={(v) => setAgeRange(v as AgeRange)}>
                <SelectTrigger className="bg-[#0A0B0E] border-white/[0.06]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1D26] border-white/[0.06]">
                  {AGE_OPTIONS.map((opt) => (
                    <SelectItem key={opt} value={opt}>
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Build</Label>
              <Select value={build} onValueChange={(v) => setBuild(v as BuildType)}>
                <SelectTrigger className="bg-[#0A0B0E] border-white/[0.06]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1D26] border-white/[0.06]">
                  {BUILD_OPTIONS.map((opt) => (
                    <SelectItem key={opt} value={opt} className="capitalize">
                      {opt}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {/* Environment fields */}
        {entityType === "environment" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="lighting">Lighting</Label>
              <Input
                id="lighting"
                value={lighting}
                onChange={(e) => setLighting(e.target.value)}
                placeholder="e.g. soft golden hour"
                className="bg-[#0A0B0E] border-white/[0.06]"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="atmosphere">Atmosphere</Label>
              <Input
                id="atmosphere"
                value={atmosphere}
                onChange={(e) => setAtmosphere(e.target.value)}
                placeholder="e.g. misty, ethereal"
                className="bg-[#0A0B0E] border-white/[0.06]"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="time_of_day">Time of Day</Label>
              <Input
                id="time_of_day"
                value={timeOfDay}
                onChange={(e) => setTimeOfDay(e.target.value)}
                placeholder="e.g. twilight"
                className="bg-[#0A0B0E] border-white/[0.06]"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="arch_style">Architecture Style</Label>
              <Input
                id="arch_style"
                value={architectureStyle}
                onChange={(e) => setArchitectureStyle(e.target.value)}
                placeholder="e.g. gothic, brutalist"
                className="bg-[#0A0B0E] border-white/[0.06]"
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-3 pt-2">
          <Button
            type="submit"
            disabled={!name.trim() || createMutation.isPending}
            className="bg-[var(--personality-primary)] text-[#0A0B0E] hover:opacity-90 font-semibold"
          >
            {createMutation.isPending ? "Creating..." : "Create Character"}
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/characters">Cancel</Link>
          </Button>
        </div>
      </form>
    </div>
  );
}
