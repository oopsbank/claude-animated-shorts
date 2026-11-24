"""Caption-free thumbnail frame for Cat righting: the cat upside down in mid-air in Marey's 1894 lab (s01 frame 0,
HIDE_UI: no 1894 title / PARIS pill). Headline added by tools/thumbnail.py.

usage: .venv/bin/python flat2d/cat_righting_thumb.py OUT.png
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cat_righting as B

B.HIDE_UI = True
img, _ = B.s01_frame(.6, .6)
img.convert('RGB').save(sys.argv[1])
