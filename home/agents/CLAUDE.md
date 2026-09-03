# Tooling preferences

Prefer the `fff` MCP tool over `grep`/`ripgrep` for code search. Reach for `grep` only when `fff` can't do the job.

Install and update agent skills only with the skills CLI (`bunx skills add/update/...`). Never copy or edit installed SKILL.md files by hand.

Never use `npx`; use `bunx` instead, unless something specifically requires `npx`.

Using `bun` as the package manager does not imply `bun` is also the runtime. Default the runtime to `node` unless the user has explicitly said otherwise (or the project's config/scripts already make the runtime unambiguous, e.g. `bun:` scripts or Bun-only APIs in use). If it's unclear which runtime a project wants, ask.

Use `mbx` (Mr Boxington) instead of `cargo`. It is a caching wrapper: put `mbx` where `cargo` would go and pass the same arguments. It keeps the build cache and target directories on an external volume rather than the internal disk, and reuses compiled work across checkouts and worktrees.

mbx owns those two paths and reads them from its own configuration, so an `mbx` command runs bare — no environment variables in front of it. A project file that tells you to point Cargo somewhere by hand predates mbx: run the command bare, then say so, because that file is stale and worth fixing.

```bash
mbx build --release
mbx test --workspace --all-features
mbx clippy --workspace --all-targets
```

Cargo still owns resolution, features, and linking, so aliases and installed subcommands (`mbx nextest run`, `mbx add serde`) work unchanged. `mbx` also has its own commands: `mbx doctor` checks the setup, `mbx explain <cmd>` reports what could not be cached, `mbx cache stats` and `mbx gc` inspect and trim the store.

Ignore Rust build output as `target` or `/target`. mbx replaces the directory with a symlink into its cache, and a pattern ending in a slash (`target/`, `/target/`) matches directories only, so git offers the symlink for commit. Stock Python and Java templates ship the slash form, so a mixed-language repo can carry it without anyone choosing it.

Typing `cargo` in a non-interactive shell reaches a wrapper that forwards to `mbx` anyway, so nothing breaks if you forget — but write `mbx`, because bare flags (`cargo --version`) deliberately bypass it.

# Worktrees

Worktrees are how parallel agents share one repo without stepping on each other. Use `wt` (Worktrunk) for all of it — it owns the layout, hooks, and cleanup, so a worktree it creates carries `.env`, caches, and dependencies over from the primary worktree with copy-on-write reflinks.

- Start isolated work on a task: `wt switch --create <branch>`. In a script, `cd` to the path `wt switch` prints.
- Survey state: `wt list` (branch, status, CI, ahead/behind per worktree). Check out a pull request: `wt switch pr:123`.
- Finish a local branch — commit, squash, rebase, fast-forward, clean up in one command: `wt merge`.
- Sharing caches is opt-in per repo: a `.worktreeinclude` file (gitignore-style patterns) lists what the post-start hook copies.

Raw `git worktree add` bypasses wt's layout and hooks — a hand-made worktree starts cold and lands outside `wt list`'s conventions. Create worktrees with `wt switch --create`.

# Engineering decisions

- Do not preserve backward compatibility. Remove obsolete paths instead of adding compatibility layers, fallbacks, or migrations.
- Choose the simplest implementation that fully meets the current requirements. Avoid speculative abstractions, configuration, and indirection.
- Grow the system in layers. Start from the smallest version that works end to end, and add each new capability on top of a product that already works. Never trade a working product for unfinished complexity.
- Keep components modular and concerns clearly separated.
- Prefer established, well-maintained libraries when they reduce overall complexity or improve reliability. Do not reimplement common functionality without a clear reason.
- Lean on the dependencies already in the project before writing your own implementation or adding packages. Do not assume a library lacks a capability without checking its documentation and types.
- Make architectural decisions for the long term. Do not accept a stopgap that only works for now and is meant to be replaced later.

(Source: [Marcos Hernanz on X](https://x.com/MarcosHernanz/status/2083954734487212511) — his full AGENTS.md after ~60B tokens of testing; earlier tweets in the same thread are subsets of this.)

# Writing style

Always write in ASD-STE100 Simplified Technical English — every response, not only formal documents. Invoke the installed `simple-english` skill by default, in its "pragmatic" mode (real domain vocabulary like `webhook`, `idempotent`, `deploy` stays; only go to "strict" mode if the user explicitly asks for standards compliance). Short sentences, active voice, one word for one meaning (don't call it "config" here and "settings" there), plain verbs over inflated ones (`use`, not `leverage` or `utilize`; `help`, not `facilitate`). Cut hedging modals ("should," "would," "may," "it's worth noting that") and filler transitions ("not only X, but also Y", "in today's fast-paced world", significance-inflation like "stands as a testament to" or "serves as a cornerstone of").

Why this exists, and where it came from: the underlying idea — writing in a controlled, low-ambiguity register cuts the tells that make LLM output read as LLM output — is what practitioners on X have converged on independently of this one repo (e.g. [Andrew Carr](https://x.com/andrew_n_carr/status/2082453463712018658) reaches for an STE-style prompt specifically when Claude/Codex invent project-specific vocabulary and it gets out of hand; [Shreya Shankar](https://x.com/sh_reya/status/2066674728396579101) built a similar "plain writing" skill out of her DocWriter research into AI "slopwords"; [Matt Pocock](https://x.com/mattpocockuk/status/2084753070437609606) runs "always talk in ASD-STE100" as the sole rule in his global CLAUDE.md, echoing Sebastian Cochinescu (@cochinescu on X)'s framing of it as "the smart version of caveman" — for token efficiency and clarity at once). The Hacker News discussion of the skill itself (468 stars, 232 points) landed on a fair point worth internalizing rather than outsourcing entirely to the skill file: most of the value is the tested rule set and the discipline of picking one word per concept, not a trick unavailable elsewhere.

## Read CONTEXT.md files

When a project has a `CONTEXT.md` (or similar domain-vocabulary doc), always read it first and use its terms exactly — including its "avoid" lists. These files exist to stop ambiguity between similarly-named concepts (three systems each with a `user` table, say) from leaking into conversation and code. Treat their vocabulary as load-bearing, not a suggestion.

(Source: [Matt Pocock on X](https://x.com/mattpocockuk/status/2084753070437609606) — "Always read CONTEXT.md files, and use their ubiquitous language.")

## Zinsser's four principles

Alongside ASD-STE100, hold every piece of writing to Zinsser's four qualities: **simplicity**, **brevity**, **clarity**, **humanity**. The first three cut clutter; the fourth is the check the other three don't cover — plain and short can still read like a machine. Write like a person said it.

## Forbidden patterns

Read `~/.claude/forbidden.md` for a growing catalog of specific rhetorical tics that read as AI-generated (the antithesis reframe, staccato pairs, and others). Check output against it before sending. When you catch a new tic in your own writing that isn't in the file yet, add it.

## Writer subagent context budget

If a task spins up a dedicated writer subagent, keep it under 50% of its context window at all times — quality drops fast past that point. Delegate to fresh subagents for sub-sections rather than letting one subagent's context fill past half.

(Source: [Shann³ on X](https://x.com/shannholmberg/status/2086809139729367521).)

# Code comments

Write comments the way a top-tier maintainer would: they have a voice, but they're not chatty, not robotic, and never stiff corporate-speak. A comment can sound like a person thought it, not like a linter generated it.

**Never narrate history.** No "this used to duplicate the row because X," no "removed the second copy that caused Y," no "fix for the bug where...". A comment documents the code as it stands *now* — history belongs in the commit message or PR description, never the source. If code changes, the comment either stays true or gets rewritten; it never becomes a fossil record of what was wrong before.

**Comments earn their place by saying something the code can't.** Before writing one, ask what a reader still won't know after reading the code itself — that's the only thing worth writing. Never restate what a line already says.

What's worth writing (loosely following antirez's taxonomy and Ousterhout's *A Philosophy of Software Design*):
- **Why / rationale** — the reasoning behind a non-obvious decision, especially a tradeoff. "We do X here because skipping it means Y" is the shape to aim for: causal, specific, and honest about the cost of the alternative. This is the single highest-value comment type and the one to reach for most.
- **Interface / contract** — for a public function, class, or module: what it promises to callers (behavior, invariants, units, nullability, ordering) that isn't obvious from the signature. Written for someone who will never read the implementation.
- **Non-obvious domain knowledge** — the bit of math, protocol detail, or business rule a reader can't be expected to already know, stated plainly so they don't have to go look it up.
- **Synchronization warnings** — "if you add a case here, also update `getTypeNameByID`" — the kind of comment that exists because the type system or tests can't catch the coupling for you.
- **Structural signposts** — sparing, only where a genuinely dense function needs a beat to breathe. If a comment is easier to skip than the code it's next to, it's dead weight; delete it.

What to avoid:
- Comments that just re-say the line in English ("increment i by one").
- Formal, hedge-everything corporate tone ("It should be noted that…", "Please be advised…").
- TODO/FIXME left to rot — either fix it, file it, or don't leave a marker that nobody owns.
- Commented-out code. Git remembers it; the file shouldn't.
- Apologizing or narrating uncertainty in the comment itself ("I think this works but not sure why").

Sources: [Code Tells You How, Comments Tell You Why (Coding Horror)](https://blog.codinghorror.com/code-tells-you-how-comments-tell-you-why/), [antirez — Writing system software: code comments](https://antirez.com/news/124), John Ousterhout, *A Philosophy of Software Design* (comments chapter), Kernighan & Pike, *The Practice of Programming* (commenting chapter), [Linux kernel coding style — commenting section](https://docs.kernel.org/process/coding-style.html).

# Commit / PR hygiene

Never add "Co-Authored-By" lines or any other reference to the AI agent/tool used (in commit messages, PR descriptions, code comments, etc.), unless explicitly asked to.

Always write commit messages following [Conventional Commits](https://www.conventionalcommits.org/) (`type(scope): description`, e.g. `fix(auth): handle expired refresh tokens`). Use the repo's existing type/scope conventions if it already has some; otherwise default to the standard types (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `ci`, `perf`, `style`).

## Stacked pull requests

When a change is big enough that one PR would bury the reviewer, stack it: a chain of small PRs, each targeting the branch below it, each reviewable as its own diff. Reach for the `gh-stack` skill (backed by `gh stack`) whenever the user asks for a stack, or the work has natural sequential layers (e.g. data model, then API, then UI).

In T3 Code, one agent thread's worktree is one layer. Branch a new layer off the previous layer's branch with `gh stack add <name>` instead of branching from `main`, and submit with `gh stack submit` instead of a flat `gh pr create`. Write each PR body to describe only that layer's own diff — never the whole stack's. Restructuring commands (`gh stack modify`, `rebase`, `unstack`) touch branches a reviewer may already be mid-review on, so run them only when the user asks.

(Sources: [GitHub changelog — stacked PRs public preview](https://github.blog/changelog/2026-07-30-stacked-pull-requests-are-now-in-public-preview/), [github/gh-stack](https://github.com/github/gh-stack), [T3 Code architecture](https://betterstack.com/community/guides/ai/t3-code/).)

# The anti-slop design law

Source: https://pols.dev/slop.md

Follow this whenever designing or building any interface. Read it before starting, keep it in mind while working, and re-check output against it before shipping. The user's explicit instruction always overrides a default below — absent that, this is the default.

## Fonts to avoid (read as generic/AI-made)
Sans: Space Grotesk, Sora, Syne, Archivo, Onest, Darker Grotesque, Geologica, Hanken Grotesk, Spline Sans, Schibsted Grotesk, Gabarito, Figtree, Quicksand, and rounded novelty faces (Bagel Fat One, Baloo, Fredoka, Chewy, Lobster). Serif: Fraunces, Cormorant Garamond, Bodoni/Didot/Didones, Petrona, Hedvig Letters Serif, Brygada 1918, Young Serif. Mono: JetBrains Mono, IBM Plex Mono, Spline Sans Mono, Fragment Mono. Also avoid "tasteful designer" defaults reached for by reflex (Big Shoulders, Newsreader, Instrument Serif, Bricolage) — picking by reputation instead of the brief is still slop. Prefer licensed/self-hosted type (Fontshare: General Sans, Clash Display, Cabinet Grotesk, Satoshi, Switzer — though even these now read generic; reach further: Pally, Gambarino, Sentient, Tanker, Velvetyne) paired with a true neutral body (system-ui is fine). Never reuse the same font pairing across projects.

**Exception:** Inter and Geist (including Geist Mono) are allowed — do not flag or avoid them.

## Color to avoid
- Blue-to-purple gradients (the single most recognizable AI palette move), and purple alone.
- Cool blue-charcoal dark mode default (~#0c0e15 with lilac/periwinkle accent).
- Pastel candy gradients (butter-yellow/peach/pink, mint-to-lavender).
- Drifting soft-blend gradient blobs / "candy aurora" (multiply-blend blurred orbs).
- Radial glow halos behind objects, background glow bleeding from corners.
- Cream/beige "editorial" background as a default — as unconsidered as blue-purple now.
- The default UI-kit neutral gray (#f3f4f6-ish family) as a surface/footer/divider color.
- Saturated/poster-bright accent colors used identically everywhere. Prefer tonal (much lighter/darker, desaturated) accents.
- Colliding colors between adjacent sections, or hard color seams at section boundaries — let color hand off, not cut dead.
- Two gradients (in type + behind it) clashing.

## Components/patterns to avoid
- Pill/eyebrow badges, glowy pill buttons, gradient pill with icon+text.
- Oversized icon in a colored tile (also true for logos — bare marks only, no container box).
- Floating decorative cards with idle bob animation.
- Kitchen-sink cards stacking many tells at once.
- Fake macOS window mockups, fake code-snippet windows (unless genuinely populated/real).
- Default CTA button pair (gradient-filled primary + outline ghost secondary) — pick one clear action or a non-stock differentiation.
- Three-tier pricing block as a preset, "MOST POPULAR" glow+pill middle card.
- Testimonial cards with giant quote-mark icon + fake metric; decorative smart-quote wrapping.
- Gradient-circle initials avatars.
- Pre-footer CTA gradient banner slab.
- Logo lockup: icon in gradient squircle + generic geometric wordmark.
- Grid/graph-paper background as a default filler (fine only if sparing/specific: ticks, crop marks).
- Crude CSS/SVG placeholder illustrations (bar-chart divs, floating spheres, orbit rings).
- Accent-bar card with a single colored edge line added "for interest".
- Hairline light 1px borders on every card by default (prefer self-colored low-opacity border + tonal surface shift).
- Countdown timers used to fake urgency.
- Card hover-lift (translate + all-around shadow bloom + glowing border) as a reflex.
- Letterspaced serif wordmark as instant "luxury".
- Monospace used as the house voice for non-data text (labels, captions, copyright).
- One label treatment (tracked uppercase/mono) applied to every small string on the page.
- Botched glass: visible blur banding, shadow/glow leaking below the element, resting halo that never blends, blur that "pops" on interaction.
- Botched fill animations: caps flip rounded mid-transition, partial-length fills, stutter easing.
- **Never hide content behind an entrance animation.** Content must be visible by default; never gate existence of text/controls on animation completing (covers CSS `animation-timeline`, IntersectionObserver reveal classes, Framer `initial={{opacity:0}}`). Animate things already on screen instead.
- Content sliced by a clip-path/notch/overflow/fixed-height cut — always "clear the cut" with padding, verify pixel-for-pixel.
- Misaligned parallel columns in comparison grids — anchor buttons to bottom, equal card height, shared baselines per role regardless of copy length.
- Text jammed against the viewport/container edge with no gutter.
- Default all-around soft shadow by reflex — use tight, directional, tinted-to-surface shadows, or none.
- Content flung to far edges with dead space between (default asymmetry) — align to a shared grid instead.
- Missing real logos/icons where they'd add legitimacy, OR invented/faked logos — never fabricate, use real assets only when warranted.
- Chronic centering misses (SVG/badge/pill content not actually centered — verify `dominant-baseline`, optical vs bounding-box center).
- Faking a shadow by inserting a second offset box/duplicate element instead of a real shadow.
- Icon or logo placed on a filled tile/chip/circle background — strip the container.
- Decorative hairline "eyebrow tick" beside a kicker label.
- Oversized footer wordmark done without craft: uncentered, clipped caps, clashing internal gradient, no letter-spacing decision. When done right: centered, deliberate case/spacing, placed above background texture, anchored flush to the bottom edge with no gap beneath.
- Hard-edged "box" shadow (blur too tight, reads as a duplicate panel) instead of a seamless falloff.
- Low-contrast text on its background — always confirm real legibility, especially button labels.
- Shadow/glow that's just a blurred copy of the element's own silhouette ("bloom") — use one small directional cast shadow instead.
- Dot under the active nav item as a stand-in for a real active state (use weight/color shift on the link itself).
- Content clipped where an overlapping section's edge guillotines what should continue underneath.
- Cramped display type with crushed tracking around separators/units — give big type room.
- Grain sitting on top of content/text instead of behind it as a substrate texture.
- Hero shorter than the viewport so the next section bleeds in unaligned — compose the hero to own the first screen.
- Multi-line (3-4 row) stacked headlines with no rhythm; a lone colored/italic accent word stranded at the end of a tall stack.
- Filled-button-next-to-outlined-button as the default action pair.
- Small-label-over-big-heading section openers used for every section (vary: drop the label, change scale, open with an image/number/sentence).
- Numbered steps (01/02/03) beside a plain vertical rule.
- Sun-and-moon sliding theme toggle; hand-redrawn generic line icons (document+checkmark, linked circles, shield+tick) that could sit on any product.
- Bare unrounded hairline rules used as decoration/dividers.
- Metadata/tags wrapped in tinted pill chips everywhere, by reflex.
- Dead/fake controls: any tab, accordion, slider, toggle, or button must actually work when clicked.
- Hover "boop" (button lifts/scales on hover) — change state via fill/color/icon-slide instead, never move the button.
- Inner-glow badges/boxes that light up from within; pulsing glow ring on a "live" status dot.
- Off-center strike-through/cut lines not aligned to true x-height/vertical center.
- Underline-fill hover animations (growing/wiping underlines) on links and buttons.
- Fixed-position background that just trails the scroll under everything including the nav, with no real reactivity.
- Hard image-to-flat-section seams — mask the image's own pixels with a long, finely-eased gradient (10+ stops, ~30% of section per edge), on a tall section, against continuous background color on both sides; never a color-overlay-only fix.

## Slop layouts (recolor doesn't fix a template layout)
- Kicker + serif-H2 section head, repeated on every section.
- Big serif statement block with one italic accent word as "the idea" beat.
- Inset "enquire" island with kicker + serif headline + form, as the default closer.
- Email-pill input beside a pill button as the default signup row.
- Image card with bottom gradient scrim + uppercase label + serif name + arrow.
- Full-bleed hero image followed by flat dark/cream fill for every section after — atmosphere must carry the whole page, not just the hero.
- Recycling your own house style (same 5 section shapes, new palette) across different projects.
- Hero-stack-with-right-panel (eyebrow, headline, subtext, 2 buttons, product panel right) — the most over-shipped skeleton; break the axis or drop pieces.
- The entire Stripe/Linear/Vercel meta-skeleton (2-col hero → 3 feature cards with tiled icons → tabbed switch → pricing cards → FAQ accordion → CTA slab → multi-column footer) stacked in that order.
- Stacking multiple recognized slop layouts compounds into unmistakably generated output even if each block looks clean alone.

## Dodging the checklist is still slop
Swapping fonts, recoloring the same skeleton, using a rule instead of a border, deleting all icons to "play it safe" — none of that is design. The bar is a genuine point of view, executed with conviction, not the absence of flagged items.

## What premium execution actually looks like
- **Real translucency**: glass that refracts a real backdrop, chromatic dispersion at edges, top-lip highlight, tuned inner/drop shadows — reacts to what's behind it. (Concrete reference recipe: fill ~50-100% opacity brand color, white label, two 20%-opacity hairline strokes in near-surface tints, inner top highlight shadow, tight color-matched drop shadow at low opacity; glass params — light angle/intensity, refraction, depth, dispersion, frost, splay. CSS approximation: `backdrop-filter: blur()` + saturate/contrast, inset white box-shadow, layered low-opacity border strokes, tight color-matched drop shadow, 1px cyan/magenta edge offset for fake dispersion.)
- **Self-colored borders + tonal elevation**: shift surface value slightly from background, 1px stroke in the surface's own color at low opacity, soft top inner highlight — an edge you feel, not a drawn line.
- **Bespoke geometry**: invented silhouettes (diagonal-cut markers, chamfers, notches, custom brackets) instead of default rectangles, applied to dividers/corners/edges.
- **Bare icons**: no tile/chip/container behind icons — the mark alone.
- **Say less**: terse copy, cut every non-load-bearing line, let spacing and hierarchy carry meaning.
- **Custom in-house iconography**: one consistent house style (stroke, corner, grid), not a pulled pack — and not zero icons either.
- **Authored micro-interactions**: bespoke, tuned motion specific to one element, not default fade-and-translate.
- **Considered light**: specific, unexpected glow color/direction/falloff instead of the reflexive blue-purple bloom.
- **Premium noise**: very-low-opacity film grain/perlin noise on gradients and flat fills to kill banding and add tactility — felt, not seen.
- **Licensed/self-hosted type** over free Google defaults as the signature face; neutral workhorse + mono as support.
- **Full-page, large-scale composition**: oversized headlines, a wordmark bleeding off an edge, generous negative space — the whole viewport art-directed as one frame.
- **Real logo walls**: genuine recognizable brand marks only, monochrome and evenly sized — never invented or faked.
- **Blueprint/canvas backgrounds**: fine module grid, ruler ticks, corner crop marks, dashed guides — subtle and monochrome, not a full-bleed grid.
- **Inset "island" sections**: floated panel with consistent margin on all sides on a distinct surface, reading as a deliberate detached object.
- **Crafted custom SVG renders**: hand-built product/illustration with real proportion, layered detail, considered light.
- **Scroll-authored motion**: content that reveals/settles/parallaxes tied to scroll position, subtle and fast, always gated behind `prefers-reduced-motion`.
- **Grainy, never banded, gradients**: dither noise into any large color transition.
- **Good grid**: a fine, small, textured micro-grid (not lazy full-page graph paper) — looks like a printed substrate, not a wireframe.

## The signature: how uniqueness is actually made
A correct, sparse, well-typed page with zero invention is still boring. Formula: **one signature artifact** (a single custom high-effort focal object nothing else could be pasted into) + **atmosphere, not a flat fill** (a composed environment: illustration, render, texture, scene) + **layered z-axis depth** (foreground copy / midground focal object / background scene, with at least one element crossing a layer boundary) + **the product shown as a real, populated artifact** (not empty placeholder boxes) + **character in the display type** (headline face has real personality, set large — body can stay neutral) + **one bespoke silhouette** (a single custom-cut shape signing the page) + **a treated, deliberate nav** (not a flush default row) + **real specifics** (real logos, real names/data, real copy — not generic placeholders).

Decide the signature artifact FIRST; nothing else rescues a page that's missing it.

## Applying premium moves
These are tools for the right context, not a checklist to run top to bottom. Two equal failures: stacking every technique at once (noise, not design — pick only what fits this brand), and using nothing when a signature is clearly called for (the boring failure). The governing rule is cohesion — never add an element that fights the rest of the system; one palette, one type voice, one signature artifact, decided first, everything else composed around it.

Useful concrete moves: a large signature serif headline with one italic/accent-colored word; full-bleed atmospheric hero as the actual background art; an animated low-contrast character-field background (reduced-motion gated) for data/dev/AI/security products; gradient-filled icon interiors used sparingly as a "jewel" detail; a deliberately drawn (not default) CTA arrow; one cohesive visual language across nav/buttons/corners/borders/background; premium glass CTAs only over a backdrop worth refracting.

**Real component libraries over hand-rolled UI** (in a framework context, e.g. Next.js/React): prefer accessible, tested primitives over reinventing buttons/toggles/nav/cards from scratch, then art-direct hard on top for the brand. Standing toolkit: Motion (motion.dev / `motion/react`) as the animation engine of choice; shadcn/ui for accessible Tailwind+Radix primitives; tailark for Tailwind marketing blocks; motion-primitives for Motion+Tailwind animated components; kokonut UI for Tailwind v4 + Motion component set. In a non-Tailwind codebase, adapt their structure/patterns rather than dropping in Tailwind classes that won't apply — never bolt global Tailwind onto an existing non-Tailwind app for one block. Always de-slop prebuilt blocks: strip any blue-purple gradient, glowy pill, fill+outline pair, sun-moon toggle, or tracked-caps default the library ships, and run the result through this whole list before shipping.

## Field notes (win over everything else when in doubt)
- **Incoherence, not individual slop tells, is the most common failure**: parts that are each fine but don't belong to each other. Fix: one disciplined palette, one type voice (or one display + one quiet neutral, nothing else), one signature artifact decided first, then compose sections from that world.
- **"Creative" ≠ "realistic"**: when a brief calls for creative/maximal, literal photoreal stock imagery reads as the opposite of creative. Use one consistent authored medium instead (cyanotype, a single illustration style, pixel art, riso, painted sky) — a limited palette also makes every image auto-cohere.
- Fontshare faces, self-hosted via `next/font/local`, are the practical route to licensed-feeling type without a paid license — but even Clash Display/General Sans now read as the new default; reach further (Pally, Gambarino, Sentient, Tanker, Velvetyne) and pair with a true-neutral body (system-ui).
- A faux app window is only a slop tell when it's empty/generic — a fully populated, real product UI (actual editor, real diffs, working controls) floated with depth is a genuine signature. Never fake a product UI for something that's just a file; design from what the thing actually is.
- When given reference sites for "vibe," lift the design *language* (palette mood, type energy, motion, the kind of hero/footer) and write fully original copy/layout/artifact — reproducing a reference's actual headline or product window is copying.
- Dead/static pages are a real rejection even with zero slop tells present. Put authored, purposeful motion somewhere (a nav that responds, a drifting signature, scroll-linked parallax, crafted hovers) — calm is fine, dead is not. Never gate content on a reveal; animate position, not opacity-from-0.
