import tkinter as tk
from tkinter import ttk, filedialog
import os, math, random, struct, subprocess
#source: https://github.com/zeittresor/py_gen_amiga_mod
period_table = [
    856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453,
    428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226,
    214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113
]

def generate_kick():
    length = 2000; data = []
    phase = 0.0
    for i in range(length):
        freq = 50.0 + (5.0 - 50.0) * (i / length)
        phase += 2 * math.pi * freq / 44100.0
        amp = 1.0 - i / length
        val = amp * math.sin(phase)
        if i < length / 20:
            val += 0.5 * math.sin(2 * math.pi * 2000 * (i / 44100.0))
        val = max(-1.0, min(1.0, val))
        data.append(int(val * 127) & 0xFF)
    return bytes(data)

def generate_snare():
    length = 1200; data = []
    for i in range(length):
        noise = random.uniform(-1, 1)
        envelope = math.exp(-5 * i / length)
        val = noise * envelope
        val = max(-1.0, min(1.0, val))
        data.append(int(val * 127) & 0xFF)
    return bytes(data)

def generate_hat():
    length = 300; data = []; prev = 0.0
    for i in range(length):
        noise = random.uniform(-1, 1)
        envelope = math.exp(-10 * i / length)
        val = (noise - prev) * envelope; prev = noise
        val = max(-1.0, min(1.0, val))
        data.append(int(val * 127) & 0xFF)
    return bytes(data)

def generate_clap():
    length = 250; data = []
    for i in range(length):
        noise = random.uniform(-1, 1)
        envelope = math.exp(-12 * i / length)
        val = noise * envelope
        val = max(-1.0, min(1.0, val))
        data.append(int(val * 127) & 0xFF)
    return bytes(data)

def generate_tusch():
    length = 300; data = []
    for i in range(length):
        t = i / 44100.0
        val = math.sin(2 * math.pi * 600 * t) * math.exp(-8 * i / length)
        val = max(-1.0, min(1.0, val))
        data.append(int(val * 127) & 0xFF)
    return bytes(data)

def generate_triangle_wave(cycles=1):
    spc = 32; data = []
    for i in range(spc * cycles):
        t = (i % spc) / spc
        val = 2 * abs(2 * t - 1) - 1
        val *= 0.8
        data.append(int(max(-1, min(1, val)) * 127) & 0xFF)
    return bytes(data)

def generate_sine_wave(cycles=1, harmonics=[]):
    spc = 32; data = []
    max_amp = 1 + sum(abs(a) for _, a in harmonics)
    for i in range(spc * cycles):
        t = (i % spc) / spc
        val = math.sin(2 * math.pi * t)
        for mul, amp in harmonics:
            val += amp * math.sin(2 * math.pi * mul * t)
        val /= max_amp
        data.append(int(max(-1, min(1, val)) * 127) & 0xFF)
    return bytes(data)

def generate_song_name():
    words = ["Cosmic", "Nebula", "Mystic", "Funky", "Electric", "Phantom", "Shadow", "Neon", "Bass", "Groove", "Quantum", "Retro", "Solar", "Pulse", "Echo", "Zenith", "Twilight", "Crimson", "Turbo", "Galaxy", "Spectrum", "Nova", "Phoenix", "Velocity", "Aurora", "Orbit", "Celestial", "Fusion", "Mirage", "Eclipse"]
    return " ".join(random.sample(words, 3))

def compose_mod(style, scale_name, key_name, start_octave, intro_patterns, main_patterns, outro_patterns, bpm, use_arpeggio, use_vibrato, use_tremolo, use_echo, use_filter):
    os.makedirs("output", exist_ok=True)
    styles_all = ["techno", "breakbeat", "acid", "drum & bass", "dubstep", "synthpop", "swing", "meditation", "ambient", "chill", "blues"]
    style_lower = style.lower()
    scales = {"Dur": [0,2,4,5,7,9,11], "Moll": [0,2,3,5,7,8,10], "Dorisch": [0,2,3,5,7,9,10], "Phrygisch": [0,1,3,5,7,8,10], "Lydisch": [0,2,4,6,7,9,11], "Mixolydisch": [0,2,4,5,7,9,10], "Lokrich": [0,1,3,5,6,8,10]}
    if scale_name not in scales:
        scale_name = "Dur"
    scale = scales[scale_name]
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_offset = note_names.index(key_name) if key_name in note_names else 0
    bass_oct = start_octave
    chord_oct = start_octave + 1
    lead_oct = start_octave + 2
    total_patterns = intro_patterns + main_patterns + outro_patterns
    total_measures = total_patterns * 4
    progression = [0] * total_measures
    if style_lower == "blues":
        twelve_bar = [0,0,0,0, 3,3, 0,0, 4,3, 0,4]
        for i in range(total_measures):
            progression[i] = twelve_bar[i % 12] if total_measures >= 12 else 0
    else:
        alt_degree = 5 if len(scale) >= 6 else (4 if len(scale) >= 5 else 0)
        for i in range(total_measures):
            progression[i] = 0 if i % 4 != 3 else alt_degree
    def get_chord(deg):
        root = scale[deg % len(scale)] + 12 * (deg // len(scale))
        third = scale[(deg + 2) % len(scale)] + 12 * ((deg + 2) // len(scale))
        fifth = scale[(deg + 4) % len(scale)] + 12 * ((deg + 4) // len(scale))
        return root, third, fifth
    patterns = [[[None for _ in range(4)] for _ in range(64)] for _ in range(total_patterns)]
    def set_event(pat, row, ch, inst=None, period_idx=None, effect_cmd=None, effect_param=None):
        if pat < 0 or pat >= total_patterns or row < 0 or row >= 64:
            return
        if patterns[pat][row][ch] is None:
            patterns[pat][row][ch] = {"inst": 0, "period": None, "effect": None, "param": None}
        if inst is not None:
            patterns[pat][row][ch]["inst"] = inst
            if period_idx is not None:
                patterns[pat][row][ch]["period"] = period_idx
        if effect_cmd is not None:
            patterns[pat][row][ch]["effect"] = effect_cmd & 0xF
            patterns[pat][row][ch]["param"] = effect_param & 0xFF if effect_param is not None else 0
    for pat in range(total_patterns):
        for meas in range(4):
            global_meas = pat * 4 + meas
            if global_meas >= total_measures:
                break
            root_deg = progression[global_meas]
            r, t, f = get_chord(root_deg)
            chord_root = r + key_offset + chord_oct * 12
            chord_third = t + key_offset + chord_oct * 12
            chord_fifth = f + key_offset + chord_oct * 12
            bass_root = r + key_offset + bass_oct * 12
            bass_alt = bass_root + 3 if bass_root + 3 <= 35 else bass_root
            if style_lower in ["techno", "acid", "drum & bass", "dubstep", "synthpop", "breakbeat"]:
                for beat in range(4):
                    row = meas * 16 + beat * 4
                    set_event(pat, row, 0, inst=1)
                    if beat == 1 or beat == 3:
                        set_event(pat, row, 1, inst=2)
                    if beat == 2:
                        set_event(pat, row, 0, inst=7)
                    hat_row = row + 2
                    set_event(pat, hat_row, 1, inst=3)
                    bass_row = row + 2
                    bass_choice = bass_root if beat % 2 == 0 else bass_alt
                    set_event(pat, bass_row, 0, inst=4, period_idx=min(35, max(0, bass_choice)))
                    if beat == 3:
                        set_event(pat, row, 1, inst=8)
            elif style_lower == "swing":
                for beat in range(4):
                    row = meas * 16 + beat * 4
                    if beat == 0 or beat == 2:
                        set_event(pat, row, 0, inst=1)
                    else:
                        set_event(pat, row, 0, inst=7)
                    if beat == 1 or beat == 3:
                        set_event(pat, row, 1, inst=2)
                    hat_row = row + 2
                    set_event(pat, hat_row, 1, inst=3)
                    bass_row = row + 2
                    set_event(pat, bass_row, 0, inst=4, period_idx=min(35, max(0, bass_root)))
            elif style_lower in ["meditation", "ambient", "chill"]:
                for beat in range(4):
                    row = meas * 16 + beat * 4
                    if beat == 0:
                        set_event(pat, row, 0, inst=1)
                    hat_row = row + 2
                    set_event(pat, hat_row, 1, inst=3)
                    if beat == 2:
                        set_event(pat, row, 1, inst=2)
                    bass_row = row + 2
                    set_event(pat, bass_row, 0, inst=4, period_idx=min(35, max(0, bass_root)))
            else:
                for beat in range(4):
                    row = meas * 16 + beat * 4
                    set_event(pat, row, 0, inst=1)
                    set_event(pat, row, 1, inst=2)
                    hat_row = row + 2
                    set_event(pat, hat_row, 1, inst=3)
                    bass_row = row + 2
                    set_event(pat, bass_row, 0, inst=4, period_idx=min(35, max(0, bass_root)))
            if style_lower == "blues":
                pass
            if pat >= intro_patterns and pat < intro_patterns + main_patterns:
                prob_note = 0.8 if style_lower != "blues" else 0.6
                last_pitch = None
                for sub in range(8):
                    sub_row = meas * 16 + sub * 2
                    if random.random() >= prob_note:
                        continue
                    if last_pitch is None:
                        choices = [chord_root, chord_third, chord_fifth]
                        pitch = random.choice(choices)
                    else:
                        poss = []
                        for oct_shift in range(lead_oct, lead_oct + 2):
                            for interval in scale:
                                note_val = interval + key_offset + oct_shift * 12
                                if abs(note_val - last_pitch) <= 5:
                                    poss.append(note_val)
                        pitch = random.choice(poss) if poss else last_pitch
                    pitch_idx = min(35, max(0, pitch))
                    set_event(pat, sub_row, 3, inst=6, period_idx=pitch_idx)
                    if use_vibrato:
                        set_event(pat, sub_row, 3, effect_cmd=0x4, effect_param=(8 << 4) | 2)
                    last_pitch = pitch_idx
    if use_echo:
        delay = 8 if style_lower == "blues" else 4
        for pat in range(total_patterns):
            for r in range(64):
                evt = patterns[pat][r][3]
                if evt and evt.get("inst") == 6:
                    total_idx = pat * 64 + r + delay
                    target_pat = total_idx // 64
                    target_row = total_idx % 64
                    if target_pat < total_patterns:
                        if patterns[target_pat][target_row][2] is None:
                            patterns[target_pat][target_row][2] = {"inst": 6, "period": evt["period"], "effect": 0xC, "param": 0x20}
    if use_filter:
        if intro_patterns > 0:
            set_event(0, 0, 0, effect_cmd=0xE, effect_param=0x01)
        if main_patterns > 0:
            set_event(intro_patterns, 0, 0, effect_cmd=0xE, effect_param=0x00)
        if outro_patterns > 0:
            set_event(intro_patterns + main_patterns, 0, 0, effect_cmd=0xE, effect_param=0x01)
    set_event(0, 0, 1, effect_cmd=0xF, effect_param=0x06)
    tempo_val = bpm if bpm >= 32 else 125
    set_event(0, 0, 2, effect_cmd=0xF, effect_param=tempo_val & 0xFF)
    samples = {}
    kick_data = generate_kick()
    samples[1] = {"name": "Kick", "data": kick_data, "volume": 64, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": len(kick_data)}
    snare_data = generate_snare()
    samples[2] = {"name": "Snare", "data": snare_data, "volume": 48, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": len(snare_data)}
    hat_data = generate_hat()
    samples[3] = {"name": "Hat", "data": hat_data, "volume": 40, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": len(hat_data)}
    bass_data = generate_triangle_wave()
    samples[4] = {"name": "Bass", "data": bass_data, "volume": 64, "finetune": 0, "loop_start": 0, "loop_length": len(bass_data), "length": len(bass_data)}
    chord_data = generate_sine_wave(harmonics=[(2, 0.5)])
    samples[5] = {"name": "Chord", "data": chord_data, "volume": 50, "finetune": 0, "loop_start": 0, "loop_length": len(chord_data), "length": len(chord_data)}
    lead_data = bytes([0x7F] * 16 + [0x81] * 16)
    samples[6] = {"name": "Lead", "data": lead_data, "volume": 64, "finetune": 0, "loop_start": 0, "loop_length": len(lead_data), "length": len(lead_data)}
    clap_data = generate_clap()
    samples[7] = {"name": "Clap", "data": clap_data, "volume": 50, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": len(clap_data)}
    tusch_data = generate_tusch()
    samples[8] = {"name": "Tusch", "data": tusch_data, "volume": 50, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": len(tusch_data)}
    for inst in range(9, 32):
        samples[inst] = {"name": "", "data": b"", "volume": 0, "finetune": 0, "loop_start": 0, "loop_length": 1, "length": 0}
    song_name = generate_song_name()
    title_bytes = song_name.encode('ascii')[:20].ljust(20, b'\x00')
    mod_bytes = bytearray(title_bytes)
    for inst in range(1, 32):
        s = samples[inst]
        name_bytes = s["name"].encode('ascii')[:22].ljust(22, b'\x00')
        mod_bytes.extend(name_bytes)
        mod_bytes.extend(struct.pack(">H", s["length"] // 2))
        mod_bytes.append(s["finetune"] & 0x0F)
        vol = s["volume"]
        mod_bytes.append(vol if vol <= 64 else 64)
        mod_bytes.extend(struct.pack(">H", s["loop_start"] // 2))
        mod_bytes.extend(struct.pack(">H", s["loop_length"] // 2))
    song_length = total_patterns if total_patterns < 128 else 127
    mod_bytes.append(song_length & 0xFF)
    mod_bytes.append(0x00)
    order_list = list(range(total_patterns)) + [0] * (128 - total_patterns)
    mod_bytes.extend(bytes(order_list[:128]))
    mod_bytes.extend(b"M.K.")
    for pat in range(total_patterns):
        for row in range(64):
            for ch in range(4):
                cell = patterns[pat][row][ch]
                if cell is None:
                    mod_bytes.extend(b'\x00\x00\x00\x00')
                else:
                    inst_num = cell.get("inst", 0)
                    period_idx = cell.get("period", None)
                    effect = cell.get("effect", 0) or 0
                    param = cell.get("param", 0) or 0
                    period_val = period_table[period_idx] if period_idx is not None and inst_num != 0 else 0
                    inst_high = (inst_num >> 4) & 0xF
                    inst_low = inst_num & 0xF
                    period_high = (period_val >> 8) & 0xF
                    period_low = period_val & 0xFF
                    byte1 = (inst_high << 4) | period_high
                    byte2 = period_low
                    byte3 = (inst_low << 4) | (effect & 0xF)
                    byte4 = param & 0xFF
                    mod_bytes.extend(bytes([byte1, byte2, byte3, byte4]))
    sample_data_bytes = bytearray()
    for inst in range(1, 32):
        sample_data_bytes.extend(samples[inst]["data"])
    mod_bytes.extend(sample_data_bytes)
    base_name = song_name.replace(" ", "_")
    file_path = os.path.join("output", base_name + ".mod")
    if os.path.exists(file_path):
        cnt = 1
        while os.path.exists(os.path.join("output", f"{base_name}_{cnt}.mod")):
            cnt += 1
        file_path = os.path.join("output", f"{base_name}_{cnt}.mod")
    with open(file_path, "wb") as f:
        f.write(mod_bytes)
    return file_path

def open_output_folder():
    folder = os.path.abspath("output")
    if os.name == "nt":
        os.startfile(folder)
    elif os.name == "posix":
        subprocess.Popen(["xdg-open", folder])
    elif os.name == "darwin":
        subprocess.Popen(["open", folder])

root = tk.Tk()
root.title("MOD Music Generator")
root.geometry("600x550")
style_var = tk.StringVar(value="Techno")
tk.Label(root, text="Musikstil:").grid(row=0, column=0, sticky="e")
ttk.Combobox(root, textvariable=style_var, values=["Techno", "Breakbeat", "Acid", "Drum & Bass", "Dubstep", "Swing", "Synthpop", "Meditation", "Ambient", "Chill", "Blues"], state="readonly").grid(row=0, column=1, sticky="w")
scale_var = tk.StringVar(value="Dur")
tk.Label(root, text="Skala:").grid(row=1, column=0, sticky="e")
ttk.Combobox(root, textvariable=scale_var, values=["Dur", "Moll", "Dorisch", "Phrygisch", "Lydisch", "Mixolydisch", "Lokrich"], state="readonly").grid(row=1, column=1, sticky="w")
key_var = tk.StringVar(value="C")
tk.Label(root, text="Grundton:").grid(row=2, column=0, sticky="e")
ttk.Combobox(root, textvariable=key_var, values=["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"], state="readonly").grid(row=2, column=1, sticky="w")
octave_var = tk.IntVar(value=2)
tk.Label(root, text="Start-Oktave:").grid(row=3, column=0, sticky="e")
tk.Spinbox(root, from_=1, to=4, textvariable=octave_var, width=5).grid(row=3, column=1, sticky="w")
tk.Label(root, text="Intro Patterns:").grid(row=4, column=0, sticky="e")
intro_spin = tk.Spinbox(root, from_=0, to=8, width=5)
intro_spin.grid(row=4, column=1, sticky="w")
tk.Label(root, text="Main Patterns:").grid(row=5, column=0, sticky="e")
main_spin = tk.Spinbox(root, from_=1, to=20, width=5)
main_spin.grid(row=5, column=1, sticky="w")
tk.Label(root, text="Outro Patterns:").grid(row=6, column=0, sticky="e")
outro_spin = tk.Spinbox(root, from_=0, to=8, width=5)
outro_spin.grid(row=6, column=1, sticky="w")
arpeggio_var = tk.BooleanVar()
vibrato_var = tk.BooleanVar()
tremolo_var = tk.BooleanVar()
echo_var = tk.BooleanVar()
filter_var = tk.BooleanVar()
tk.Checkbutton(root, text="Arpeggio", variable=arpeggio_var).grid(row=7, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Vibrato", variable=vibrato_var).grid(row=8, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Tremolo", variable=tremolo_var).grid(row=9, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Echo", variable=echo_var).grid(row=10, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Filter Modulation", variable=filter_var).grid(row=11, column=0, columnspan=2, sticky="w")
tk.Label(root, text="Tempo (BPM):").grid(row=12, column=0, sticky="e")
tempo_scale = tk.Scale(root, from_=60, to=180, orient="horizontal", length=300)
tempo_scale.set(125)
tempo_scale.grid(row=12, column=1, sticky="w")
status_label = tk.Label(root, text="")
status_label.grid(row=14, column=0, columnspan=2)
def generate_song():
    status_label.config(text="Generiere .MOD Datei...")
    root.update()
    file_path = compose_mod(style_var.get(), scale_var.get(), key_var.get(), octave_var.get(), int(intro_spin.get()), int(main_spin.get()), int(outro_spin.get()), int(tempo_scale.get()), arpeggio_var.get(), vibrato_var.get(), tremolo_var.get(), echo_var.get(), filter_var.get())
    status_label.config(text="Generiert: " + file_path)
def open_folder():
    open_output_folder()
tk.Button(root, text="Generate .MOD", command=generate_song).grid(row=13, column=0, columnspan=2, pady=5)
tk.Button(root, text="Open Output Folder", command=open_folder).grid(row=15, column=0, columnspan=2, pady=5)
root.mainloop()
