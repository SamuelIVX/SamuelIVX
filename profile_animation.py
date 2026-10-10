"""Self-contained ASCII aura animation for the current profile portrait."""

import re

STYLE = '''
<style>
  .plume, .mote { opacity: 0; animation: emit 3s linear infinite; }
  .aura-value { opacity: 0; animation: glyph-cycle 1.8s steps(1, end) infinite; }
  .aura-shine { animation: shine 2.8s ease-in-out infinite; }
  .existing-aura { animation: existing-shine 3.6s ease-in-out infinite; }
  @keyframes existing-shine {
    0%, 65%, 100% { fill: var(--original); }
    28% { fill: var(--highlight); }
  }
  @keyframes glyph-cycle {
    0% { opacity: 1; }
    33.333333% { opacity: 0; }
    100% { opacity: 0; }
  }
  @keyframes shine {
    0%, 100% { fill: var(--blue); }
    35% { fill: var(--silver); }
    65% { fill: var(--violet); }
  }
  @keyframes emit {
    0% { opacity: 0; transform: translate(0, 0); }
    15% { opacity: .65; }
    45% { opacity: .5; }
    100% { opacity: 0; transform: translate(var(--drift), var(--rise)); }
  }
  @media (prefers-reduced-motion: reduce) {
    .plume, .mote { animation: none !important; opacity: 0; }
    .aura-value, .aura-shine { animation: none !important; }
    .existing-aura { animation: none !important; }
  }
</style>
'''

# Emission follows the hair, shoulders, arms and torso in the approved portrait.
# shortcut: these coordinates fit the current pose; remap if the artwork changes.
ORIGINS = ((116, 122), (226, 132), (85, 174), (267, 182),
           (74, 246), (279, 256), (91, 305), (261, 316),
           (115, 355), (238, 368), (65, 412), (284, 427),
           (47, 471), (300, 487), (124, 511), (236, 522),
           (99, 566), (272, 576))

def animate(original: str, theme: str) -> str:
    """Add the approved shimmer and body particles to a themed profile SVG.

    Args:
        original: Static SVG from update_profile.render, with art and info groups.
        theme: Dark or light palette key.
    Returns:
        SVG containing only internal CSS animation, ready for image embedding.
    """
    # Animate only the artwork's existing blue/violet aura, without new glyphs.
    # shortcut: color + region selection fits this pose; remap for different art.
    start = original.index('<g id="art">')
    end = original.index('</g>', start)
    art_source = original[start:end]
    position = 0
    def shimmer(match):
        """Highlight existing cool-colored aura cells while preserving their text."""
        nonlocal position
        row, col = divmod(position, 64)
        position += 1
        color, glyph = match.groups()
        r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
        outside_pose = row < 8 or row > 53 or col < 13 or col > 43
        minimum_blue = (25 if col > 43 else 35) if row < 8 else (45 if col > 43 else 70)
        if not outside_pose or not glyph.strip() or b < minimum_blue or b < r * 1.2 or b < g * 1.06:
            return match.group(0)
        target = (215, 245, 255) if theme == 'dark' else (95, 165, 225)
        amount = (.28 if col > 43 else .2) if row < 8 and b < 70 else (.46 if col > 43 else .35)
        peak = '#' + ''.join(f'{round(c*(1-amount)+t*amount):02x}' for c, t in zip((r,g,b), target))
        # One phase per row sends the crest vertically, including the top rows.
        return f'<tspan fill="{color}" class="existing-aura" style="--original:{color};--highlight:{peak};animation-delay:-{row*.09}s">{glyph}</tspan>'
    moving_art = re.sub(r'<tspan fill="(#[0-9a-fA-F]{6})">([^<]*)</tspan>', shimmer, art_source)
    original_with_shimmer = original[:start] + moving_art + original[end:]
    # The current art already fills its column; add motion inside its existing fades.
    plumes = []
    particles = []
    for i, (x, y) in enumerate(ORIGINS):
        color = ('#ddf7ff', '#94ccff', '#b0a0ff')[i % 3] if theme == 'dark' else ('#3b74c5', '#6584da', '#9675cc')[i % 3]
        drift = (-1 if x < 176 else 1) * (12 + i % 4 * 6)
        duration = 2.6 + i % 5 * .28
        for phase in range(3):
            # Cycle ASCII values in place as each short plume lifts off the body.
            # Three staggered states share one cell; no script or raster overlay.
            glyphs = []
            for j in range(5):
                states = ('.:.', '+*+', ':*:') if j < 3 else ('.', ':', '*')
                for state, value in enumerate(states):
                    delay = i * .17 + j * .13 + phase * .21 + state * .6
                    glyphs.append(f'<text class="aura-value" text-anchor="middle" x="{(-1 if (i+j)%2 else 1)*5.806}" y="{-j*9.677}" style="animation-delay:-{delay}s">{value}</text>')
            palette = ('#8ecfff', '#effcff', '#b7a3ff') if theme == 'dark' else ('#387aca', '#72b3db', '#8b6cc4')
            shine = f'<g class="aura-shine" style="--blue:{palette[0]};--silver:{palette[1]};--violet:{palette[2]};animation-delay:-{i*.23+phase*.51}s">' + ''.join(glyphs) + '</g>'
            plumes.append(f'<g transform="translate({x} {y})"><g class="plume" fill="{color}" font-size="9.677" style="--drift:{drift}px;--rise:-{65+i%4*18}px;animation-duration:{duration}s;animation-delay:-{i*.41+phase*duration/3}s">{shine}</g></g>')
        particles.append(f'<g transform="translate({x} {y})"><text class="mote" fill="{color}" font-size="11" style="--drift:{drift*1.5}px;--rise:-{140+i%5*20}px;animation-duration:{4.1+i%4*.4}s;animation-delay:-{i*.63}s">{(".", "+", "*", ":")[i%4]}</text></g>')
    body_aura = '<g id="aura">' + ''.join(plumes) + ''.join(particles) + '</g>'
    animated = original_with_shimmer.replace('</defs>', STYLE + '</defs>', 1).replace('</g>\n</g>\n</g>\n</g>\n<g id="info">', '</g>\n' + body_aura + '\n</g>\n</g>\n</g>\n<g id="info">', 1)
    return animated
