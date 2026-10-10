# Profile layout

The README embeds one SVG with a 40/60 split: colored ASCII art on the left,
information and stats on the right. Both themes use an 880 × 600 canvas. The art
fills the left 352 pixels; information spans x=360 to x=864 with a small inset.
Normal stats text is 13.125px, about 21% larger than the previous equal split.

Values use explicit SVG positions and right anchors. Dotted leaders and section
rules span the same column width. Longer counts can grow beyond their usual
character allocation; the renderer reduces the shared font size to keep them
inside the column. Art scales proportionally to cover the 352 × 600 left
column and is clipped to that viewport. All 62 source rows and their colors are
preserved; the crop removes a little from the sides while showing the full height.
`profile_animation.py` adds a vertical blue-white shimmer to existing aura glyphs
and the approved ASCII particle streams around the body. Their colors pulse and
their ASCII values cycle; no surrounding outline or raster overlay is added.
The right and top-right aura have slightly stronger highlights for balance.
Animation uses internal SVG CSS; stats remain stationary and no scripts are embedded.
Nested luminance masks fade 2% of the column width and 1.5% of its height
(about 7–9 pixels) into the theme background, softening edges and corners without
recoloring or blurring the center.

Run `python -m unittest -v` to check both themes, zero and large counts, art
preservation, edge masks, and alignment. The scheduled workflow runs these checks before
`python update_profile.py` refreshes the SVGs with live stats.
The generator writes both animated `*_mode.svg` and static `*_static_mode.svg`
files. The README picture selects static assets for reduced-motion users before
selecting the normal dark/light images. The workflow's `*_mode.svg` glob includes
all four files, keeping their stats synchronized. Source colors are retained as
the base fills; only selected aura characters brighten during animation.

Visually check both themes at desktop and narrow widths. The README image fills
its available width; on narrow screens the whole image scales down, including
its text.
