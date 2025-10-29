# ----------------------------------------------------------
# Eight-car engine test with smooth stereo panning motion
# ----------------------------------------------------------
from pyo import *
import time, random, threading

# --- Boot stereo server ---
s = Server(audio="portaudio", nchnls=2, duplex=0).boot()
s.start()

ENGINE_FILE = "engine_clean.wav"
tbl = SndTable(ENGINE_FILE)

cars = []
for i in range(8):
    pitch = SigTo(value=random.uniform(0.4, 1.2), time=2.0)
    vol   = Sig(random.uniform(0.4, 0.7))

    loop  = Looper(tbl, pitch=pitch, mul=vol)

    # --- Add a slow stereo pan LFO per car ---
    # Each with a unique phase and speed so they drift independently
    pan_lfo = Sine(freq=random.uniform(0.03, 0.08),
                   phase=random.uniform(0, 1)).range(0.0, 1.0)

    pan = Pan(loop, outs=2, pan=pan_lfo)
    cars.append({"pitch": pitch, "vol": vol, "obj": pan})

# --- Mix all cars + gentle global reverb ---
mix = Mix([c["obj"] for c in cars], voices=2)
rev = Freeverb(mix, size=0.5, damp=0.4, bal=0.25).out()

print("Eight-car engine test with panning.  Press Ctrl+C to stop.")

# --- background thread for rev sweeps ---
def rev_sweep():
    while True:
        for c in cars:
            c["pitch"].value = random.uniform(0.4, 1.2)
            c["vol"].value   = random.uniform(0.4, 0.8)
        time.sleep(random.uniform(2.5, 5.0))

threading.Thread(target=rev_sweep, daemon=True).start()

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopping test...")

s.stop()
s.shutdown()
