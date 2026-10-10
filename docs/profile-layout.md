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
Nested luminance masks fade 2% of the column width and 1.5% of its height
(about 7–9 pixels) into the theme background, softening edges and corners without
recoloring or blurring the center.

Run `python -m unittest -v` to check both themes, zero and large counts, art
preservation, edge masks, and alignment. The scheduled workflow runs these checks before
`python update_profile.py` refreshes the SVGs with live stats.

Visually check both themes at desktop and narrow widths. The README image fills
its available width; on narrow screens the whole image scales down, including
its text.
