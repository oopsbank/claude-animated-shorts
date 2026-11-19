# FX rules

These are fx-specific lessons from review. Follow them for every new effect, and check each strip and dense timing sheet against them.

1. **Empty at both ends.** At t=0 and t=1 the sprite has no visible pixels. `catalog.py` checks this automatically.
2. **Exit by shrinking, not by alpha.** Shrink with an ease-in-out (`shrink()` = 1 - smoothstep) so the sprite is small by about t=0.92. Alpha may fade only in the last ~8%. A long alpha fade looks murky on night plates, and outlined puffs turn into hollow "soap bubble" rings. A plain cubic shrink still leaves a big sprite at 11/12 that pops off.
3. **Entry by `pop()`.** Grow a little, pull back (the wind-up), then overshoot with `out_back` (DRAWING_RULES 25). The anticipation shape must read as a ball or squash, never as a comma or another glyph.
4. **Never freeze in the hold.** Add a slow settle, drift, throb, bob or pulse between the pop and the exit.
5. **Scale stroke widths with the sprite.** When a glyph is transformed, scale `w` with `k` as well as the positions. Otherwise a shrinking "?" becomes a fat blob.
6. **Tiny shapes get a thinner outline** (`min(e, r*0.6)`). A full 3 px line on a 1 px dot reads as a black speck that pops.
7. **No blurred glows.** Gaussian halos break the flat style and smear on day plates. Use flat cel rings at low alpha. If you ever must blur, blur only the alpha and keep the RGB solid, because blurring straight RGBA drags in black.
8. **Line style follows the main cast** (bean-head, `characters.md` §2). Use plum ink `#241726`, drawn as one ink pass grown by `e` and shifted toward 64° (bottom-right) by 0.5e, so the line is thin on the top-left and about 3x thicker on the bottom-right. Fills get the soft crescent shade (`crescent()`, like `fill_shaded()` in bean.py). Size `line` to the character's scale (about `10*char_scale`), not to the sprite size.
9. **Draw outlines first, then all fills** (one merged silhouette, DRAWING_RULES 8). Details such as highlights and cores go on top with no outline.
10. **Day contrast:** pale fills (pale yellow, cyan) vanish on a light sky. Pick saturated mid-tones (`#ffe45c`, `#2fa8ec`) and let the ink outline carry the edge at night.
11. **Stagger groups in an order** (middle first, or left to right). Random delays look like pops.
12. **Look at a dense sheet** (t = 1/12 .. 11/12) on day and night, not just the 5-frame strip. Exit pops and frozen holds only show there.
13. **Diagram effects (arrows, paths, angle marks)** draw on along their length and exit by erasing along the path plus a short fade. Never flatten them. A 'blocked' sign must leave the blocked thing visible.
14. **When two reviewers ask for opposite fixes, pick the drawing convention and write it down.** For example, an angle mark is a small wedge at the pivot. Don't flip it back and forth.
