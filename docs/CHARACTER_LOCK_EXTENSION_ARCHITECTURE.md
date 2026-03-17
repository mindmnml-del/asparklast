# Character Lock Chrome Extension — Architecture Document

> **Date:** 2026-03-11 (Updated: 2026-03-11 v1.1)
> **Author:** Nika Bokuchava
> **Source:** NotebookLM Architecture Sessions + Claude Validation + Multi-Source Review
> **Status:** Ready for Implementation (Post-Review)
> **Purpose:** Load into NotebookLM as source for code generation and task management
> **Review Sources:** Claude Code Peer Review, Genspark AI Review, Live MCP DOM Inspection
> **Changelog:** See `ARCHITECTURE_UPDATE_CHANGELOG.md` for detailed change rationale

---

## 1. Product Overview

### What It Does

Chrome Extension that stores character visual profiles and auto-injects them into AI image generation platform prompt fields with one click. Solves character consistency problem across multi-scene AI image generation WITHOUT LoRA training or manual re-specification.

### Validated Assumptions

- **Prompt injection works.** Tested on Imagen 3 across 3 different scenes (cyberpunk city, medieval tavern, space station). Same character remained recognizable in all three. Visual proof exists.
- **Market demand confirmed.** Reddit threads with 84+ upvotes, Upwork job postings at $25-50/hr for character consistency work, /r/aitubers creators spending 3 months solving this problem manually.
- **Standalone B2B API window is closed.** Segmind, Leonardo AI, Runway Gen-4, LTX Studio already offer character consistency features. Chrome extension is the correct distribution path.

### Business Model

- **Free tier:** 3 character profiles
- **Pro tier:** Unlimited characters, $5-10/month via ExtensionPay (Stripe wrapper, no backend needed)
- **Target users:** AI image/video creators on Midjourney, Leonardo AI, Gemini/Imagen

---

## 2. File Structure

```
character-lock-ext/
├── manifest.json
├── content/
│   ├── platform_detector.js    # Detects which platform user is on
│   ├── dom_heuristics.js       # Finds prompt input fields (ARIA/placeholder-based)
│   └── injector.js             # Text injection logic (handles React/Vue state)
├── core/
│   ├── character_sheet.js      # Port of Python character_lock.py to JavaScript
│   └── prompt_truncator.js     # Tiered truncation for Imagen 480-token limit
├── popup/
│   ├── index.html              # Extension popup UI
│   ├── ui.js                   # Character CRUD, Quick Create, Inject button
│   └── styles.css
├── tests/
│   ├── character_sheet.test.js # Vitest unit tests for to_prompt_text()
│   ├── mocks/                  # Mock HTML pages mimicking platform DOMs
│   └── injection.spec.js       # Playwright integration tests
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

**Design decision:** Modular over monolithic. When Discord changes DOM, only `dom_heuristics.js` needs updating — `character_sheet.js` stays untouched.

---

## 3. Manifest V3

```json
{
  "manifest_version": 3,
  "name": "Character Lock",
  "version": "1.0.0",
  "description": "Visual character consistency for AI image generation",
  "permissions": [
    "storage",
    "activeTab",
    "scripting",
    "clipboardWrite"
  ],
  "host_permissions": [
    "*://*.discord.com/*",
    "*://app.leonardo.ai/*",
    "*://chatgpt.com/*",
    "*://*.midjourney.com/*",
    "*://aistudio.google.com/*",
    "*://gemini.google.com/*",
    "*://labs.google/*"
  ],
  "action": {
    "default_popup": "popup/index.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

**Design decision:** Dynamic injection via `chrome.scripting.executeScript` from popup (Lazy Evaluation) instead of static `content_scripts` (Eager Loading). Code only runs when user clicks "Inject", saving memory and avoiding Chrome Store review delays from broad permissions.

**v1.1 changes:**
- Added `clipboardWrite` permission — required for reliable clipboard fallback when popup steals focus. *(Source: Claude Code Review)*
- Added `*://labs.google/*` host permission — ImageFX platform support. *(Source: MCP DOM Inspection)*

---

## 4. Data Storage

### Schema (chrome.storage.sync) — Per-Character Keys

> **v1.1 CHANGE:** Restructured from single `characters` array to per-character keys.
> **Reason:** `chrome.storage.sync` has an 8KB per-item limit. A single array of 50+ characters (~1.5KB each = 75KB) would exceed this limit and silently fail.
> *(Source: Claude Code Review + Genspark Review — both independently identified this)*

```json
{
  "char_index": ["char_abc123", "char_def456"],

  "char_abc123": {
    "id": "char_abc123",
    "name": "Cyberpunk Detective",
    "createdAt": "2026-03-11T10:00:00Z",
    "attributes": {
      "description": "A confident journalist in her early thirties",
      "gender": "female",
      "age_range": "young adult (20-35)",
      "ethnicity": "Mediterranean",
      "skin_tone": "olive",
      "face_shape": "oval",
      "eye_color": "dark brown",
      "eye_shape": "almond",
      "nose_shape": "straight",
      "lip_shape": "full",
      "hair_color": "dark auburn",
      "hair_style": "wavy",
      "hair_length": "shoulder-length",
      "facial_hair": "",
      "height": "average",
      "build": "slim",
      "distinctive_features": ["small mole near left eyebrow", "dimpled chin"],
      "clothing_style": "",
      "typical_outfit": "navy blazer over white blouse, dark jeans",
      "accessories": ["thin gold necklace", "leather watch"]
    },
    "compiled_prompt": "A confident journalist in her early thirties. female, young adult (20-35), Mediterranean ethnicity, olive skin. oval face, almond dark brown eyes, straight nose, full lips. dark auburn hair wavy shoulder-length. slim build. distinctive features: small mole near left eyebrow, dimpled chin. wearing navy blazer over white blouse, dark jeans. accessories: thin gold necklace, leather watch."
  },

  "subscription": {
    "isPro": false
  },
  "settings": {
    "autoInject": false,
    "defaultPlatform": "general",
    "autoMidjourneyPrefix": false
  }
}
```

**Design decision:** `chrome.storage.sync` over `chrome.storage.local` or IndexedDB. Sync stores data on user's Google account — characters survive device changes.

**Storage math:** Each character is ~1-2KB. The `char_index` key is ~50 bytes per character. Per-character keys stay well under the 8KB per-item limit. Total 100KB limit supports 50+ characters comfortably.

**v1.1 additions:**
- `autoMidjourneyPrefix` setting — when enabled, prepends `/imagine prompt: ` on Discord. Default OFF to avoid corruption in non-Midjourney channels. *(Source: Genspark Review)*
- Removed `characterCount` from subscription (derive from `char_index.length` instead).

---

## 5. Core Module: character_sheet.js

Direct port of Python `character_lock.py` `CharacterSheet` dataclass and `to_prompt_text()` method.

### CharacterSheet Fields

```javascript
const CHARACTER_FIELDS = {
  // Basic Identity
  name: "",
  description: "",

  // Physical
  gender: "unspecified",    // male | female | non-binary | unspecified
  age_range: "",            // child (5-12) | teenager (13-19) | young adult (20-35) | middle-aged (36-55) | senior (55+)
  ethnicity: "",
  skin_tone: "",

  // Facial
  face_shape: "",           // oval | round | square | heart | angular
  eye_color: "",
  eye_shape: "",            // almond | round | hooded | upturned
  nose_shape: "",           // straight | button | aquiline | broad
  lip_shape: "",            // full | thin | heart-shaped | wide

  // Hair
  hair_color: "",
  hair_style: "",           // wavy | straight | curly | short cropped
  hair_length: "",          // shoulder-length | waist-length | pixie | very short
  facial_hair: "",          // beard | mustache | goatee | clean-shaven

  // Body
  height: "",               // tall | average | short | petite
  build: "average",         // slim | athletic | average | muscular | curvy | heavy-set
  distinctive_features: [], // scars, tattoos, piercings, etc.

  // Style
  clothing_style: "",
  typical_outfit: "",
  accessories: [],
  color_palette: []
};
```

### to_prompt_text() Method

```javascript
function toPromptText(character) {
  const parts = [];

  if (character.description) parts.push(character.description);

  // Physical characteristics
  const physical = [];
  if (character.gender !== "unspecified") physical.push(character.gender);
  if (character.age_range) physical.push(character.age_range);
  if (character.ethnicity) physical.push(`${character.ethnicity} ethnicity`);
  if (character.skin_tone) physical.push(`${character.skin_tone} skin`);
  if (physical.length) parts.push(physical.join(", "));

  // Facial features
  const face = [];
  if (character.face_shape) face.push(`${character.face_shape} face`);
  if (character.eye_color && character.eye_shape) {
    face.push(`${character.eye_shape} ${character.eye_color} eyes`);
  } else if (character.eye_color) {
    face.push(`${character.eye_color} eyes`);
  }
  if (character.nose_shape) face.push(`${character.nose_shape} nose`);
  if (character.lip_shape) face.push(`${character.lip_shape} lips`);
  if (face.length) parts.push(face.join(", "));

  // Hair
  const hair = [];
  if (character.hair_color) hair.push(`${character.hair_color} hair`);
  if (character.hair_style) hair.push(character.hair_style);
  if (character.hair_length) hair.push(character.hair_length);
  if (character.facial_hair && character.facial_hair !== "clean-shaven") {
    hair.push(`with ${character.facial_hair}`);
  }
  if (hair.length) parts.push(hair.join(" "));

  // Body
  // v1.1 FIX: Normalize empty build to "average" before comparison (Source: Genspark Review)
  const buildVal = character.build || "average";
  if (character.height || buildVal !== "average") {
    const body = [];
    if (character.height) body.push(`${character.height} height`);
    if (buildVal !== "average") body.push(`${buildVal} build`);
    parts.push(body.join(", "));
  }

  // Distinctive features
  if (character.distinctive_features.length) {
    parts.push(`distinctive features: ${character.distinctive_features.join(", ")}`);
  }

  // Clothing
  if (character.typical_outfit) {
    parts.push(`wearing ${character.typical_outfit}`);
  } else if (character.clothing_style) {
    parts.push(`dressed in ${character.clothing_style} style`);
  }

  // Accessories
  if (character.accessories.length) {
    parts.push(`accessories: ${character.accessories.join(", ")}`);
  }

  return parts.join(". ") + ".";
}
```

---

## 6. Prompt Truncation (Tiered Rendering)

Imagen 3 has a 480-token limit (~350 words). Full 30+ attribute prompt may exceed this.

### Tier System

| Tier | Fields | Priority | Cut When |
|------|--------|----------|----------|
| **Tier 1: Core Identity** | description, gender, age_range, distinctive_features | NEVER cut | — |
| **Tier 2: Visual Context** | hair (color/style/length), eye_color, face_shape, skin_tone, typical_outfit, build | Cut last resort | > 350 words |
| **Tier 3: Granular Detail** | accessories, color_palette, nose_shape, lip_shape, eye_shape, ethnicity, height | Cut first | > 250 words |

### Algorithm

```javascript
function toPromptTextForPlatform(character, platform) {
  // Imagen 3 token limit applies to Gemini, AI Studio, and ImageFX
  if (platform === "gemini" || platform === "aistudio" || platform === "imagefx") {
    const full = toPromptText(character);
    const wordCount = full.split(/\s+/).length;

    if (wordCount <= 350) return full;

    // Cut Tier 3 first
    const tier1and2 = toPromptTextTier1and2(character);
    if (tier1and2.split(/\s+/).length <= 350) return tier1and2;

    // Emergency: Core Identity only
    return toPromptTextTier1(character);
  }

  return toPromptText(character); // No limit for other platforms
}
```

---

## 7. Platform Detection and Injection

> **v1.1 MAJOR REVISION:** This section has been substantially rewritten based on three independent review sources. See `ARCHITECTURE_UPDATE_CHANGELOG.md` for detailed rationale.

### Platform Registry (7 Platforms)

| Platform | Hostname | Primary Selector | Verified? | Element Type | Strategy | Notes |
|----------|----------|-----------------|-----------|--------------|----------|-------|
| **Discord (Midjourney)** | `discord.com` | `div[role="textbox"][data-slate-editor="true"]` | Partial | contenteditable (Slate.js) | B-Slate (4-tier) | Custom Slate.js fork. ARIA `aria-label^="Message"`. *(Source: Claude Code Review)* |
| **Leonardo AI** | `app.leonardo.ai` | `textarea[placeholder*="prompt" i]` | Estimated | textarea (React) | A | Standard React controlled textarea. *(Source: Original doc)* |
| **ChatGPT / DALL-E** | `chatgpt.com` | `#prompt-textarea` | Confirmed | contenteditable div | B | **CHANGED from textarea.** Now `<div contenteditable>` with same ID. Possibly ProseMirror. *(Source: Claude Code Review)* |
| **Stable Diffusion WebUI** | localhost / various | `#txt2img_prompt textarea` | Confirmed | textarea (Gradio) | A | Gradio generates stable IDs. *(Source: Original doc)* |
| **Google AI Studio** | `aistudio.google.com` | `textarea[aria-label*="prompt" i]` | Estimated | textarea (Angular) | A | May use Shadow DOM (Angular/Lit components). *(Source: Claude Code Review)* |
| **Google Gemini Chat** | `gemini.google.com` | `div.ql-editor[contenteditable="true"]` | **DOM-Verified** | contenteditable (Quill.js) | B | Inside `<RICH-TEXTAREA>` Angular component. `aria-label="Enter a prompt for Gemini"`. *(Source: MCP DOM Inspection)* |
| **Google ImageFX** | `labs.google` | `div[contenteditable="true"][role="textbox"]` | **DOM-Verified** | contenteditable (chip-based) | C | Chip-based editor. Requires click-to-activate before injection. Styled Components (`sc-` prefix). *(Source: MCP DOM Inspection)* |

### Selector Fallback Chains (Self-Healing Architecture)

> **v1.1 ADDITION.** Hardcoded selectors are fragile. Each platform has an ordered fallback chain. Chains are stored in code but can be overridden via `chrome.storage.local` for hot-updates without Chrome Web Store review. *(Source: Claude Code Review)*

```javascript
// dom_heuristics.js
const SELECTOR_CHAINS = {
  discord: [
    '[data-slate-editor="true"]',
    'div[role="textbox"][contenteditable="true"]',
    'div[role="textbox"][aria-label^="Message"]',
  ],
  chatgpt: [
    '#prompt-textarea',
    'div#prompt-textarea[contenteditable="true"]',
    'div[contenteditable="true"][role="textbox"]',
  ],
  leonardo: [
    'textarea[placeholder*="prompt" i]',
    'textarea[placeholder*="describe" i]',
    'textarea[aria-label*="prompt" i]',
  ],
  gemini: [
    'div.ql-editor[contenteditable="true"]',
    'rich-textarea div[contenteditable="true"][role="textbox"]',
    'div[contenteditable="true"][aria-label*="prompt" i]',
  ],
  aistudio: [
    'textarea[aria-label*="prompt" i]',
    'textarea[placeholder*="prompt" i]',
    'div[contenteditable="true"][role="textbox"]',
  ],
  imagefx: [
    'div[contenteditable="true"][role="textbox"]',
    'div[contenteditable="true"][aria-label*="prompt" i]',
  ],
  sdwebui: [
    '#txt2img_prompt textarea',
    'textarea[placeholder*="prompt" i]',
  ],
};
```

### Element Discovery Algorithm

```javascript
function findPromptInput(platform) {
  // Priority 1: User's focused element (most reliable, framework-agnostic)
  const active = document.activeElement;
  if (isValidTarget(active)) return active;

  // Priority 2: Platform-specific selector chain
  const chain = SELECTOR_CHAINS[platform] || [];
  for (const selector of chain) {
    const el = querySelectorDeep(selector); // handles Shadow DOM
    if (el && isVisible(el)) return el;
  }

  // Priority 3: Generic heuristic — find any visible textbox, score by size
  const candidates = document.querySelectorAll(
    '[role="textbox"][contenteditable="true"], textarea'
  );
  const scored = [...candidates]
    .filter(isVisible)
    .map(el => ({ el, score: el.getBoundingClientRect().width }))
    .sort((a, b) => b.score - a.score);

  return scored[0]?.el || null;
}

// Shadow DOM traversal for Google properties (Angular/Lit web components)
function querySelectorDeep(selector) {
  let el = document.querySelector(selector);
  if (el) return el;

  // Traverse open Shadow DOMs
  const allElements = document.querySelectorAll('*');
  for (const host of allElements) {
    if (host.shadowRoot) {
      el = host.shadowRoot.querySelector(selector);
      if (el) return el;
    }
  }
  return null;
}

function isVisible(el) {
  const rect = el.getBoundingClientRect();
  return rect.width > 50 && rect.height > 20 && el.offsetParent !== null;
}

function isValidTarget(el) {
  if (!el) return false;
  return (
    el.tagName === 'TEXTAREA' ||
    el.tagName === 'INPUT' ||
    el.contentEditable === 'true' ||
    el.getAttribute('role') === 'textbox'
  );
}
```

### Runtime Element Type Detection

> **v1.1 ADDITION.** Instead of hardcoding platform→strategy mappings, detect the element type at runtime. This is self-healing: if a platform changes from textarea to contenteditable (as ChatGPT did), the extension auto-adapts. *(Source: Claude Code Review)*

```javascript
function detectElementType(element) {
  if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
    return 'native-input';       // → Strategy A
  }
  if (element.contentEditable === 'true' || element.getAttribute('role') === 'textbox') {
    return 'contenteditable';    // → Strategy B or C
  }
  return 'unknown';              // → Clipboard fallback
}
```

### platform_detector.js

```javascript
function detectPlatform() {
  const host = window.location.hostname;

  if (host.includes("discord.com")) return "discord";
  if (host.includes("leonardo.ai")) return "leonardo";
  if (host.includes("chatgpt.com")) return "chatgpt";
  if (host.includes("aistudio.google.com")) return "aistudio";
  if (host.includes("gemini.google.com")) return "gemini";
  if (host === "labs.google") return "imagefx";
  if (host.includes("localhost") || host.includes("127.0.0.1")) return "sdwebui";

  return "unknown";
}
```

### injector.js — Three Injection Strategies + Tiered Discord Handling

#### Strategy A: textarea (Leonardo, AI Studio, SD WebUI)

> **v1.1 FIX:** Added `_valueTracker` reset. Without this, React silently discards the event because the tracked value already matches the DOM value. *(Source: Claude Code Review, React Issue #11488)*

```javascript
function injectIntoTextarea(element, text) {
  const currentValue = element.value || "";
  const newValue = currentValue + (currentValue ? " " : "") + text;

  // Step 1: Store old value for _valueTracker reset
  const lastValue = element.value;

  // Step 2: Use native setter to bypass React's property override
  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, "value"
  ).set;
  nativeSetter.call(element, newValue);

  // Step 3: Reset React's _valueTracker to old value (so React sees a diff)
  // This is an undocumented React internal — defensive null check required
  const tracker = element._valueTracker;
  if (tracker) {
    tracker.setValue(lastValue);
  }

  // Step 4: Event cascade for React/Vue/Svelte state sync
  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));

  return true;
}
```

#### Strategy B: contenteditable div (ChatGPT, Gemini Chat, generic)

> Works with Quill.js (Gemini), ProseMirror (ChatGPT), and generic contenteditable.
> `execCommand('insertText')` is deprecated in spec but no browser has a removal timeline. Risk: negligible. See `EXTENSION_BRAINSTORM_REVIEW.md` Section 5 for full deprecation analysis.

```javascript
function injectIntoContentEditable(element, text) {
  element.focus();

  // Move cursor to end
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(element);
  range.collapse(false); // collapse to end
  selection.removeAllRanges();
  selection.addRange(range);

  // Browser-native command — Quill.js and ProseMirror generally trust this
  const result = document.execCommand("insertText", false, " " + text);

  return result && element.textContent.includes(text);
}
```

#### Strategy B-Slate: Discord Tiered Injection (4-Level Fallback)

> **v1.1 ADDITION.** Discord uses a custom Slate.js fork. `execCommand` does not reliably sync with Slate's internal document model. This tiered approach attempts multiple injection methods before falling back to clipboard. *(Source: Claude Code Review, Slate discussions #5721 and #5003, BetterDiscord PR #948)*

```javascript
function injectIntoSlateEditor(element, text) {
  element.focus();

  // Move cursor to end
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(element);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);

  // Tier 1: Try execCommand (works in some Slate versions)
  const execResult = document.execCommand("insertText", false, " " + text);
  if (execResult && element.textContent.includes(text)) {
    return true;
  }

  // Tier 2: Try beforeinput event dispatch (Slate listens to these since PR #1232)
  const beforeInputEvent = new InputEvent("beforeinput", {
    bubbles: true,
    composed: true,
    cancelable: true,
    inputType: "insertText",
    data: " " + text,
  });
  element.dispatchEvent(beforeInputEvent);
  if (element.textContent.includes(text)) {
    return true;
  }

  // Tier 3: Try accessing Slate editor via React fiber internals
  try {
    const fiberKey = Object.keys(element).find(k => k.startsWith("__reactFiber"));
    if (fiberKey) {
      let fiber = element[fiberKey];
      while (fiber) {
        const editor = fiber.memoizedProps?.editor ||
                       fiber.memoizedProps?.node ||
                       fiber.stateNode?.editor;
        if (editor && typeof editor.insertText === "function") {
          editor.insertText(" " + text);
          return true;
        }
        fiber = fiber.return;
      }
    }
  } catch (e) {
    console.warn("[CharacterLock] Slate fiber access failed:", e.message);
  }

  // Tier 4: Signal failure — caller should use clipboard fallback
  return false;
}
```

#### Strategy C: Click-to-Activate (ImageFX)

> **v1.1 ADDITION.** ImageFX uses a chip-based prompt editor. The contenteditable div only appears after clicking a chip/button. Strategy C programmatically activates the editor, then delegates to Strategy B. *(Source: MCP DOM Inspection)*

```javascript
async function injectIntoChipEditor(element, text) {
  // Step 1: Find and click the chip area to activate the editor
  // ImageFX uses BUTTON elements as chips. Click the last one or the empty area.
  const chipArea = element.closest('[role="textbox"]') || element;
  chipArea.click();

  // Step 2: Wait for contenteditable to appear (chip editor is async)
  await new Promise(resolve => setTimeout(resolve, 200));

  // Step 3: Find the now-visible contenteditable div
  const editableDiv = chipArea.querySelector('[contenteditable="true"]')
    || document.querySelector('[contenteditable="true"][role="textbox"]');

  if (!editableDiv) {
    console.warn("[CharacterLock] ImageFX: contenteditable not found after click");
    return false;
  }

  // Step 4: Delegate to Strategy B (contenteditable injection)
  return injectIntoContentEditable(editableDiv, text);
}
```

#### Unified Injection Orchestrator

```javascript
async function inject(platform, text, settings) {
  // Prepend /imagine for Discord if setting enabled
  if (platform === "discord" && settings?.autoMidjourneyPrefix) {
    text = "/imagine prompt: " + text;
  }

  // Apply prompt truncation for Imagen-based platforms
  if (platform === "gemini" || platform === "aistudio" || platform === "imagefx") {
    text = toPromptTextForPlatform(text, platform);
  }

  const element = findPromptInput(platform);
  if (!element) {
    return fallbackClipboard(text);
  }

  const elementType = detectElementType(element);
  let success = false;

  // Strategy routing
  if (platform === "discord") {
    success = injectIntoSlateEditor(element, text);  // B-Slate (4-tier)
  } else if (platform === "imagefx") {
    success = await injectIntoChipEditor(element, text);  // C
  } else if (elementType === "native-input") {
    success = injectIntoTextarea(element, text);     // A
  } else if (elementType === "contenteditable") {
    success = injectIntoContentEditable(element, text); // B
  }

  if (!success) {
    return fallbackClipboard(text);
  }
  return true;
}
```

#### Fallback: Clipboard Copy

> **v1.1 FIX:** The popup must close BEFORE triggering injection to return focus to the page. `navigator.clipboard.writeText()` throws `DOMException: Document is not focused` if the popup is still open. *(Source: Claude Code Review)*

```javascript
async function fallbackClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    // Last resort: use deprecated execCommand in offscreen document
    console.warn("[CharacterLock] Clipboard API failed:", e.message);
    return false;
  }
  return false; // signals to UI: show "Copied to clipboard — paste manually" message
}
```

**Popup injection flow (focus-timing fix):**

```javascript
// In popup/ui.js — inject button handler
async function handleInject(characterPrompt) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  // Close popup FIRST to return focus to the page
  window.close();

  // executeScript runs from service worker context after popup closes
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: inject,
    args: [detectedPlatform, characterPrompt, userSettings],
  });
}
```

### Injection Engine Architecture (Visual)

```
┌────────────────────────────────────────┐
│  findPromptInput(platform)             │
│  (dom_heuristics.js)                   │
│                                        │
│  1. document.activeElement             │
│  2. Platform selector chain            │
│  3. Shadow DOM traversal               │
│  4. Generic heuristic (scored by size) │
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│  detectElementType(element)            │
│                                        │
│  <textarea> / <input> → 'native-input' │
│  contenteditable      → 'contenteditable'│
│  other                → 'unknown'      │
└──┬──────────┬──────────┬───────────────┘
   │          │          │
   ▼          ▼          ▼
┌────────┐ ┌──────────────────┐ ┌───────────────┐
│Strat A │ │ Strategy B       │ │ Platform-      │
│textarea│ │ contenteditable  │ │ Specific       │
│        │ │                  │ │                │
│Native  │ │ execCommand      │ │ B-Slate:       │
│setter +│ │ ('insertText')   │ │  4-tier Discord│
│_value- │ │                  │ │                │
│Tracker │ │ Works with:      │ │ C: ImageFX     │
│reset + │ │  Quill (Gemini)  │ │  Click-to-     │
│events  │ │  ProseMirror     │ │  Activate      │
│        │ │  (ChatGPT)       │ │                │
└───┬────┘ └────────┬─────────┘ └──────┬────────┘
    │               │                  │
    │ (on failure)  │ (on failure)     │ (on failure)
    ▼               ▼                  ▼
┌────────────────────────────────────────┐
│  Clipboard Fallback                    │
│  (popup closes first to return focus)  │
│                                        │
│  navigator.clipboard.writeText()       │
│  → Show "Copied to clipboard" message │
└────────────────────────────────────────┘
```

---

## 8. Popup UI

### Two Modes

**Quick Create (default):** 5 fields for 80% visual consistency.

| Field | Example | Why Critical |
|-------|---------|-------------|
| Subject/Archetype | Cyberpunk Detective | Primary identity anchor |
| Gender & Age | Female, 30s | Strongest visual differentiator |
| Distinctive Feature | Neon blue cybernetic left arm | Most memorable visual element |
| Clothing | Black tactical vest | Consistent across all scenes |
| Color Palette | Dark, neon blue accents | Unifies visual identity |

**Full Editor:** All 30+ fields for maximum consistency. Accessible via "Advanced" toggle.

### Settings Panel

> **v1.1 ADDITION.** *(Source: Genspark Review)*

| Setting | Default | Description |
|---------|---------|-------------|
| Auto-Inject | OFF | Automatically inject when page loads (post-MVP) |
| Default Platform | general | Pre-select platform for truncation |
| Midjourney /imagine Prefix | OFF | Auto-prepend `/imagine prompt: ` when injecting on Discord. Only enable if user primarily uses Midjourney. |

### Import from Prompt (Future Feature — Not MVP)

Client-side regex extraction for basic attributes. NOT reliable enough for MVP. Quick Create is sufficient for launch.

```javascript
// Post-MVP feature
function extractFromPrompt(promptText) {
  const features = {};
  if (/\b(male|man|boy)\b/i.test(promptText)) features.gender = "male";
  if (/\b(female|woman|girl)\b/i.test(promptText)) features.gender = "female";
  // ... more patterns
  return features; // Pre-fills UI, user confirms/edits
}
```

---

## 9. Freemium Gating

### Payment: ExtensionPay (No Backend Required)

```javascript
import ExtPay from "extpay";
const extpay = ExtPay("character-lock");

// Check subscription status
extpay.getUser().then(user => {
  if (user.paid) {
    chrome.storage.sync.set({ subscription: { isPro: true } });
  }
});
```

### Character Limit Enforcement

> **v1.1 UPDATED** to use `char_index` instead of loading all characters. *(Source: Storage restructuring)*

```javascript
function canCreateCharacter() {
  return new Promise(resolve => {
    chrome.storage.sync.get(["char_index", "subscription"], data => {
      const count = (data.char_index || []).length;
      const isPro = data.subscription?.isPro || false;
      resolve(isPro || count < 3);
    });
  });
}
```

**Known trade-off:** Client-side gating is bypassable via DevTools. Acceptable risk — 99% of target users (creators, not developers) won't attempt this.

---

## 10. Error Recovery

### Scenario 1: Selector fails (DOM changed)

> **v1.1 UPDATED:** Now uses the full fallback chain from `dom_heuristics.js`. *(Source: Claude Code Review)*

```
findPromptInput() attempts in order:
  1. document.activeElement (user may have cursor in input)
  2. Platform-specific selector chain (3 selectors per platform)
  3. Shadow DOM traversal (for Google Angular/Lit components)
  4. Generic heuristic: any visible [role="textbox"] or textarea, scored by width
  → If all fail → fallback to clipboard copy
    → Popup closes first (focus-timing fix)
    → Show message: "Auto-inject failed. Copied to clipboard — paste manually."
```

### Scenario 2: Injection succeeds but React state doesn't update

```
Strategy A (textarea): _valueTracker reset ensures React sees the diff.
Strategy B (contenteditable): execCommand is browser-native, generally trusted.
Strategy B-Slate (Discord): 4-tier fallback catches Slate sync failures.

If platform's submit button still disabled after all strategies:
  → Show popup message: "Text injected. Press Space once to activate the send button."
```

### Scenario 3: Multiple tabs open

```
chrome.scripting.executeScript uses target: { tabId: currentTab.id }
  → Injection always targets the tab where popup was opened
  → No cross-tab interference
```

### Scenario 4: ImageFX chip editor not activated

> **v1.1 ADDITION.** *(Source: MCP DOM Inspection)*

```
Strategy C: click-to-activate fires a click event, waits 200ms.
  → If contenteditable div does not appear → increase wait to 500ms, retry once
  → If still not found → clipboard fallback
```

### Scenario 5: Popup steals document focus

> **v1.1 ADDITION.** *(Source: Claude Code Review)*

```
Popup calls window.close() BEFORE chrome.scripting.executeScript.
  → Focus returns to page → clipboard API works
  → If clipboard still fails (e.g., iframe focus issues):
    → Show error: "Could not copy. Please copy manually from the popup."
```

---

## 11. Testing Strategy

### Unit Tests (Vitest)

Test `character_sheet.js` `toPromptText()`:
- All fields populated → correct formatted output
- Minimal fields (Quick Create 5) → valid output
- Empty fields → no trailing commas or empty sections
- Special characters in distinctive_features → properly escaped

### Integration Tests (Playwright)

- Load extension as unpacked in Chromium
- Create mock HTML pages mimicking each platform's DOM structure
- Test: selector finds input → injection succeeds → text appears in field
- Test: selector fails → clipboard fallback triggers

### Manual Testing Checklist (Pre-Release)

- [ ] Discord: Create character → Inject (4-tier Slate) → Send → Midjourney bot processes without error
- [ ] Discord: Enable /imagine prefix → Verify `/imagine prompt: ` is prepended
- [ ] Leonardo AI: Inject → Generate button becomes active → Image generates
- [ ] ChatGPT: Inject into contenteditable → Send button activates → Response received
- [ ] Gemini Chat: Inject into Quill.js editor → Image generates
- [ ] AI Studio: Inject into Imagen prompt → Image generates
- [ ] ImageFX: Click chip area → Inject after activation → Image generates
- [ ] Unknown site: Inject attempt → Clipboard fallback → "Copied" message shown
- [ ] Selector failure: All selectors return null → Clipboard fallback triggers
- [ ] Free tier: Create 3 characters → 4th blocked → Upgrade prompt shown
- [ ] Pro tier: ExtensionPay payment → Unlimited characters unlocked
- [ ] Build="" edge case: Character with empty build → No empty "build" text in output

---

## 12. Implementation Order

> **v1.1 UPDATED:** Phase 3 expanded to cover 3 injection strategies + 4-tier Discord handling. Phase 4 expanded to 7 platforms.

| Phase | Task | Exit Criterion |
|-------|------|---------------|
| **Phase 1** | `character_sheet.js` + `toPromptText()` (with build="" fix) + unit tests | All tests pass, output matches Python version, empty build handled |
| **Phase 2** | Popup UI (Quick Create + Full Editor + character CRUD + settings panel) | Can create/edit/delete characters, per-character storage keys work |
| **Phase 3** | Injection engine: Strategy A (textarea + _valueTracker) + Strategy B (contenteditable) + Strategy B-Slate (4-tier Discord) + Strategy C (ImageFX click-to-activate) + clipboard fallback (with focus-timing fix) | Works on Leonardo AI, ChatGPT, and Discord |
| **Phase 4** | `dom_heuristics.js` (selector chains + Shadow DOM) + `platform_detector.js` + all 7 platforms | Manual testing checklist passes for all 7 platforms |
| **Phase 5** | Prompt truncation for Gemini/Imagen/ImageFX | Tier system works, stays under 350 words |
| **Phase 6** | ExtensionPay integration + freemium gating (per-character key storage) | Payment flow works end-to-end |
| **Phase 7** | Chrome Web Store submission | Published and live |

---

## 13. Known Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Platform DOM changes break selectors | Extension stops working on that platform | **v1.1:** Ordered fallback chains (3 selectors/platform) + `document.activeElement` + Shadow DOM traversal + clipboard fallback + selector hot-update via `chrome.storage.local` |
| Chrome Web Store rejection | Can't distribute | Specific host_permissions (7 domains, not `<all_urls>`), clear privacy policy, `clipboardWrite` permission justified |
| Prompt injection approach becomes obsolete | Product loses value | Monitor IP-Adapter/LoRA adoption; pivot to reference image approach if needed |
| ExtensionPay service goes down | Can't process payments | Store `isPro` flag locally; payment failure doesn't revoke existing access |
| Google changes Gemini/AI Studio/ImageFX DOM | Injection fails on Google platforms | **v1.1:** Gemini selector DOM-verified (Quill.js). ImageFX DOM-verified (chip-based). AI Studio still estimated. Shadow DOM traversal handles Angular/Lit components |
| React `_valueTracker` internal API changes | Strategy A breaks for textarea platforms | **v1.1:** Defensive null check (`if (tracker)`). Monitor React release notes. Falls through to clipboard fallback |
| Discord Slate.js fork diverges | Discord-specific injection breaks | **v1.1:** 4-tier fallback (execCommand → beforeinput → React fiber → clipboard). At least one tier should work |
| `execCommand` eventually removed from browsers | Strategy B breaks for all contenteditable platforms | **v1.1:** No removal timeline exists. W3C maintaining separate spec. Risk: negligible for 2-3 years minimum |

---

## Appendix A: Proven Test Results

Three images generated with Character Lock `to_prompt_text()` output on Imagen 3:
- **Scenario 1:** Cyberpunk city, rain, neon reflections → Character recognizable
- **Scenario 2:** Medieval tavern, warm candlelight → Same character, different setting
- **Scenario 3:** Space station, zero gravity → Same character, extreme environment change

All three maintained: hair style (dark, shaved sides), cybernetic left arm (blue glow), nose piercing, facial scar, tactical vest, blue eyes. This validates the prompt injection approach.

---

## Appendix B: Competitive Context

- **Midjourney `--cref`:** Works but limited to Midjourney-generated images, no field-level control
- **Leonardo AI Character Reference:** Requires 15-30 training images, 45-90 min training time
- **Runway Gen-4:** Single reference image, no attribute-level customization
- **Character Lock Extension:** Zero training, field-level control, works across ALL platforms
