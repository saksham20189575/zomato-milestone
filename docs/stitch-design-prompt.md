# Google Stitch Design Prompt — Zomato AI Restaurant Recommendations

Copy everything below the line into Google Stitch.

---

## Prompt for Google Stitch

Design a modern, polished **web app UI** for an **AI-powered restaurant recommendation product** inspired by **Zomato**. The app helps users in **Bangalore** discover where to eat by combining structured filters with AI-generated rankings and explanations. Target: **desktop-first responsive web** (mobile-friendly). This is a **portfolio-quality consumer product**, not an admin dashboard.

### Product summary

**Name (working):** Zomato AI Recommendations / TasteFinder  
**One-liner:** “Tell us what you want — we filter real restaurants and AI explains your best matches.”  
**Core value:** Personalized, **explainable** picks (not just a filter list). Every result shows *why* it fits the user’s preferences.

**User flow:**
1. Land on home → see preference form  
2. Submit preferences → **loading state** (2–15 seconds while AI ranks)  
3. See **optional AI summary** + **ranked restaurant cards** (top 1–20)  
4. Handle **empty results**, **errors**, and **degraded AI** gracefully  

No login, no cart, no booking — **discovery only** for MVP.

---

### Brand & visual direction

- **Inspiration:** Zomato’s warmth and food-forward energy — appetizing, trustworthy, urban India context  
- **Mood:** Friendly, confident, slightly premium; avoid generic “AI purple gradient” clichés  
- **Color:** Primary accent in **Zomato-adjacent red/coral** (#E23744 family) with neutral backgrounds (off-white / warm gray), strong contrast for accessibility  
- **Typography:** Clean sans-serif (e.g. Inter, DM Sans, or similar); clear hierarchy for restaurant names vs metadata  
- **Imagery:** Use **food/restaurant placeholder imagery** on cards where helpful; locality context (Bangalore neighbourhoods) can appear as subtle chips or map-pin motifs — **no real map required** for MVP  
- **AI touch:** Small “AI explained” badge or sparkle icon on explanation blocks — subtle, not gimmicky  

---

### Screens to design

#### Screen 1 — Home / Search preferences (default)

**Header**
- Logo + product name  
- Short subtitle: “Personalized picks from real Zomato data — filtered by you, ranked by AI”  

**Preference form** (card or panel layout, 2-column on desktop, stacked on mobile)

| Field | Control type | Notes |
|-------|--------------|-------|
| **Location (area)** | Searchable **dropdown** | ~90 Bangalore neighbourhoods: Indiranagar, Bellandur, BTM, Koramangala 5th Block, HSR, Whitefield, etc. Show map-pin icon. |
| **Budget** | Segmented control or dropdown | Options: **Low** · **Medium** · **High** (₹ for two implied) |
| **Cuisine** | Text input with suggestions | Placeholder: “Italian, Chinese, North Indian…” |
| **Minimum rating** | Slider 0.0–5.0 (step 0.5) | Show star icon + numeric value |
| **Additional preferences** | Multi-line text (optional) | Placeholder: “family-friendly, quick service, outdoor seating” |
| **Number of results** | Stepper or compact select | 1–20, default 5 |

**Primary CTA:** Full-width button — **“Get recommendations”**  

**Empty / idle state below form:** Light illustration or icon + “Set your preferences and we’ll find the best spots for you.”

---

#### Screen 2 — Loading

After submit:
- Disable form / show overlay  
- **Skeleton cards** (3–5 placeholders) OR centered loader with copy: “Finding and ranking restaurants…”  
- Optional progress hint: “Filtering matches → Asking AI → Preparing your list”  
- Do **not** use a blank white screen  

---

#### Screen 3 — Results (success)

**Section A — AI summary (optional)**  
- Highlighted banner/card at top when present  
- Example copy: “Five strong Italian options in Indiranagar within a medium budget, including family-friendly spots.”  

**Section B — Recommendation cards (vertical list or responsive grid)**  
Design a **reusable Restaurant Recommendation Card** with:

| Element | Content |
|---------|---------|
| Rank badge | `#1`, `#2`, … prominent but not overwhelming |
| Restaurant name | H2/H3 weight |
| Location | Subtitle — full address string e.g. “Bangalore, Indiranagar” |
| Rating | Star + numeric (e.g. 4.5) |
| Cost | “₹800 for two” |
| Cuisine | Tags/chips (e.g. Italian, Continental) |
| **AI explanation** | Distinct block — label “Why we picked this” with 2–4 lines of natural language; visually separate from metadata (soft background, left border, or quote style) |
| Budget band | Optional chip: Low / Medium / High |

**Card interaction:** Hover elevation on desktop; entire card readable without expand for MVP. Optional “Read more” if explanation is long (max-height + expand).

**Section C — Search details (collapsible footer)**  
- “Search details” accordion: candidates considered, filter time, AI time — secondary/muted typography  

Show **5 cards** in the mockup (ranks 1–5).

---

#### Screen 4 — Empty results

Friendly empty state when filters match nothing:
- Icon (plate/search)  
- Headline: “No restaurants match”  
- Body: “Try relaxing your area, cuisine, minimum rating, or budget.”  
- Secondary button: “Adjust filters” (scrolls to form)  

---

#### Screen 5 — Degraded AI (fallback)

When AI ranking fails but rule-based results exist:
- **Non-blocking alert** above cards (amber/warning style): “AI ranking unavailable — showing top-rated matches from your filters.”  
- Results cards still shown (same layout as Screen 3)  

---

#### Screen 6 — Error states

Design compact variants for:
- **Validation errors** — inline under fields (empty location/cuisine)  
- **System error** — “Something went wrong. Check your connection and try again.” + Retry  
- **Data not loaded** — setup banner: “Restaurant data unavailable. Run ingestion first.” (developer/setup; can be minimal)  

---

### Component library to include

- Primary / secondary buttons  
- Searchable select (location)  
- Budget segmented control  
- Star rating slider  
- Cuisine text field + chip suggestions  
- Restaurant recommendation card (default + hover)  
- AI summary banner  
- Warning / info / error alerts  
- Skeleton loaders  
- Empty state illustration block  
- Collapsible “Search details” panel  
- Rank badge (#1 gold accent optional for #1 only)  

---

### Content & sample data (use in mocks)

**Sample preferences:** Indiranagar · Medium budget · Italian · Min rating 4.0 · “family-friendly, quick service” · 5 results  

**Sample restaurants for cards:**

1. **#1 — Truffles** — Bangalore, Indiranagar · 4.6 ★ · ₹1,200 for two · Italian, Cafe · *“Highly rated Italian with a relaxed vibe; fits your medium budget and family-friendly ask.”*  
2. **#2 — Toit** — Bangalore, Indiranagar · 4.4 ★ · ₹1,500 for two · Italian, Pizza · *“Popular brewpub with strong Italian menu; great for groups.”*  
3. **#3 — Little Italy** — Bangalore, Indiranagar · 4.3 ★ · ₹900 for two · Italian · *“Dedicated Italian spot within budget with consistent ratings.”*  

---

### UX principles (must follow)

1. **Scannable results** — User decides where to eat in &lt;10 seconds per card  
2. **Explainability first** — AI explanation is as important as rating/cost  
3. **Trust** — Copy reinforces “real dataset, not invented restaurants”  
4. **Accessibility** — WCAG-friendly contrast, focus states, touch targets ≥44px on mobile  
5. **Performance perception** — Loading skeletons, never frozen UI  

---

### Out of scope (do not design)

- User accounts / login  
- Cart, checkout, table booking  
- Live maps / turn-by-turn  
- Restaurant detail page / menus  
- Chat-style multi-turn conversation  
- Dark mode optional (nice-to-have only if time permits)  

---

### Technical handoff notes (for developers)

- UI will be implemented in **React** (preferred) or refined **Streamlit** — design as **standard HTML/CSS component structure**  
- Form maps to API fields: `location`, `budget` (low|medium|high), `cuisine`, `min_rating`, `additional_preferences`, `top_k`  
- Results map to: `summary`, `recommendations[]` with `rank`, `restaurant{name, location, cuisines[], rating, estimated_cost, budget_band}`, `explanation`  
- Currency: **INR (₹)**  
- Location dropdown is **neighbourhood/area**, not free-text city  

---

### Deliverables requested from Stitch

1. **Home + preference form** (desktop + mobile frame)  
2. **Loading state**  
3. **Results page** with summary + 3–5 recommendation cards  
4. **Empty state** + **fallback warning** variant  
5. **Component spec** — colors, type scale, spacing, corner radius, shadows  
6. Export-friendly layout suitable for handoff to React/Tailwind implementation  

Make the design feel like a **real Zomato-inspired product** someone would demo in a portfolio — polished, warm, and focused on helping users choose where to eat tonight.
