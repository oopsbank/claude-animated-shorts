# Bean cast: drawing rules

The spec is `references/reports/characters.md` §2. The anatomy and animation rules in `stickman/DRAWING_RULES.md` (smooth bends, each arm from its own shoulder, foreshortening, continuous strokes, walk rules 20-29) apply here too. Each rule below is a mistake already made once, phrased as an instruction.

## Views
1. **Front view stays pixel-identical** when you add features. Run the regression check (save the cast and expressions before, compare after) on every change to `bean.py`.
2. **Side-view nose:** use a small open arc bulging forward, placed below the eye line. A `>` tick at eye height read as a third, squinting eye, in both side and 3/4 views.
3. **Side view needs two readable legs.** Stand the feet apart (near leg forward, far leg back), offset the hips a little, and draw the far leg darker (`mix(pants, INK, 0.8)`). Legs on top of each other read as one stilt.
4. **Arm length scales with the torso** (`min(0.85, torso - 0.28) × HH`). In side and 3/4 views, hands that hang below the torso hem read as extra short legs (kid build).
5. **Hats turn with the head.** In side and 3/4 views the brim juts out on the facing side and front details (a hard-hat ridge) move toward the front.
6. To show a forearm raised forward in a turned view, **bring the elbow forward**. A forearm lying across the belly reads as a hand on the stomach.

## Riding (`bikes.py`)
7. **Front and rear views: spare limb length goes into depth.** When a target is closer than the full limb (pedals under the hip, bars ahead of the chest), draw the limb foreshortened with a small outward bow. Two-bone IK in the screen plane threw the knees and elbows out into big sideways loops.
8. **Pad the rider card** (`turned(pad=...)`) for leaning riders. A rider leaning with the bike left the 600-wide card and got cut off.
9. **Side/3q: handlebars ahead of the chest draw over the body** and under the near hand. Otherwise the hand looks like it is resting on the belly.
10. **Seat the hip a torso-hem above the saddle top**, so the saddle shows under the body, and **fit the bicycle saddle to the rider's leg length**, so the lower leg is nearly straight.
11. **Elevated cameras (rear/front chase views): ground the lowest tyre** on the ground line, or the near wheel drops off the bottom of the card.
12. **Edge-on discs** (lamps seen from the side) need a housing and a coloured lens stroke. A bare ink line read as a stray mark.
13. **Text that carries a joke must read at video size.** The helmet sticker on the back of the head is about 1.45a wide (most of the shell). Small stickers on the side of the helmet are decoration only.
14. A **second, fixed handlebar** must read as a bar, not a fork: make it wider than the steering bar, thick, a different colour, with a clamp block and bolt heads.
