# Engine QA

1971 frames (65.70 s), 22 shots

- [x] **no black spans >= 12 f**: PASS []
- [x] **no white spans >= 12 f**: PASS []
- [x] **no frozen spans >= 12 f**: PASS [] (median frame diff 1.11 grey levels)
- [x] **no character clipped at the frame edge**: PASS 0 frames; first: []
- [x] **feet on the ground line (+-4 px)**: PASS 0 frames; worst: []
- [ ] **planted feet move <= 2 px**: FAIL 4 frames; first: [(1230, 'kip', 'foot_l', 13.5), (1230, 'kip', 'foot_r', -16.0), (1230, 'lou', 'foot_l', 16.0), (1230, 'lou', 'foot_r', -13.5)]
- [x] **beats land 0-3 f before their word**: PASS 26 beats; off: []
- [x] **captions land 0-2 f before their word**: PASS 146 captions; off: []
- [x] **no caption during silences > 0.4 s**: PASS 0 frames; first: []
- [x] **captions never cover a face**: PASS 0 frames; first: []
- [i] frame stats (reference targets, warning only): 10/66 sampled frames pass
- [x] **mp4 is 1080x1920, 30 fps, frame count matches**: PASS {'width': 1080, 'height': 1920, 'r_frame_rate': '30/1', 'nb_frames': '1971'}

## Frame stats (1 per second)
```
f_00000.jpg lum=0.47 p98=0.85 sat=0.56 cool=0.18 edge=0.06 FAIL sat
f_00030.jpg lum=0.48 p98=0.85 sat=0.55 cool=0.15 edge=0.07 FAIL sat
f_00060.jpg lum=0.52 p98=0.79 sat=0.58 cool=0.30 edge=0.06 FAIL p98,sat
f_00090.jpg lum=0.52 p98=0.84 sat=0.58 cool=0.41 edge=0.05 FAIL p98,sat,cool
f_00120.jpg lum=0.54 p98=0.88 sat=0.54 cool=0.43 edge=0.03 FAIL sat,cool,edge
f_00150.jpg lum=0.51 p98=0.85 sat=0.54 cool=0.37 edge=0.04 FAIL p98,sat,cool,edge
f_00180.jpg lum=0.53 p98=0.86 sat=0.50 cool=0.39 edge=0.04 FAIL cool
f_00210.jpg lum=0.51 p98=0.87 sat=0.50 cool=0.42 edge=0.04 FAIL cool
f_00240.jpg lum=0.50 p98=0.87 sat=0.50 cool=0.43 edge=0.05 FAIL sat,cool
f_00270.jpg lum=0.52 p98=0.88 sat=0.43 cool=0.07 edge=0.02 FAIL edge
f_00300.jpg lum=0.51 p98=0.86 sat=0.43 cool=0.04 edge=0.02 FAIL edge
f_00330.jpg lum=0.50 p98=0.89 sat=0.58 cool=0.48 edge=0.04 FAIL sat,cool,edge
f_00360.jpg lum=0.50 p98=0.89 sat=0.58 cool=0.48 edge=0.04 FAIL sat,cool,edge
f_00390.jpg lum=0.50 p98=0.76 sat=0.47 cool=0.51 edge=0.04 FAIL p98,cool
f_00420.jpg lum=0.53 p98=0.86 sat=0.44 cool=0.46 edge=0.05 FAIL cool
f_00450.jpg lum=0.53 p98=0.95 sat=0.43 cool=0.46 edge=0.06 FAIL cool
f_00480.jpg lum=0.51 p98=0.82 sat=0.45 cool=0.53 edge=0.04 FAIL p98,cool
f_00510.jpg lum=0.39 p98=0.86 sat=0.45 cool=0.51 edge=0.04 FAIL lum,cool
f_00540.jpg lum=0.40 p98=0.89 sat=0.44 cool=0.46 edge=0.04 FAIL cool,edge
f_00570.jpg lum=0.40 p98=0.89 sat=0.44 cool=0.45 edge=0.04 FAIL cool
f_00600.jpg lum=0.40 p98=0.88 sat=0.56 cool=0.16 edge=0.03 FAIL sat,edge
f_00630.jpg lum=0.51 p98=0.87 sat=0.58 cool=0.10 edge=0.02 FAIL sat,edge
f_00660.jpg lum=0.26 p98=0.70 sat=0.69 cool=0.06 edge=0.05 FAIL lum,p98,sat
f_00690.jpg lum=0.45 p98=0.87 sat=0.49 cool=0.25 edge=0.10 PASS
f_00720.jpg lum=0.45 p98=0.86 sat=0.48 cool=0.24 edge=0.10 PASS
f_00750.jpg lum=0.47 p98=0.89 sat=0.44 cool=0.07 edge=0.07 PASS
f_00780.jpg lum=0.50 p98=0.87 sat=0.42 cool=0.03 edge=0.04 FAIL edge
f_00810.jpg lum=0.52 p98=0.88 sat=0.41 cool=0.03 edge=0.04 PASS
f_00840.jpg lum=0.48 p98=0.87 sat=0.42 cool=0.01 edge=0.03 FAIL edge
f_00870.jpg lum=0.49 p98=0.92 sat=0.39 cool=0.04 edge=0.04 PASS
f_00900.jpg lum=0.47 p98=0.92 sat=0.41 cool=0.05 edge=0.05 PASS
f_00930.jpg lum=0.41 p98=0.86 sat=0.44 cool=0.15 edge=0.11 PASS
f_00960.jpg lum=0.46 p98=0.88 sat=0.40 cool=0.10 edge=0.10 PASS
f_00990.jpg lum=0.49 p98=0.89 sat=0.56 cool=0.42 edge=0.04 FAIL sat,cool
f_01020.jpg lum=0.49 p98=0.88 sat=0.56 cool=0.44 edge=0.04 FAIL sat,cool
f_01050.jpg lum=0.48 p98=0.91 sat=0.55 cool=0.44 edge=0.05 FAIL sat,cool
f_01080.jpg lum=0.44 p98=0.47 sat=0.47 cool=0.97 edge=0.01 FAIL p98,cool,edge
f_01110.jpg lum=0.45 p98=0.85 sat=0.45 cool=0.94 edge=0.01 FAIL cool,edge
f_01140.jpg lum=0.43 p98=0.99 sat=0.39 cool=0.35 edge=0.08 FAIL cool
f_01170.jpg lum=0.43 p98=0.89 sat=0.40 cool=0.34 edge=0.04 FAIL edge
f_01200.jpg lum=0.34 p98=0.79 sat=0.56 cool=0.54 edge=0.04 FAIL lum,p98,sat,cool,edge
f_01230.jpg lum=0.46 p98=0.86 sat=0.45 cool=0.94 edge=0.01 FAIL cool,edge
f_01260.jpg lum=0.51 p98=0.92 sat=0.48 cool=0.39 edge=0.04 FAIL cool
f_01290.jpg lum=0.45 p98=0.91 sat=0.46 cool=0.18 edge=0.05 PASS
f_01320.jpg lum=0.51 p98=0.91 sat=0.47 cool=0.37 edge=0.06 FAIL cool
f_01350.jpg lum=0.49 p98=0.91 sat=0.46 cool=0.26 edge=0.05 PASS
f_01380.jpg lum=0.42 p98=0.86 sat=0.34 cool=0.23 edge=0.09 FAIL sat
f_01410.jpg lum=0.42 p98=0.86 sat=0.34 cool=0.28 edge=0.09 FAIL sat
f_01440.jpg lum=0.42 p98=0.85 sat=0.34 cool=0.30 edge=0.09 FAIL sat
f_01470.jpg lum=0.42 p98=0.85 sat=0.34 cool=0.30 edge=0.09 FAIL sat
f_01500.jpg lum=0.51 p98=0.69 sat=0.53 cool=0.99 edge=0.02 FAIL p98,sat,cool,edge
f_01530.jpg lum=0.52 p98=0.84 sat=0.53 cool=0.92 edge=0.03 FAIL p98,sat,cool,edge
f_01560.jpg lum=0.54 p98=0.90 sat=0.51 cool=0.87 edge=0.04 FAIL sat,cool
f_01590.jpg lum=0.54 p98=0.91 sat=0.52 cool=0.86 edge=0.04 FAIL sat,cool
f_01620.jpg lum=0.49 p98=0.90 sat=0.50 cool=0.37 edge=0.07 FAIL sat,cool
f_01650.jpg lum=0.40 p98=0.93 sat=0.41 cool=0.38 edge=0.06 FAIL cool
f_01680.jpg lum=0.41 p98=0.93 sat=0.39 cool=0.38 edge=0.07 FAIL cool
f_01710.jpg lum=0.50 p98=0.93 sat=0.33 cool=0.32 edge=0.07 FAIL sat
f_01740.jpg lum=0.53 p98=0.98 sat=0.36 cool=0.31 edge=0.04 FAIL edge
f_01770.jpg lum=0.51 p98=0.98 sat=0.34 cool=0.30 edge=0.04 FAIL sat,edge
f_01800.jpg lum=0.55 p98=0.87 sat=0.48 cool=0.42 edge=0.04 FAIL lum,cool
f_01830.jpg lum=0.53 p98=0.84 sat=0.51 cool=0.58 edge=0.04 FAIL p98,sat,cool,edge
f_01860.jpg lum=0.55 p98=0.86 sat=0.51 cool=0.50 edge=0.04 FAIL lum,sat,cool
f_01890.jpg lum=0.52 p98=0.83 sat=0.53 cool=0.42 edge=0.05 FAIL p98,sat,cool
f_01920.jpg lum=0.52 p98=0.88 sat=0.52 cool=0.39 edge=0.06 FAIL sat,cool
f_01950.jpg lum=0.52 p98=0.89 sat=0.51 cool=0.34 edge=0.06 FAIL sat
```

Contact sheets (every 0.5 s): contact_00.jpg, contact_01.jpg, contact_02.jpg
