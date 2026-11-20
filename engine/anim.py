# Timing, easing, character acting and camera maths for the engine. Pure functions: no drawing here.
# Principles (stickman/DRAWING_RULES.md 20-29, references/reports/motion.md):
#   - beats land LEAD frames before their word; expression swaps are 1-frame swaps hidden under a blink;
#   - every action: anticipation (opposite move) -> action with ease -> overshoot (out_back) -> settle;
#   - transitions that would cross limbs go in stages (via 'hang');
#   - moving holds: blinks every 0.5-2.3 s (half/shut/shut/half) + very subtle breathing anchored at the soles;
#   - no sliding: x changes are made of small hops (feet off the ground while travelling) until wardrobe ships a walk.
import math, random

FPS = 30
W, H = 1080, 1920
RIG_OK = False           # set by the renderer when bean.py supports rig=/view=
LEAD = 2                 # beats land 2 frames before the word onset (reference 0-3 f)
ANTIC = 3                # anticipation frames before a pose swap
SETTLE = 8               # overshoot + settle frames after a pose swap
TAIL = 0.8               # seconds of picture after the last word


# ---------------------------------------------------------------- easing
def clamp(t, a=0.0, b=1.0): return a if t < a else b if t > b else t
def lerp(a, b, t): return a + (b - a) * t
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def smoother(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def out_cubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def in_quad(t): t = clamp(t); return t * t
def out_back(t, s=1.70158):
    t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1
def settle(n, amp, frames=SETTLE, s=2.2):
    """Overshoot bump after an action: 0 at n=0, peaks ~amp a few frames later, back to 0 at n=frames."""
    if n < 0 or n >= frames: return 0.0
    u = n / frames
    return amp * (out_back(u, s) - smooth(u))   # out_back overshoots 1, smooth reaches 1: the difference is the overshoot


# ---------------------------------------------------------------- words <-> shots
def word_frame(w): return int(round(w['start'] * FPS))


def shot_spans(shots, words):
    """Assign each shot its word range (by counting the words of its `text`, or an explicit "words": [a, b])
    and its frame range. Shot k starts LEAD frames before its first word (shot 0 at frame 0)."""
    spans, i = [], 0
    for s in shots:
        if 'words' in s: a, b = s['words']
        else:
            n = len(s.get('text', '').split()); a, b = i, i + n
        spans.append([a, b]); i = b
    if spans and spans[-1][1] > len(words):
        raise SystemExit(f'shots.json has {spans[-1][1]} words of text but words.json has {len(words)}')
    out = []
    for k, (a, b) in enumerate(spans):
        f0 = 0 if k == 0 else max(0, word_frame(words[a]) - LEAD)
        if k + 1 < len(spans): f1 = max(f0 + 1, word_frame(words[spans[k + 1][0]]) - LEAD)
        else: f1 = int(math.ceil((words[b - 1]['end'] + TAIL) * FPS)) if b > a else f0 + 2 * FPS
        out.append({'w0': a, 'w1': b, 'f0': f0, 'f1': f1})
    return out


def beat_frame(shot_words, words, at_word):
    """Global frame a beat lands on: LEAD frames before the onset of word `at_word` (index within the shot)."""
    a, b = shot_words
    i = min(b - 1, a + int(at_word)) if b > a else a
    return word_frame(words[i]) - LEAD, word_frame(words[i])


# ---------------------------------------------------------------- arm poses
# bean.py arm poses per arm: hang, wave, point, hold, hip, chin. Engine pose names -> (screen-left arm, screen-right arm).
# 'point', 'wave' and 'think' use the arm on the side the character faces.
NAMED = {'idle': ('hang', 'hang'), 'hang': ('hang', 'hang'), 'hold': ('hold', 'hold'), 'hips': ('hip', 'hip'),
         'akimbo': ('hip', 'hip'), 'cheer': ('wave', 'wave'), 'shrug': ('hip', 'hip'), 'present': ('hang', 'point')}
ONE_ARM = {'point': 'point', 'wave': 'wave', 'think': 'chin', 'chin': 'chin', 'hip': 'hip', 'hold_one': 'hold'}
FRONT = {'hold', 'chin'}           # arms drawn in front of the body


def arm_pair(pose, facing=0.0):
    if isinstance(pose, (list, tuple)): return tuple(pose)
    if pose in NAMED: return NAMED[pose]
    if pose in ONE_ARM:
        a = ONE_ARM[pose]
        return (a, 'hang') if facing < -0.05 else ('hang', a)
    raise ValueError(f'unknown pose {pose!r}; known: {sorted(set(NAMED) | set(ONE_ARM))} or [left, right]')


def staged(prev, new):
    """Rule 26: an arm going between a 'front' pose and a raised/out pose passes through 'hang' first."""
    mid = []
    for p, n in zip(prev, new):
        cross = (p in FRONT) != (n in FRONT) and p != 'hang' and n != 'hang' or (p in FRONT and n in FRONT and p != n)
        mid.append('hang' if cross else p)
    return tuple(mid)


# ---------------------------------------------------------------- blinks
LID = (0.5, 1.0, 1.0, 0.5)


def blink_schedule(seed, f0, f1):
    """Frames where a blink starts: gaps 0.5-2.3 s (reference), seeded per character."""
    rnd = random.Random(seed); starts = []
    f = f0 + int(rnd.uniform(0.3, 1.6) * FPS)
    while f < f1:
        starts.append(f); f += int((0.5 + 1.8 * rnd.random()) * FPS) + 4
    return starts


def lid_at(f, starts):
    for s in starts:
        if 0 <= f - s < 4: return LID[f - s]
    return 0.0


# ---------------------------------------------------------------- character track
def screen_side(view):
    """Rider-side (shots.json convention) -> screen sign: a character facing us has their left on screen right."""
    return 1.0 if view in ('rear', 'back') else -1.0


def normalize_beat(b, view):
    """Map the real shots.json beat fields onto engine state keys.
    arm_pose [rider_left, rider_right] -> pose (screen-left, screen-right); lean / body_lean (deg, negative = rider's left)
    -> screen lean (deg, + = top toward screen right)."""
    b = dict(b); sg = screen_side(view)
    if 'arm_pose' in b:
        ap = b.pop('arm_pose')
        if isinstance(ap, (list, tuple)): b['pose'] = tuple(ap) if sg > 0 else (ap[1], ap[0])
        else: b['pose'] = (ap, ap)
    for k in ('body_lean', 'lean'):
        if k in b and b[k] is not None: b['hold_lean'] = float(b.pop(k)) * sg
    # broom on the palm (wardrobe props): flick the hand one way -> the broom tips the other way a little; then tip
    if 'broom_flick' in b:
        d = b.pop('broom_flick'); b['prop'] = 'broom:%d' % (-8 if d == 'right' else 8); b.setdefault('action', 'jolt')
    if 'broom_tip' in b:
        b['prop'] = 'broom_tip_%s' % b.pop('broom_tip')
    return b


class Track:
    """The acting of one character through one shot, computed up-front so every frame is a pure lookup."""

    def __init__(self, spec, shot_span, words, seed, plate_w=W):
        self.spec = spec; self.f0, self.f1 = shot_span['f0'], shot_span['f1']
        sw = (shot_span['w0'], shot_span['w1'])
        self.facing0 = float(spec.get('facing', 0.0))
        self.x0 = float(spec.get('x', 0.5))
        view = spec.get('view', 'front')
        if 'arm_pose' in spec: spec = dict(spec, **{k: v for k, v in normalize_beat({'arm_pose': spec['arm_pose']}, view).items()})
        st = {'pose': spec.get('pose', 'idle'), 'expr': spec.get('expr', 'neutral'), 'facing': self.facing0,
              'prop': spec.get('prop'), 'hold_lean': 0.0}
        self.events = []         # (land frame, word frame, beat dict, state before)
        self.blinks = blink_schedule(seed, self.f0 - 60, self.f1 + 60)
        for b in sorted(spec.get('beats', []), key=lambda b: b.get('at_word', 0)):
            b = normalize_beat(b, view)
            land, wf = beat_frame(sw, words, b.get('at_word', 0))
            if 'at_frame_offset' in b: land += int(b['at_frame_offset'])
            prev = dict(st)
            for k in ('pose', 'expr', 'facing', 'prop', 'hold_lean'):
                if k in b: st[k] = b[k]
            if land <= self.f0 + 1:          # a beat on the shot's first word sets the starting state
                self.facing0 = float(st['facing']); st0 = dict(st)
                spec = dict(spec, pose=st0['pose'], expr=st0['expr'], prop=st0['prop'], hold_lean=st0['hold_lean']); self.spec = spec
                if 'x' in b: self.x0 = float(b['x'])
                continue
            self.events.append({'land': land, 'word': wf, 'beat': b, 'prev': prev, 'new': dict(st)})
            if b.get('expr') and b['expr'] != prev['expr']:
                self.blinks.append(land - 1)        # shut frames (land, land+1) hide the expression swap
        self.blinks.sort()
        # no bike rig in bean.py yet: a 20-34 deg bike lean on a standing figure tips it over, so scale it down
        self.rig = bool(spec.get('rig')) and RIG_OK
        # without a bike rig a 20-34 deg bike lean on a standing figure tips it over: scale it down; with a rig the
        # lean goes to bikes.ride() instead and the card itself is not rotated
        self.lean_k, self.lean_max = (0.0, 0.0) if self.rig else (0.3, 8.0) if spec.get('rig') else (1.0, 90.0)
        self._rig_track(spec, shot_span, words)
        self.start = {'pose': self.spec.get('pose', 'idle'), 'expr': self.spec.get('expr', 'neutral'), 'facing': self.facing0,
                      'prop': self.spec.get('prop'), 'hold_lean': float(self.spec.get('hold_lean', 0.0))}
        self._moves()

    # x travel: hop-steps between x targets, ending on the beat's landing frame
    def _moves(self):
        self.moves = []; x = self.x0
        for e in self.events:
            if 'x' in e['beat']:
                nx = float(e['beat']['x']); d = nx - x
                if abs(d) > 1e-4:
                    n = max(1, int(math.ceil(abs(d) / 0.07)))          # ~0.07 frame widths per hop
                    hop = 9                                              # frames per hop
                    end = e['land']; start = end - n * hop
                    self.moves.append((start, end, x, nx, n, hop))
                x = nx

    def x_at(self, f):
        x = self.x0; lift = 0.0
        for start, end, xa, xb, n, hop in self.moves:
            if f >= end: x = xb
            elif f >= start:
                k = (f - start) // hop; u = ((f - start) % hop) / hop
                x = lerp(xa, xb, (k + smooth(u)) / n)
                lift = 4 * u * (1 - u)                                   # 0 at each contact, 1 mid-air
                return x, lift, True
        return x, lift, False

    def state_at(self, f):
        """pose pair, expr, facing, lean (deg, + = toward screen right), lift (fraction of height), lid, grounded."""
        st = dict(self.start); lean = 0.0; lift = 0.0; grounded = True
        pose = arm_pair(st['pose'], st['facing'])
        for e in self.events:
            land = e['land']; n = f - land
            if f < land - ANTIC - 2: break
            prev_pose = arm_pair(e['prev']['pose'], e['prev']['facing']); new_pose = arm_pair(e['new']['pose'], e['new']['facing'])
            pose_change = prev_pose != new_pose
            b = e['beat']; side = 1.0 if (e['new']['facing'] >= 0) else -1.0
            if n < 0:
                # anticipation: lean away from the coming action, ease in
                react = b.get('expr') and b['expr'] != e['prev']['expr']
                if pose_change or b.get('action') or react:   # every beat moves the body (expression-only: smaller)
                    lean += (-2.2 if pose_change else -1.2) * side * smooth((n + ANTIC + 1) / (ANTIC + 1))
                mid = staged(prev_pose, new_pose)
                if mid != prev_pose and n >= -2: pose = mid           # staged transition: 2 frames through the mid pose
                # turn: facing eases over the 3 frames before landing
                if e['new']['facing'] != e['prev']['facing'] and n >= -3:
                    st['facing'] = lerp(float(e['prev']['facing']), float(e['new']['facing']), smooth((n + 4) / 4))
                continue
            st.update(e['new']); pose = new_pose
            if pose_change or b.get('action'):
                lean += settle(n, 4.0 * side, SETTLE + 2)                 # overshoot toward the action, settle
            elif b.get('expr') and b['expr'] != e['prev']['expr']:
                lean += settle(n, 2.0 * side)                             # reaction: a small body take
        lean += self.hold_lean_at(f)
        # actions (hop / jolt / shrug / shake / nod) on top
        for e in self.events:
            a = e['beat'].get('action'); n = f - e['land']
            if not a: continue
            if a == 'hop':                     # crouch-free hop: lift off on the beat, 10 f airtime, land with a lean settle
                if 0 <= n < 10: lift += 0.10 * 4 * (n / 10) * (1 - n / 10); grounded = False
            elif a == 'jolt':                  # surprise: small fast pop up (4 f) then drop back
                if 0 <= n < 6: lift += 0.035 * math.sin(math.pi * n / 6); grounded = n == 0
            elif a == 'shake':                 # shiver: lean flips every 2 f for 12 f
                if 0 <= n < 12: lean += 1.4 * (1 if (n // 2) % 2 else -1) * (1 - n / 12)
            elif a == 'lean':
                lean += float(e['beat'].get('deg', 6)) * (smooth(n / 6) if n >= 0 else 0)
        x, hop_lift, moving = self.x_at(f)
        if moving: lift += 0.04 * hop_lift; grounded = hop_lift < 1e-6; lean += 2.0 * (1 if self._dir(f) > 0 else -1)
        lid = lid_at(f, self.blinks)
        if str(st.get('prop') or '').startswith('broom'):      # a balanced broom sits on a palm at shoulder height
            pose = tuple('palm' if p_ == 'hold' else p_ for p_ in pose)
            if 'palm' not in pose: pose = (pose[0], 'palm')
        return {'rig': self.rig_at(f) if self.rig else None, 'pose': pose, 'expr': st['expr'], 'prop': st.get('prop'), 'facing': round(float(st['facing']), 2), 'lean': lean,
                'lift': lift, 'grounded': grounded, 'lid': lid, 'x': x, 'moving': moving}

    RIG_KEYS = ('lean', 'body_lean', 'bike_lean', 'steer')

    def _rig_track(self, spec, span, words):
        """Rider-side rig values per beat (raw shots.json signs; bikes.ride() handles the view)."""
        sw = (span['w0'], span['w1']); cur = {k: None for k in self.RIG_KEYS}; cur['knee_out'] = False; cur['contact_shift'] = None
        self.rig_keys = []                                   # (land, before, after)
        for b in sorted(spec.get('beats', []), key=lambda b: b.get('at_word', 0)):
            land, _ = beat_frame(sw, words, b.get('at_word', 0)); prev = dict(cur)
            for k in self.RIG_KEYS + ('knee_out', 'contact_shift'):
                if k in b: cur[k] = b[k]
            if land <= self.f0 + 1: self.rig0 = dict(cur); continue
            if cur != prev: self.rig_keys.append((land, prev, dict(cur)))
        if not hasattr(self, 'rig0'): self.rig0 = {k: None for k in self.RIG_KEYS}; self.rig0.update(knee_out=False, contact_shift=None)

    def rig_at(self, f):
        """Eased rig values: 2 f lean-back anticipation, out_back overshoot over SETTLE frames, and an automatic
        countersteer: before every lean change the bars flick the OTHER way (the video's whole point), peaking 5 f
        before the lean lands; held leans steer gently into the turn."""
        v = {k: (float(self.rig0[k]) if self.rig0[k] is not None else None) for k in self.RIG_KEYS}
        v['knee_out'] = self.rig0['knee_out']; flick = 0.0
        for land, a, b in self.rig_keys:
            n = f - land
            if n < -12: break
            for k in self.RIG_KEYS:
                if b[k] is None or a[k] == b[k]: continue
                va = float(a[k] or 0.0); vb = float(b[k])
                if n < 0: v[k] = va - 0.08 * (vb - va) * smooth((n + 3) / 3) if n >= -2 else va
                else: v[k] = vb if n >= SETTLE else lerp(va, vb, out_back(n / SETTLE, 1.3))
                if k in ('lean', 'bike_lean') and abs(vb - va) > 5 and b.get('steer') is None:
                    flick += -math.copysign(min(10.0, 0.4 * abs(vb - va)), vb - va) * math.sin(math.pi * clamp((n + 12) / 14))
            if n >= 0: v['knee_out'] = b['knee_out']
        # contact_shift: the tyres slide out sideways under the rider (rider side). The contact patch moves out by
        # ~16 % of the figure height and the bike tips the other way about the rider's head; it hands over to the next
        # lean beat, which takes the bike the rest of the way.
        v['contact_dx'] = 0.0
        for j, (land, a, b) in enumerate(self.rig_keys):
            if b.get('contact_shift') and b['contact_shift'] != a.get('contact_shift'):
                n = f - land
                if n < 0: break
                sg = 1.0 if b['contact_shift'] == 'right' else -1.0
                nxt = next((l2 for l2, a2, b2 in self.rig_keys[j + 1:] if b2['lean'] != a2['lean'] or b2['bike_lean'] != a2['bike_lean']), None)
                k_in = out_back(n / 6, 1.4); k_out = 1 - smooth((f - nxt + 3) / SETTLE) if nxt is not None and f >= nxt - 3 else 1.0
                amt = k_in * max(0.0, k_out)
                v['contact_dx'] += 0.16 * sg * amt
                key = 'lean' if v['lean'] is not None or v['bike_lean'] is None else 'bike_lean'
                v[key] = (v[key] or 0.0) - sg * 10.0 * amt
        tot = v['lean'] if v['lean'] is not None else (v['bike_lean'] or 0.0)
        if v['steer'] is None: v['steer'] = flick + max(-5.0, min(5.0, 0.15 * tot))
        return v

    def hold_lean_at(self, f):
        v = self._hold_lean_at(f) * self.lean_k
        return max(-self.lean_max, min(self.lean_max, v))

    def _hold_lean_at(self, f):
        v = float(self.start['hold_lean'])
        for e in self.events:
            a, b = float(e['prev']['hold_lean']), float(e['new']['hold_lean'])
            if a == b: continue
            n = f - e['land']
            if n < -ANTIC: break
            if n < 0: return a - 0.12 * (b - a) * smooth((n + ANTIC + 1) / (ANTIC + 1))      # lean back a little first
            u = n / SETTLE
            v = b if u >= 1 else lerp(a, b, out_back(u, 1.3))
        return v

    def _dir(self, f):
        for start, end, xa, xb, n, hop in self.moves:
            if start <= f < end: return xb - xa
        return 0


# ---------------------------------------------------------------- camera
def kick(n):
    """Impact kick (reference v14): sign flips every frame, decays over 7 f. Returns unit offset."""
    if n < 0 or n >= 7: return 0.0
    return (1 if n % 2 == 0 else -1) * (1 - n / 7) ** 1.5


class Camera:
    """Per-shot virtual camera over the composited plate: zoom about a focus point, pan, roll, kicks.
    shots.json "camera": {"move": "push_in"|"hold"|"pull_out"|"glide", "amount": 0.05, "focus": [x, y] (fractions),
                          "to": {"zoom":1.2,"x":0.5,"y":0.45,"roll":3}, "at_word": n, "ease": "out"|"inout", "dur": 10,
                          "kick": [word, ...]}"""

    def __init__(self, cam, span, words, kicks=()):
        self.c = cam or {}; self.f0, self.f1 = span['f0'], span['f1']
        sw = (span['w0'], span['w1'])
        c = self.c
        fx, fy = c.get('focus', (0.5, 0.48))
        self.base = {'zoom': float(c.get('zoom', 1.0)), 'x': fx, 'y': fy, 'roll': float(c.get('roll', 0.0))}
        n = max(1, self.f1 - self.f0)
        mv = c.get('move', 'push_in')
        amt = float(c.get('amount', min(0.06, 0.0012 * n)))   # default: slow push ~0.12 %/f, capped at 6 % per shot
        # 'hold' still breathes: the reference camera is almost never dead still (0.14 %/f median push in quiet frames)
        self.push = {'push_in': amt, 'pull_out': -amt, 'hold': min(0.06, 0.0015 * n)}.get(mv, 0.0)
        # directional moves from shots.json: glide / follow / pan (x) and tilt_up / tilt_down (y), "amount" = frame fraction
        self.travel = None
        if mv in ('glide', 'follow', 'pan', 'tilt_up', 'tilt_down') and 'to' not in c and 'glides' not in c:
            a = float(c.get('amount', 0.06)); self.push = 0.0
            self.base['zoom'] = max(self.base['zoom'], 1 + a + 0.01)
            m = 0.5 - 0.5 / self.base['zoom']                       # largest centre offset that shows no border
            sg = -1.0 if c.get('direction') in ('left', 'up') or mv == 'tilt_up' else 1.0
            axis = 'y' if mv.startswith('tilt') else 'x'
            if mv == 'pan':
                land, _ = beat_frame(sw, words, c.get('at_word', 0)); f_a, f_b = land - 6, land + 22
            else: f_a, f_b = self.f0, self.f1
            self.travel = (axis, -sg * m, sg * m, f_a, f_b, 'smoother' if mv != 'follow' else 'linear')
            self.push = min(0.05, 0.0012 * n)                     # alive before a pan starts and while a tilt eases in
        if mv == 'shake':                                           # nervous handheld beat: small kicks every ~8 f
            self.push = 0.02; self.shake = float(c.get('amount', 0.01)) / 0.01 * 0.5
        else: self.shake = 0.0
        self.glides = []
        for g in c.get('glides', [c] if mv == 'glide' and 'to' in c else []):
            land, wf = beat_frame(sw, words, g.get('at_word', 0))
            self.glides.append((land, int(g.get('dur', 10)), g.get('to', {}), g.get('ease', 'out')))
        self.kicks = sorted(set(kicks) | {beat_frame(sw, words, k)[1] for k in c.get('kick', [])})
        if self.kicks or self.shake: self.base['zoom'] = max(self.base['zoom'], 1.02)   # at zoom 1 the border clamp eats any shake

    def at(self, f):
        n = f - self.f0; L = max(1, self.f1 - self.f0)
        z = self.base['zoom']; x, y, r = self.base['x'], self.base['y'], self.base['roll']
        # glides: ease-out (fastest on the first frame, decaying over `dur`) or symmetric ease-in-out
        for land, dur, to, ease in self.glides:
            k = 0.0
            if f >= land:
                u = (f - land + 1) / dur
                k = out_cubic(u) if ease == 'out' else smoother(u)
            z = lerp(z, float(to.get('zoom', z)), k); x = lerp(x, float(to.get('x', x)), k)
            y = lerp(y, float(to.get('y', y)), k); r = lerp(r, float(to.get('roll', r)), k)
        if self.travel:
            axis, a0, a1, f_a, f_b, ease = self.travel
            u = seg(f, f_a, f_b); u = smoother(u) if ease == 'smoother' else 0.15 * smooth(u / 0.15) if u < 0.15 else u
            off = lerp(a0, a1, u)
            if axis == 'x': x = 0.5 + off
            else: y = 0.5 + off
        # slow push across the shot; it stops at the first impact
        stop = next((kf for kf in self.kicks if kf >= self.f0), None)
        pn = min(n, stop - self.f0) if stop is not None and f >= stop else n
        z *= 1 + self.push * clamp(pn / L)
        kx = ky = kr = 0.0
        if self.shake:
            a = self.shake * kick((f - self.f0) % 9) * 0.7; kx += 4.5 * a; ky += 2.7 * a
        for kf in self.kicks:
            a = kick(f - kf); kx += 4.5 * a; ky += 2.7 * a; kr += 0.23 * a
        return {'zoom': max(0.2, z), 'x': x, 'y': y, 'roll': r + kr, 'dx': kx, 'dy': ky}
