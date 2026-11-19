# Bean cast: drawing rules

The spec is `references/reports/characters.md` §2. The anatomy and animation rules in `stickman/DRAWING_RULES.md` (smooth bends, each arm from its own shoulder, foreshortening, continuous strokes, walk rules 20-29) apply here too. Each rule below is a mistake already made once, phrased as an instruction.

## Views
1. **Front view stays pixel-identical** when you add features. Run the regression check (save the cast and expressions before, compare after) on every change to `bean.py`.
2. **Side-view nose:** use a small open arc bulging forward, placed below the eye line. A `>` tick at eye height read as a third, squinting eye, in both side and 3/4 views.
3. **Side view needs two readable legs.** Stand the feet apart (near leg forward, far leg back), offset the hips a little, and draw the far leg darker (`mix(pants, INK, 0.8)`). Legs on top of each other read as one stilt.
4. **Arm length scales with the torso** (`min(0.85, torso - 0.28) × HH`). In side and 3/4 views, hands that hang below the torso hem read as extra short legs (kid build).
5. **Hats turn with the head.** In side and 3/4 views the brim juts out on the facing side and front details (a hard-hat ridge) move toward the front.
6. To show a forearm raised forward in a turned view, **bring the elbow forward**. A forearm lying across the belly reads as a hand on the stomach.
