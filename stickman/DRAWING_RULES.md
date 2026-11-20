# Stickman drawing rules

These rules come from the user's corrections in review. Follow them for every new pose, expression or character variant, and check each new drawing against them before showing it.

## Colour
1. **The whole figure is one flat colour.** Never shade the back arm or leg darker; that read as a "colour error". Depth comes only from the thin outline and draw order.
2. Use a soft lighter cap on the top of the head (lit from above). There are no other gradients on the body.

## Proportions and style (based on stickman war animations; our own character, never a copy)
3. The figure is about **5 heads tall**: head radius 98 on the 600x1000 canvas, soles at y=975.
4. The torso is a straight tube, about the same thickness as the limbs (torso 56, limbs 50). There is no neck and no hands or feet, only round limb ends.
5. Limbs bend **smoothly** at the elbow and knee. Never use sharp polyline corners.
6. Draw a **thin dark outline** (about 3 px), not a thick cartoon line.
7. A hat must never cover the eyes.

## Silhouette and strokes
8. Draw torso and legs as **one merged silhouette**: all outlines first, then all fills. There must be no seam lines inside the body.
9. **Strokes must be continuous.** No broken outline at a shoulder, and no visible round "cap" or knot where a limb joins the torso. Fill a limb from its root, but start its outline only where it leaves the torso, or hide the root under the head or torso.
10. Never fill the gaps between limbs so much that two limbs merge into a blob. Each limb must stay readable.
11. Keep the whole figure inside the canvas. Auto-centre it, and shorten or re-angle limbs rather than clip them at the edge.

## Facing and anatomy
12. **Facing the viewer means symmetric.** Both arms belong to the merged silhouette, and neither arm is layered over the torso. Layering one arm in front of the torso makes the body look turned.
13. Use front and back limb layering **only for side-on poses** (walk, run). In those poses the face also turns toward the direction of travel (`look`).
14. **Each arm attaches at its own shoulder.** The left arm comes from the left shoulder and the right arm from the right. The elbow stays on the same side as its shoulder, and only a forearm may cross the body.
15. **Foreshorten** a segment that points at the viewer by making it shorter (the upper-length factor), instead of drawing it at full side-view length.

## Specific poses
16. **Think / hand on chin (front view):**
    - The right upper arm is foreshortened, so the elbow sits in front of the chest under the chin.
    - The right forearm rises **vertically** to the chin.
    - The left arm hangs from the left shoulder, then its forearm crosses the belly to support the right elbow.
    - Draw order: right upper arm, then the left (supporting) arm, then the right forearm. Redraw only the hand over the chin after the face, joined to the forearm without a seam.
17. **Wave, point and cheer:** arms come from the shoulders and stay within the canvas. Pointing arms are shortened so they never clip.

## Review habit
18. Before showing a pose, render it large and look at a **zoomed crop of the shoulders, elbows and crossings**. Check rules 1, 8, 9, 12 and 14 in particular.
19. In scenes, bloom or glow must never blow out the character's face. Only warm lights glow.

## Animation (from walk-cycle and 12-principles references, applied in `scripts/anim_v2.py`)
20. **Walk cycle** = contact -> down -> passing -> up, then mirrored. The hips are lowest just after contact (the stance knee gives a little) and highest after passing. Only the **swinging** leg bends its knee, most as it passes under the hip, with the thigh lifting slightly forward. The supporting leg stays nearly straight.
21. **Foot locking: no sliding.** The hip travels exactly as far as the planted foot moves back. Compute the travel from the stance foot; never move the character at a constant speed.
22. **Arms swing like pendulums from the shoulder,** opposite the legs, peaking a little **after** the legs (overlap). The forearm trails the upper arm.
23. **Line of action:** lean about 4 degrees into the walk direction. Straighten up on the stop.
24. **Stops:** finish on a contact pose, sink (down), bring the feet together, then let the arms settle with a damped swing (follow-through).
25. **Every action** has anticipation (a small opposite move first), then the action with ease in/out, then overshoot and settle (`out_back`). Never use a plain linear blend between two poses.
26. **Transitions that would pass limbs through each other go in stages.** Example for think: arms down first, then the hand to the chin, then the other arm crosses. Animate the shoulder positions (`_sh`) instead of letting them jump.
27. **Front-view crouch:** the knees go out and the feet stay apart. Never let the shins meet, which reads as a loop.
28. **Moving holds:** subtle breathing (about 0.6% scale) and blinks every 2 to 4 s. Never fully freeze.
29. Start the walk-in just off-screen so the first frames are never empty.

## Wardrobe (outfits, hats, props, mouths)
30. **Garments recolour the merged silhouette; they never redraw it.** A sleeve, trouser leg or torso band is stamped at exactly the fill width (never over the outline). A garment that widens the body (coat skirt, apron skirt) joins the outline pass and the fill pass like a limb, so it merges with no seam.
31. **Sleeve, trouser and shirt-hem ends are straight cuts** perpendicular to the limb, not round stamps.
32. **Garment details (buttons, collar, belt) are drawn after the front-view arm fills.** Otherwise the arm roots hide them and leave half-buttons or slivers (a collar once showed only as a dark triangle).
33. **A skirt's top stays inside the torso tube** (half-width 26 or less). Wider tops make a visible step at the waist.
34. **Side-on garments follow the stride.** A coat skirt tracks the outer edges of both thighs. An apron hangs from the waist on the leading side and drapes over the front thigh, with one strap. Never paste a front-view panel onto a side-on body.
35. **In side-on poses, draw the front arm before the head,** so its root (and a coloured sleeve root) hides under the head. Drawing it after the head broke the head outline at the chin and left a sleeve "knot".
36. **Two garments of similar colour need a tint plus a dark edge.** A white apron on a white shirt vanished. Give the upper garment a tinted fill and a thin ink edge.
