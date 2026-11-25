# Why Are Airplane Windows Round? (video 12, `plane-windows`, 2026-11-25)

The Director picked this topic and said to go ahead without a script review. **First video in the new cinematic 2D style** (see "Cinematic upgrade" below) and **the Animator runs at effort `max`** (the Director's call, a one-video trial).
"Why" format on the **Blood Falls formula** (HANDOFF): a human witness + year in line 1 (1954: British engineers sink a whole airliner in a water tank and pressurise it again and again), ONE strange hero image (a Comet fuselage inside a giant water tank in a hangar, its wings sticking out through the tank walls), the wrong answer stated and killed at once ("just style": the first jet airliner had squarish windows and two broke up in 1954), 3 one-fact clues + a riddle, the mechanism (pressurisation cycles, stress piling into sharp corners, metal fatigue), one everyday analogy (bending a paperclip), the flip ("Round windows aren't about looks. They're about not tearing open."), loop back to the 1954 tank. Serious, respectful tone (two real air disasters, 56 people died), no comedy. Voice Kokoro `am_adam` 1.16: `audio/plane-windows/` (1956 frames = 65.20 s; final with the 0.1 s cover ~65.3 s).

## Sources
- The de Havilland DH.106 Comet 1 was the first jet airliner (BOAC service from 1952). G-ALYP ("Yoke Peter") broke up on 10 Jan 1954 off Elba and G-ALYY on 8 Apr 1954 off Naples, both after taking off from Rome Ciampino and while climbing; the fleet was grounded. https://aviation-safety.net/wikibase/335195 ; https://www.faa.gov/lessons_learned/transport_airplane/accidents/G-ALYP
- The Royal Aircraft Establishment (Farnborough) put a complete Comet fuselage (G-ALYU) in a water tank and pressurised it repeatedly (water, so a failure would not explode); the wings, outside the tank, were flexed by jacks. After roughly 3,000 pressure cycles in total (about 1,230 earlier flights + about 1,830 in the tank) the cabin failed, the FAA summary says at the corner of the squarish forward escape-hatch window. https://www.faa.gov/lessons_learned/transport_airplane/accidents/G-ALYV
- Window-corner fatigue cracks are documented in the 1962 HMSO report on Comet G-ALYR. https://www.faa.gov/sites/faa.gov/files/2022-10/G-ALYR_Report_0.pdf
- Each crashed plane had flown only about a thousand pressurised flights (G-ALYP ~1,290, G-ALYY ~900).
- **Care:** how much the window shape itself is to blame for the Comet failures is debated (the G-ALYP break-up is usually traced to the roof ADF window; other airliners also had squarish windows). The script only claims what the tests showed: the test cabin split from a sharp window corner, and sharp corners concentrate stress; later airliners (Comet 4 onwards) use rounded windows.
- Simplified: "the body swells slightly, like a balloon" = the pressure difference stretches the skin a little every flight; "one flight, one squeeze" = one pressurisation cycle; the paperclip analogy is ours.

## Voice-over (213 words)
1. In 1954, British engineers sank an entire airliner in a giant tank of water. Then they pumped it up, again and again.
2. Ever noticed that plane windows never have sharp corners?
3. Most people think it's just style.
4. But the first jet airliner, the Comet, had squarish windows. And in 1954, two Comets broke apart in the sky.
5. Clue one. Both broke up climbing away from Rome, as the air outside thinned.
6. Clue two. Neither plane was old. Each had made only about a thousand flights.
7. Clue three. In the tank, the test plane finally split open, starting at the sharp corner of a hatch window.
8. So why would a corner tear first?
9. Up high, the cabin is pumped full of air so you can breathe. The body swells slightly, like a balloon.
10. Every landing, it shrinks back. One flight, one squeeze.
11. Around a round window, the stretch flows smoothly past. At a sharp corner, it piles into one tiny point.
12. Squeeze after squeeze, a tiny crack grows there, until the metal gives way. That's metal fatigue.
13. It's like bending a paperclip: once is fine. Do it a hundred times, and it snaps.
14. Round windows aren't about looks. They're about not tearing open.
15. And it was learned in a tank of water, in 1954.

## Line start times (real voice)
| line | s |
|---|---|
| 1 | 0.06 |
| 2 | 7.32 |
| 3 | 10.13 |
| 4 | 11.84 |
| 5 | 18.68 |
| 6 | 22.98 |
| 7 | 27.44 |
| 8 | 33.08 |
| 9 | 34.77 |
| 10 | 39.86 |
| 11 | 42.88 |
| 12 | 48.53 |
| 13 | 53.80 |
| 14 | 57.99 |
| 15 | 61.21 |

## Cinematic upgrade (new for this video; build the tools into flat2d so later videos reuse them, and write them up in NOTES.md + LESSONS.md)
The Director wants the look of top 2D story channels (reference: a stickman "burglar" short: real perspective sets, a moving camera, cinematic light). Keep our flat2d style, characters and captions, and add:
- **Depth of field**: blurred foreground layers framing shots (a seat back, a window frame, a tool rack), sharp mid-ground, softly blurred background.
- **Camera angles**: low angle looking up (the tank, the engineers), top-down (the tank from above, the desk), over-the-shoulder, POV through a round airplane window (the window frame as a vignette: our motif), macro close-ups (the crack at the corner).
- **A moving camera with few hard cuts**: push-ins, pull-backs, pans that carry us from one shot into the next (e.g. push through a cabin window into the sky, pull out of a window into the hangar); match cuts on shapes (round window, round tank porthole).
- **Light and colour grading per scene**: cool grey-green 1950s hangar with skylight shafts and water caustics; warm cabin light; bright thin-blue high-altitude sky; dark navy diagram stage; a soft vignette everywhere; light shafts, dust motes, rim light.
- **Perspective in sets** where it helps (the hangar and tank with real depth; the cabin aisle receding).

## Visual bible (for the Animator)
- Look: the house flat2d style at **Blood Falls / Wind Cave level** plus the cinematic upgrade above. Worlds: a 1950s **test hangar at Farnborough** (riveted steel roof, skylights, a huge water tank with the fuselage inside and the wings sticking out through the walls on jacks, pipes, gauges, engineers in white coats and overalls), a **modern airliner cabin** (seats, round-cornered windows, a passenger looking out), **high altitude** (thin blue sky, cloud sea below, the Comet climbing), a **1950s records office** for clue 2, and a clean **diagram stage** for the mechanism.
- **The Comet must look right**: a slim 1950s jet airliner, four engines buried in the wing roots (no engine pods), a rounded nose with a stepped cockpit, **squarish passenger windows** (rectangles with small corner radii), a white top and blue cheatline, **no real airline logo or name**. Modern airliner for contrast: oval / round-cornered windows.
- Disasters shown **respectfully**: no explosions, fire, debris clouds or people in danger. Show the loss as two markers on a map of Italy (Elba, Naples) after a dotted climb-out from Rome, a 1954 newspaper headline ("COMET LOST" / "COMETS GROUNDED"), or the plane fading out in the sky.
- Humans: white stickmen with a black outline (engineers, investigators, a passenger, a person bending a paperclip).
- s01 frame 0 = the hook and the loop frame: the hangar, the giant tank, the fuselage under water with wings out through the walls, engineers on a gantry, 1954 · ENGLAND title.
- s02-s03: the modern cabin window close-up (round corners), a passenger; chip JUST STYLE?
- s04: the Comet (squarish windows) climbing; then the two markers / headline; STYLE? gets an X.
- s05 CLUE 1: map from Rome, climb profile, an altimeter, "air outside thinner" (pressure gauge: cabin vs outside).
- s06 CLUE 2: logbooks / flight counters: ~1,000 FLIGHTS each.
- s07 CLUE 3: in the tank, a macro push-in on the sharp corner of a hatch window; the crack runs out of the corner.
- s08 riddle: the cracked corner, a big ?
- s09-s12 mechanism (must be crystal clear, on the diagram stage): the fuselage cross-section inflating slightly (arrows outward) and deflating on landing (ONE FLIGHT = ONE SQUEEZE, a cycle counter); stress flow lines around a round window (smooth) vs a square window (lines bunching into the corner, a red hot spot); the crack growing a little with every cycle until it rips (METAL FATIGUE).
- s13 analogy: a hand bending a paperclip back and forth, a bend counter, the clip snaps.
- s14 the flip, biggest title over a modern round window looking out on clouds: NOT ABOUT LOOKS. / ABOUT NOT TEARING OPEN. (yellow), each on its word.
- s15 back to the 1954 tank; the last frame equals s01 frame 0 (loop).
- Thumbnail: the round-cornered window vs a cracked square window, or the fuselage in the tank; text WHY ROUND? (white) / NOT FOR LOOKS (yellow), or better if you find it.
