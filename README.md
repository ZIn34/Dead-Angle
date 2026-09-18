# Dead Angle

A top-down shooter fought in the dark. The map is unlit; a visibility polygon
cast against the walls decides what you can see, and everything outside it is
black. A *dead angle* is the space cover hides from you — the whole game lives
in that gap.

Runs in a browser. No build step, no dependencies, no framework.

## Running it

It needs to be served over HTTP (the game loads `game.js` and the art as
separate files). Anything static will do:

```bash
python -m http.server 8123
```

Then open <http://localhost:8123>.

## Controls

| | |
|---|---|
| Move | `W` `A` `S` `D` |
| Aim | mouse |
| Fire | click — or swing the stock if you're empty |
| Melee | `V` |
| Pick up | `E` |
| Swap weapon | `Q`, or `1` / `2` |
| Reload | `R` |
| Stim | `F` |
| Frag | `G` |
| Smoke | `H` |
| Sprint (loud) | `Shift` |
| Give up when downed | `X` |
| Mute | `M` |
| Pause | `Esc` |

A controller works throughout, menus included: left stick moves, right stick
aims, `RT` fires, `LT` frag, `RB` smoke, `LB` sprint, `A` pick up, `B` melee,
`X` reload, `Y` swap, d-pad up stim, `Start` pauses. Prompts switch between
keyboard and controller labels on their own.

## Modes

- **Battle royale** — 26 players, loot from nothing, closing zone
- **Teams 5v5** / **War 10v10** — shared loadouts, respawns, first to a score
- **Capture the flag** — carrying the flag makes you ring out across the map
- **Sectors** — three holds, every one you own pays a point a second
- **Infection** — a horde that keeps coming; survive the clock
- **Gun game** — every elimination promotes you up the weapon ladder
- **1v1** — identical loadouts on a small arena

Each takes a **CQB** (rooms and corridors) or **WORLD** (open ground with
buildings) map, a **solo** or **duos** squad size, and **normal** or
**blackout** lighting.

## How it works

- **Sight** — wall runs are merged into segments, and a visibility polygon is
  cast at them each frame. Rendering clips to it, so nothing leaks out of the
  dark. Terrain you've seen is remembered and drawn dim.
- **Sound** — every shot, footstep and reload emits a ring that propagates at a
  fixed speed. Audio is scheduled to reach your ears at `distance / ringSpeed`,
  so you hear a far-off shot exactly as its ring crosses you, muffled by range
  and by walls. In **blackout** the rings are drawn, and sound becomes
  something you can see.
- **Smoke** blocks sight only — measured as the chord a line of sight cuts
  through the cloud — while walls block movement and bullets.
- **Characters** are composed from loose parts (torso, legs, head, two arms)
  plus the weapon in hand, animated procedurally: the walk cycle, recoil, the
  grenade wind-up and the melee jab are all translation, driven by real speed.

## Layout

```
index.html        markup, styles, and the asset loader calls
game.js           the entire game
assets/           art, audio and the pack geometry
tools/            scripts that built the assets from source art
```

`EARSHOT.debug()` and `EARSHOT.step(seconds)` are exposed on `window` for
testing — `step` advances the simulation without drawing, which is the only
sane way to check bot behaviour over real game time.

## Online

Not built yet. It needs an authoritative server holding match state — the
client is already friendly to it (fixed tick, small state, bots that swap out
for players one-for-one), but GitHub Pages serves static files only, so the
server has to live somewhere that runs a process.
