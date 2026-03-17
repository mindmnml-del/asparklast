# Architecture Update Changelog — Character Lock Extension

> **Date:** 2026-03-11
> **Update Version:** v1.1 (Post-Review)
> **Input Sources:**
> - Claude Code Peer Review (`EXTENSION_BRAINSTORM_REVIEW.md`)
> - Genspark AI Independent Review
> - Live MCP DOM Inspection (ImageFX, Gemini Chat)
> **Affected Document:** `CHARACTER_LOCK_EXTENSION_ARCHITECTURE.md`

---

## Multi-Agent Reconciliation Debate

Before modifying the architecture document, each of the 10 findings was debated across three review sources. Below is the reconciliation record.

### Finding 1: ChatGPT Migration to Contenteditable

**Source:** Claude Code Review
**Claim:** ChatGPT `#prompt-textarea` is now a `<div contenteditable>`, not `<textarea>`.

> **Claude Code Review position:** Confirmed via GhostPrompt extension source code and multiple developer codebases. ProseMirror likely underlies it.
> **Genspark Review position:** Did not independently flag this. Assumed textarea per the original architecture doc.
> **Reconciliation:** Claude Code evidence is concrete (open-source repos confirm). **Accepted.** ChatGPT reclassified to Strategy B (contenteditable). Runtime element-type detection added as a safety net since OpenAI may revert.

---

### Finding 2: React _valueTracker Reset

**Source:** Claude Code Review
**Claim:** Strategy A missing `_valueTracker.setValue(lastValue)` reset — React silently discards events.

> **Claude Code Review position:** Well-documented via React Issue #11488. Canonical workaround requires explicit reset.
> **Genspark Review position:** Did not flag this specific issue but recommended "verifying React state sync."
> **Reconciliation:** **Accepted.** The fix is straightforward and low-risk. Added defensive null check (`if (tracker)`) for non-React textareas.

---

### Finding 3: Discord Slate.js Tiered Injection

**Source:** Claude Code Review
**Claim:** `execCommand('insertText')` does not reliably work with Slate.js. Need 4-tier fallback.

> **Claude Code Review position:** Slate maintains its own internal model. `execCommand` modifies DOM but not Slate's state. Confirmed via Slate discussions #5721, #5003.
> **Genspark Review position:** Flagged Discord injection as "high risk" but proposed only `beforeinput` event dispatch, not the full tiered approach.
> **Reconciliation:** **Accepted Claude Code's 4-tier approach** as it is more comprehensive. Tier order: execCommand → beforeinput → React fiber → clipboard. The Genspark `beforeinput` suggestion is incorporated as Tier 2.

---

### Finding 4: Clipboard Focus Timing

**Source:** Claude Code Review
**Claim:** `navigator.clipboard.writeText()` fails when popup steals document focus.

> **Claude Code Review position:** Popup must close before content script runs. Add `clipboardWrite` permission.
> **Genspark Review position:** Did not flag this.
> **Reconciliation:** **Accepted.** The popup `window.close()` before `executeScript()` pattern is the standard Chrome extension approach. Added to both manifest and popup injection flow.

---

### Finding 5: ImageFX Chip-Based Editor

**Source:** Live MCP DOM Inspection
**Claim:** ImageFX (labs.google/fx) uses a chip-based editor with BUTTON elements. The contenteditable div only appears after clicking a chip.

> **Claude Code Review position:** Did not inspect ImageFX (was not in original platform list).
> **Genspark Review position:** Did not inspect ImageFX.
> **MCP DOM Inspection finding:** Confirmed. The prompt area uses `<button>` elements wrapping chip content. Clicking a chip reveals a `div[contenteditable="true"][role="textbox"]`. Styled Components classes (`sc-` prefix) are unstable.
> **Reconciliation:** **Accepted as new intelligence.** Creates a new **Strategy C: Click-to-Activate** injection. The extension must programmatically click the chip area, wait for the contenteditable to appear, then inject via Strategy B. Added ImageFX to Platform Registry as 7th platform.

---

### Finding 6: Gemini Chat Uses Quill.js

**Source:** Live MCP DOM Inspection
**Claim:** Gemini Chat uses Quill.js (`div.ql-editor`), not Draft.js. Parent is Angular `<RICH-TEXTAREA>` custom element.

> **Claude Code Review position:** Assumed generic contenteditable. Identified Quill as a possibility but did not confirm.
> **Genspark Review position:** Did not inspect Gemini Chat DOM.
> **MCP DOM Inspection finding:** Confirmed. Selector is `div.ql-editor[contenteditable="true"]` inside `<RICH-TEXTAREA>`. `aria-label="Enter a prompt for Gemini"`.
> **Reconciliation:** **Accepted.** `execCommand('insertText')` has better compatibility with Quill.js than with Slate.js because Quill uses its own Delta format but does listen to DOM mutations for synchronization. Updated Platform Registry with verified selector and ARIA label. Added `ql-editor` to Gemini selector chain.

---

### Finding 7: Discord /imagine Prefix

**Source:** Genspark Review
**Claim:** Midjourney requires `/imagine` command prefix. Extension should auto-prepend it.

> **Claude Code Review position:** Did not address Midjourney command semantics.
> **Genspark Review position:** Recommended auto-prepending `/imagine prompt: ` when platform is Discord.
> **Reconciliation:** **Partially accepted.** Auto-prepending `/imagine` is useful UX but risky if the user is not in a Midjourney channel, or if they're using a different Discord bot. Resolution: Make this a toggle in settings (`autoMidjourneyPrefix: true`), default OFF. User can enable it. When enabled, prepend `/imagine prompt: ` before the character description. This avoids false positives in non-Midjourney Discord channels.

---

### Finding 8: Storage Restructuring

**Source:** Claude Code Review + Genspark Review
**Claim:** `chrome.storage.sync` 8KB per-item limit will break when characters array grows.

> **Claude Code Review position:** Store each character as `char_<uuid>` key with a `char_index` array.
> **Genspark Review position:** Flagged same issue, recommended identical per-key approach.
> **Reconciliation:** **Accepted (both sources agree).** New schema: `char_index` (array of UUIDs) + individual `char_<uuid>` keys. Also updates `canCreateCharacter()` to use the index key instead of loading all characters.

---

### Finding 9: Selector Self-Healing

**Source:** Claude Code Review
**Claim:** Hardcoded selectors are fragile. Need ordered fallback chains, Shadow DOM traversal, and hot-updatable config.

> **Claude Code Review position:** Implement `SELECTOR_CHAINS` per platform, `querySelectorDeep()` for Shadow DOM, `document.activeElement` as priority 1.
> **Genspark Review position:** Recommended "ARIA-first selectors" but did not design the full fallback architecture.
> **Reconciliation:** **Accepted Claude Code's full architecture.** The ordered fallback chain (activeElement → platform chain → Shadow DOM → generic heuristic) is comprehensive. Added `chrome.storage.local` for selector config hot-updates.

---

### Finding 10: build="" Edge Case in toPromptText()

**Source:** Genspark Review
**Claim:** If `character.build` is empty string `""`, the condition `character.build !== "average"` is `true`, causing an empty "build" entry in the output.

> **Claude Code Review position:** Did not flag this.
> **Genspark Review position:** Identified the bug. Fix: `const buildVal = character.build || "average"`.
> **Reconciliation:** **Accepted.** Simple defensive fix. Updated `toPromptText()` to normalize empty build to "average" before comparison.

---

## Summary of Changes Applied to Architecture Document

| # | Change | Section Modified | Source |
|---|--------|-----------------|--------|
| 1 | ChatGPT reclassified: textarea → contenteditable | §7 Platform Registry | Claude Code Review |
| 2 | Strategy A: added `_valueTracker` reset | §7 Injection Strategies | Claude Code Review |
| 3 | Discord: 4-tier Slate.js injection | §7 Injection Strategies | Claude Code Review |
| 4 | Clipboard: popup closes before injection | §7 Fallback, §10 Error Recovery | Claude Code Review |
| 5 | ImageFX added as 7th platform with Strategy C | §7 Platform Registry, §3 Manifest | MCP DOM Inspection |
| 6 | Gemini Chat: verified Quill.js selector | §7 Platform Registry | MCP DOM Inspection |
| 7 | Discord /imagine prefix toggle | §8 Popup UI, §4 Settings | Genspark Review |
| 8 | Storage: per-character keys | §4 Data Storage | Claude Code + Genspark |
| 9 | Selector fallback chain + Shadow DOM | §7 dom_heuristics.js | Claude Code Review |
| 10 | build="" bugfix in toPromptText() | §5 character_sheet.js | Genspark Review |
| 11 | `clipboardWrite` + ImageFX host permission | §3 Manifest V3 | Claude Code + MCP |
| 12 | Runtime element-type detection | §7 Injection Strategies | Claude Code Review |

---

## Architectural Decisions Record

### ADR-001: Runtime Element Detection vs Platform Mapping
**Decision:** Use runtime `detectElementType()` as primary strategy selector, with platform-specific overrides only for known edge cases (Discord Slate.js, ImageFX click-to-activate).
**Rationale:** Platforms change element types without notice (ChatGPT did exactly this). Runtime detection is self-healing.

### ADR-002: Strategy C (Click-to-Activate) Scope
**Decision:** Strategy C is currently ImageFX-specific. Do not generalize until a second platform requires it.
**Rationale:** Over-engineering the activation pattern for one platform adds complexity. If a second chip-based editor appears, refactor into a generic pattern.

### ADR-003: /imagine Prefix Default
**Decision:** Default OFF, user-enabled toggle.
**Rationale:** Auto-prepending in non-Midjourney Discord channels would corrupt the message. Opt-in is safer than opt-out.

### ADR-004: Storage Migration Path
**Decision:** New installations use per-character keys from day one. No migration code needed for v1.0.
**Rationale:** There are no existing users to migrate. The old schema was never shipped.
