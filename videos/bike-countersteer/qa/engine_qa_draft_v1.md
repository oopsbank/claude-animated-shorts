# Engine QA

1921 frames (64.03 s), 18 shots

- [x] **no black spans >= 12 f**: PASS []
- [x] **no white spans >= 12 f**: PASS []
- [x] **no frozen spans >= 12 f**: PASS [] (median frame diff 0.95 grey levels)
- [x] **no character clipped at the frame edge**: PASS 0 frames; first: []
- [x] **feet on the ground line (+-4 px)**: PASS 0 frames; worst: []
- [x] **planted feet move <= 2 px**: PASS 0 frames; first: []
- [x] **beats land 0-3 f before their word**: PASS 32 beats; off: []
- [i] frame stats (reference targets, warning only): 6/65 sampled frames pass
- [x] **mp4 is 1080x1920, 30 fps, frame count matches**: PASS {'width': 1080, 'height': 1920, 'r_frame_rate': '30/1', 'nb_frames': '1921'}

## Frame stats (1 per second)
```
f_00000.jpg lum=0.56 p98=0.91 sat=0.32 cool=0.23 edge=0.04 FAIL lum,sat
f_00030.jpg lum=0.55 p98=0.90 sat=0.32 cool=0.23 edge=0.03 FAIL lum,sat,edge
f_00060.jpg lum=0.55 p98=0.90 sat=0.32 cool=0.23 edge=0.03 FAIL lum,sat,edge
f_00090.jpg lum=0.55 p98=0.90 sat=0.33 cool=0.22 edge=0.04 FAIL sat,edge
f_00120.jpg lum=0.55 p98=0.90 sat=0.33 cool=0.22 edge=0.04 FAIL sat
f_00150.jpg lum=0.33 p98=0.96 sat=0.48 cool=0.22 edge=0.05 FAIL lum
f_00180.jpg lum=0.32 p98=0.90 sat=0.49 cool=0.23 edge=0.05 FAIL lum
f_00210.jpg lum=0.32 p98=0.90 sat=0.49 cool=0.23 edge=0.05 FAIL lum
f_00240.jpg lum=0.33 p98=0.90 sat=0.46 cool=0.23 edge=0.05 FAIL lum
f_00270.jpg lum=0.59 p98=0.87 sat=0.41 cool=0.24 edge=0.06 FAIL lum
f_00300.jpg lum=0.59 p98=0.87 sat=0.39 cool=0.21 edge=0.07 FAIL lum
f_00330.jpg lum=0.56 p98=0.86 sat=0.32 cool=0.31 edge=0.03 FAIL lum,sat,edge
f_00360.jpg lum=0.56 p98=0.86 sat=0.33 cool=0.32 edge=0.03 FAIL lum,sat,edge
f_00390.jpg lum=0.57 p98=0.86 sat=0.33 cool=0.34 edge=0.03 FAIL lum,sat,edge
f_00420.jpg lum=0.58 p98=0.86 sat=0.34 cool=0.36 edge=0.03 FAIL lum,sat,cool,edge
f_00450.jpg lum=0.59 p98=0.86 sat=0.35 cool=0.38 edge=0.03 FAIL lum,sat,cool,edge
f_00480.jpg lum=0.32 p98=0.94 sat=0.48 cool=0.23 edge=0.05 FAIL lum
f_00510.jpg lum=0.31 p98=0.89 sat=0.49 cool=0.23 edge=0.05 FAIL lum
f_00540.jpg lum=0.31 p98=0.86 sat=0.48 cool=0.23 edge=0.04 FAIL lum
f_00570.jpg lum=0.57 p98=0.95 sat=0.39 cool=0.30 edge=0.05 FAIL lum
f_00600.jpg lum=0.57 p98=0.95 sat=0.38 cool=0.27 edge=0.06 FAIL lum
f_00630.jpg lum=0.57 p98=0.95 sat=0.37 cool=0.25 edge=0.05 FAIL lum
f_00660.jpg lum=0.56 p98=0.95 sat=0.36 cool=0.23 edge=0.05 FAIL lum
f_00690.jpg lum=0.58 p98=0.95 sat=0.32 cool=0.27 edge=0.06 FAIL lum,sat
f_00720.jpg lum=0.57 p98=0.95 sat=0.40 cool=0.34 edge=0.06 FAIL lum
f_00750.jpg lum=0.57 p98=0.95 sat=0.40 cool=0.34 edge=0.06 FAIL lum
f_00780.jpg lum=0.57 p98=0.95 sat=0.40 cool=0.34 edge=0.06 FAIL lum
f_00810.jpg lum=0.58 p98=0.95 sat=0.39 cool=0.33 edge=0.06 FAIL lum
f_00840.jpg lum=0.50 p98=1.00 sat=0.39 cool=0.00 edge=0.05 PASS
f_00870.jpg lum=0.50 p98=1.00 sat=0.39 cool=0.00 edge=0.05 PASS
f_00900.jpg lum=0.50 p98=1.00 sat=0.38 cool=0.00 edge=0.06 PASS
f_00930.jpg lum=0.33 p98=0.95 sat=0.47 cool=0.21 edge=0.05 FAIL lum
f_00960.jpg lum=0.32 p98=0.90 sat=0.48 cool=0.21 edge=0.05 FAIL lum
f_00990.jpg lum=0.32 p98=0.85 sat=0.48 cool=0.22 edge=0.05 FAIL lum,p98
f_01020.jpg lum=0.62 p98=0.95 sat=0.35 cool=0.26 edge=0.04 FAIL lum,edge
f_01050.jpg lum=0.61 p98=0.95 sat=0.36 cool=0.26 edge=0.04 FAIL lum,edge
f_01080.jpg lum=0.60 p98=0.95 sat=0.36 cool=0.26 edge=0.04 FAIL lum,edge
f_01110.jpg lum=0.62 p98=0.96 sat=0.33 cool=0.01 edge=0.03 FAIL lum,sat,edge
f_01140.jpg lum=0.61 p98=0.96 sat=0.34 cool=0.01 edge=0.03 FAIL lum,sat,edge
f_01170.jpg lum=0.61 p98=0.96 sat=0.34 cool=0.01 edge=0.03 FAIL lum,sat,edge
f_01200.jpg lum=0.47 p98=0.97 sat=0.54 cool=0.00 edge=0.03 FAIL sat,edge
f_01230.jpg lum=0.60 p98=0.96 sat=0.34 cool=0.00 edge=0.05 FAIL lum,sat
f_01260.jpg lum=0.60 p98=0.96 sat=0.35 cool=0.00 edge=0.04 FAIL lum,sat,edge
f_01290.jpg lum=0.60 p98=0.96 sat=0.35 cool=0.00 edge=0.04 FAIL lum,sat,edge
f_01320.jpg lum=0.60 p98=0.96 sat=0.35 cool=0.00 edge=0.04 FAIL lum,sat,edge
f_01350.jpg lum=0.61 p98=0.96 sat=0.35 cool=0.00 edge=0.04 FAIL lum,edge
f_01380.jpg lum=0.60 p98=0.97 sat=0.31 cool=0.08 edge=0.02 FAIL lum,sat,edge
f_01410.jpg lum=0.59 p98=0.97 sat=0.32 cool=0.08 edge=0.02 FAIL lum,sat,edge
f_01440.jpg lum=0.59 p98=0.97 sat=0.32 cool=0.08 edge=0.02 FAIL lum,sat,edge
f_01470.jpg lum=0.58 p98=0.97 sat=0.33 cool=0.08 edge=0.03 FAIL lum,sat,edge
f_01500.jpg lum=0.58 p98=0.95 sat=0.38 cool=0.16 edge=0.03 FAIL lum,edge
f_01530.jpg lum=0.58 p98=0.95 sat=0.38 cool=0.15 edge=0.03 FAIL lum,edge
f_01560.jpg lum=0.53 p98=0.95 sat=0.43 cool=0.00 edge=0.08 PASS
f_01590.jpg lum=0.52 p98=0.95 sat=0.43 cool=0.01 edge=0.08 PASS
f_01620.jpg lum=0.30 p98=0.94 sat=0.47 cool=0.13 edge=0.04 FAIL lum
f_01650.jpg lum=0.29 p98=0.90 sat=0.48 cool=0.13 edge=0.04 FAIL lum
f_01680.jpg lum=0.28 p98=0.87 sat=0.48 cool=0.14 edge=0.04 FAIL lum
f_01710.jpg lum=0.28 p98=0.82 sat=0.48 cool=0.14 edge=0.04 FAIL lum,p98
f_01740.jpg lum=0.53 p98=0.95 sat=0.43 cool=0.00 edge=0.04 PASS
f_01770.jpg lum=0.48 p98=0.93 sat=0.46 cool=0.00 edge=0.04 FAIL edge
f_01800.jpg lum=0.30 p98=0.93 sat=0.47 cool=0.13 edge=0.05 FAIL lum
f_01830.jpg lum=0.29 p98=0.90 sat=0.48 cool=0.13 edge=0.05 FAIL lum
f_01860.jpg lum=0.29 p98=0.90 sat=0.48 cool=0.13 edge=0.05 FAIL lum
f_01890.jpg lum=0.29 p98=0.90 sat=0.48 cool=0.14 edge=0.05 FAIL lum
f_01920.jpg lum=0.29 p98=0.90 sat=0.48 cool=0.14 edge=0.05 FAIL lum
```

Contact sheets (every 0.5 s): contact_00.jpg, contact_01.jpg, contact_02.jpg
