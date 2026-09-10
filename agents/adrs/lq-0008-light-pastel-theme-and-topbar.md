# ADR-lq-0008: Light pastel theme, topbar navigation, contained layout

## Status

Accepted 2026-09-10 by `lq` (owns the frontend half, ADR-sf-0005). Supersedes
the visual half of the design handoff; see Scope.

## Context

The design handoff (`design_handoff_algaewatch_villarrica/README.md`) specifies a
**dark** interface: black shell (`#000`), two blurred accent halos, a glass
surface (`backdrop-filter: blur(18px) saturate(140%)`) on every panel, saturated
"Apple system" accent colours, and a full-bleed three-band shell
(`height: 100vh; overflow: hidden`) with a segmented control for navigation.

The owner (`lq`) asked to move the frontend to a **lighter, calmer** direction:
light background, pastel palette, no fluorescent/neon colours, information
reorganised, real page margins instead of edge-to-edge, and navigation
segregated into a **topbar**. PR-4 requires handoff deviations to be recorded as
an ADR; this is that record. ADR-lq-0007 already covered the dark-theme risk
palette and glass reduction — this ADR extends and largely replaces it on the
visual layer.

The pitch is ~2026-09-10, so this was scoped as a **focused pass**, not a
per-view redesign.

## Decision

### D1 — Light pastel theme

`tokens.css` flips to a light semantic token set (variable names unchanged so
components keep working):

- Page `#F5F7FA`, cards `#FFFFFF`, ink `#24303F` / `#4A5766` / `#66727F`.
- Brand: muted periwinkle `#5B77C2` (`--color-accent-ink` `#43589A` for text).
- Status: pastel green `#5FA980` / amber `#D19A5C` (`#8A5A2B` for small text).
- Shadows: shallow flat-design scale (`0 1px 2–3px`), no glow.
- No `backdrop-filter` on content panels; the topbar keeps a light 8px blur only
  as a scroll-legibility scrim.
- Font moves to **Inter** (from the handoff's system stack), loaded from Google
  Fonts in `index.html`.

### D2 — Risk scale: light-mode pastel sequential ramp

The dark magma ramp from ADR-lq-0007 is replaced with a light-surface pastel
ramp sampled from `magma`'s warm end:

| Level | ADR-lq-0007 (dark) | Now (light) |
|---|---|---|
| MUY_BAJO | `#93318A` | `#EAC49B` |
| BAJO | `#D0466B` | `#E0A074` |
| MEDIO | `#F47355` | `#C9765A` |
| ALTO | `#FCAC3D` | `#A05445` |

Monotonic OKLCH lightness (0.84 → 0.76 → 0.65 → 0.53), single hue (~36°), worst
adjacent ΔE 8.5 (OKLab ×100) under normal / protan / deutan / tritan. Validated
with the dataviz skill's `validate_palette` in `--ordinal` mode against surface
`#F6F8FA`. `risk.js` adds an `ink` field per level — a darker step for small text
on white, since the ramp fill itself is a mark colour (chips, markers,
gradients), not body-text colour.

### D3 — Topbar navigation

The segmented control becomes a sticky topbar: brand + logo left, text nav tabs
(Mapa / Estaciones / Tendencias / Modelo) with an active/hover tint, live-status
+ pass date right. The time-window slider drops to a secondary bar under it.
Desktop keeps the topbar (owner's choice) rather than switching to a sidebar at
≥1024px.

### D4 — Contained, scrolling layout

The `height: 100vh; overflow: hidden` shell is dropped for a normal scrolling
page. A `.container` (`max-width: 1280px`, centred) with gutters that grow
16 → 28 → 44px by breakpoint replaces the edge-to-edge bands. The map view gets
an explicit height (`min(72vh, 680px)`) since the page now scrolls; the analytics
panel is a fixed 380px column beside it that stacks below the map under 900px.
The Modelo footer becomes a normal card in the flow.

### D5 — Logo

The topbar brand mark and favicon load from the site-root URL `/logo.png` (the
pastel lake + volcano illustration the owner supplied). The file lives under
`frontend/public/` and is **not committed yet** — the owner drops it in (see
that directory's README). `Header.jsx` renders an inline SVG fallback mark until
it exists, and the favicon 404s harmlessly.

## Scope

This is a focused pass. Done: tokens, shell/topbar/container structure, all
shared surfaces (cards, map chrome, popup, legend, AI panel, sparklines), the
risk ramp, per-component dark-colour cleanup. **Not** done: per-view information
re-architecture (the four views keep their existing structure), a real logo
asset, responsive QA below 768px, and a light/dark toggle (the dark theme is
gone, not switchable).

## Consequences

- The handoff and the code now disagree on the entire visual layer, not just two
  elements. Fidelity checks against the handoff's colour/effect/layout spec no
  longer apply; this ADR plus ADR-lq-0007 are the visual source of truth.
- The two mandated *texts* from the handoff are still honoured: the TRL-2 seal
  (BL-019) and the AI-panel disclaimer render unchanged.
- ADR 0003 (Leaflet) is unaffected — the map library did not change.
- The credential-free local run is unaffected.
- If a dark theme is ever wanted back, D1–D2 are a token swap plus restoring the
  removed `backdrop-filter`/halo rules; the git history holds both.
- `numEs` still prints near-zero negatives as "-0,000" (Toltén FAI). Pre-existing,
  out of scope, noted for a later cleanup.

## Evidence

- `agents/reviews/20260910/light-theme-pass_screens/` — screenshots of all four
  views running on real data, light theme.
- Ramp validation reproduced in `agents/reviews/20260910/frontend_credibility_pass.lq.md`
  (updated) — `validate_palette --ordinal --mode light --surface #F6F8FA` all-pass,
  CVD worst adjacent ΔE 8.5.

## Sources

- Owner request, 2026-09-10 ("colores más claros, no fosforescentes … pasteles …
  segregando en menús o topbar … márgenes readaptados")
- PR-4 — handoff deviations recorded as ADRs
- ADR-lq-0007 — the dark-theme credibility pass this extends
- ADR-sf-0005 — the frontend/model split; frontend is `lq`'s
- ui-ux-pro-max skill — light/minimal design-system search (Swiss Modernism 2.0 /
  data-dense dashboard, light)
- dataviz skill — `validate_palette` ordinal mode
