# Every Night at 3 A.M. (video 13, `night-clock`, 2026-11-25)

The Director (2026-11-25): an ORIGINAL story made like a short film, not based on any real case; open on someone asleep upstairs hearing a noise downstairs. **Fiction**: the posting description must say it is a short story (the channel's earlier videos were true stories). Mystery skeleton kept: hook, wrong answer killed, 3 clues, riddle, reveal on camera, flip line, loop back to 3 a.m. Suspense tone, warm ending, no comedy. Voice Kokoro `am_adam` ~1.16, 216 words. Look: the stickman story style with real perspective sets (HANDOFF › Direction set on 2026-11-25).

**Title (proposed):** Every Night at 3 A.M., Someone Unlocks Her Door 🕰️ · **Thumbnail:** dark hallway, an old man's silhouette at the grandfather clock, Emma peeking down from the stairs; WHO WINDS (white) / HER CLOCK? (yellow).

## Voice-over (`vo.txt`)
1. It's 3 a.m. Emma is asleep upstairs. Then, downstairs, something clicks.
2. Footsteps. A soft ticking. Then silence.
3. She creeps downstairs. The room is empty. The front door is locked.
4. Just the old house settling, she tells herself.
5. But the next night, it happens again. And the next.
6. Clue one. Nothing is ever stolen.
7. Clue two. The lock is never broken. Whoever comes in has a key.
8. Clue three. The old clock in the hall came with the house. She never winds it. It never stops.
9. So who walks into a stranger's house every night, just to touch a clock?
10. Emma hides a camera on the bookshelf, and waits.
11. 3 a.m. The door opens. An old man steps inside, in his slippers.
12. He walks straight to the clock and winds it. Slowly. Carefully.
13. Then he pats the wood, like saying goodnight, and leaves.
14. The next morning, Emma knocks on the house next door.
15. He lived in her house for forty years. The clock was his late wife's. He promised her it would never stop.
16. He sold the house. He kept the key. And he kept his promise.
17. It was never a burglar. It was a man keeping his word.
18. Now, at 3 a.m., when Emma hears a click downstairs, she just smiles, and goes back to sleep.

## Hook map (~every 10 s)
0 s click downstairs at 3 a.m. · ~8 s empty room, door locked · ~14 s "house settling" killed · ~18-30 s clues (the clock that never stops) · ~32 s riddle · ~38 s the door opens on camera · ~45 s he winds the clock · ~52 s the promise · ~60 s flip + loop.

## Visual bible (for the Animator)
- Characters: **Emma** (white stickman, 30s, swept hair, label EMMA), **the old man** (white stickman, 70s, glasses, white hair, cardigan, slippers, label NEIGHBOUR). `stickman.FACE_STYLE = 'ref'` + bigger-head proportions; big expressive close-ups.
- Set: one cosy old two-storey house: upstairs bedroom, staircase with banister (foreground blur), hall with a **tall wooden grandfather clock** (the hero object, warm brass pendulum, in many shots), living room with bookshelf, front door with an old brass lock; the neighbour's porch by day. Real perspective (`flat2d/persp.py`, `cine.py`, room kit in `flat2d/style_test_rooms*.py`).
- Light: night = deep blues + one warm practical (moonlight through a window, a hall lamp, the clock's brass glint); day = warm high-key `STORY` grade. Camera moves through the house with almost no hard cuts; low angle up the stairs, peephole/POV from the top step, a grainy camera-feed look for the reveal.
- Key beats: s01 bedroom 3:00 on the bedside clock, Emma's eyes open; s02 sound waves from below, the ticking; s03 down the stairs, empty room, locked door; s04 chip HOUSE SETTLING? gets an X; s05 nights passing (moon, 3:00 again); s06-s08 CLUE cards in the set (purse untouched; lock intact + key icon; the clock pendulum swinging, nobody winding it); s09 big ? over the clock; s10 hiding the camera on the bookshelf; s11 camera-feed view: the door opens, the old man in slippers; s12 he winds the clock; s13 he pats it and leaves; s14 day, Emma knocks next door; s15 warm flashback: the man and his wife young beside the same clock, her hand on his; s16 the key in his palm; s17 flip title NOT A BURGLAR. / A PROMISE. (yellow); s18 3 a.m., a click, Emma smiles and closes her eyes; last frame = frame 0 (loop).
