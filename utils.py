# utils.py
TH1 = "#006FFF"   # blue
TH2 = "#FF9000"   # orange
TH3 = "#111111"   # dark background




def alpha(color, opacity=1.0):
    a = int(opacity * 255)
    return f"{color}{a:02X}"
