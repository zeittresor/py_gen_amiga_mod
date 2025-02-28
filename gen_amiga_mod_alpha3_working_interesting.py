import tkinter as tk
from tkinter import filedialog
import math, random
# source: look here github.com/zeittresor
def note_to_period(note):
    note_names = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
    if len(note) == 3:
        if note[1] == '-' or note[1] == ' ':
            name = note[0]
            octave = int(note[2])
        elif note[1] in ['#','b']:
            name = note[0:2]
            octave = int(note[2])
        else:
            name = note[0]
            octave = int(note[1:3])
    else:
        name = note[0]
        octave = int(note[1])
    semitone_index = (octave - 1) * 12 + note_names[name]
    return math.floor(856 * (2 ** (-semitone_index / 12)))

def generate_sample_fm(carrier_freq, mod_freq, mod_index, length_seconds, sample_rate, decay_power):
    N = int(sample_rate * length_seconds)
    samples = []
    for i in range(N):
        t = i / sample_rate
        value = math.sin(2 * math.pi * carrier_freq * t + mod_index * math.sin(2 * math.pi * mod_freq * t))
        envelope = ((1 - i / (N - 1)) ** decay_power) if N > 1 else 1.0
        sample_val = int(value * envelope * 127)
        if sample_val > 127: sample_val = 127
        if sample_val < -128: sample_val = -128
        samples.append(sample_val & 0xFF)
    return bytes(samples)

def generate_kick():
    sr = 11025
    N = int(sr * 0.5)
    freq_start = random.uniform(50, 80)
    freq_end = freq_start * 0.1
    samples = []
    phase = 0.0
    for i in range(N):
        frac = i / (N - 1) if N > 1 else 1.0
        curr_freq = freq_start * ((freq_end / freq_start) ** frac)
        phase += 2 * math.pi * curr_freq / sr
        value = math.sin(phase)
        amp = (1 - frac) ** 2
        sample_val = int(value * amp * 127)
        if sample_val > 127: sample_val = 127
        if sample_val < -128: sample_val = -128
        samples.append(sample_val & 0xFF)
    samples[-1] = 0
    return bytes(samples)

def generate_snare():
    sr = 11025
    N = int(sr * 0.3)
    tone_freq = random.uniform(150, 250)
    samples = []
    phase = 0.0
    for i in range(N):
        noise = random.uniform(-1, 1)
        phase += 2 * math.pi * tone_freq / sr
        tone = math.sin(phase)
        frac = i / (N - 1) if N > 1 else 1.0
        noise_amp = (1 - frac) ** 1.5
        tone_amp = (1 - frac) ** 3
        value = noise * noise_amp + tone * tone_amp * 0.5
        sample_val = int(value * 127)
        if sample_val > 127: sample_val = 127
        if sample_val < -128: sample_val = -128
        samples.append(sample_val & 0xFF)
    samples[-1] = 0
    return bytes(samples)

def generate_hat(closed=True):
    sr = 11025
    N = int(sr * (0.1 if closed else 0.3))
    samples = []
    for i in range(N):
        noise = random.uniform(-1, 1)
        frac = i / (N - 1) if N > 1 else 1.0
        amp = (1 - frac) ** (4 if closed else 2)
        sample_val = int(noise * amp * 127)
        if sample_val > 127: sample_val = 127
        if sample_val < -128: sample_val = -128
        samples.append(sample_val & 0xFF)
    samples[-1] = 0
    return bytes(samples)

instrument_data = []

def generate_instruments(use_last):
    global instrument_data
    if use_last and instrument_data:
        return instrument_data
    carrier = random.uniform(300, 600)
    ratio = random.choice([1, 2, 3, 4])
    mod_freq = carrier * ratio
    mod_index = random.uniform(3, 8)
    lead_sample = generate_sample_fm(carrier, mod_freq, mod_index, 1.0, 22050, decay_power=1.0)
    bass_carrier = random.uniform(80, 150)
    bass_ratio = random.choice([1, 2, 3, 4])
    bass_mod_freq = bass_carrier * bass_ratio
    bass_mod_index = random.uniform(1, 4)
    bass_sample = generate_sample_fm(bass_carrier, bass_mod_freq, bass_mod_index, 1.0, 22050, decay_power=1.0)
    chord_carrier = random.uniform(200, 400)
    chord_ratio = random.choice([1, 2, 3, 4])
    chord_mod_freq = chord_carrier * chord_ratio
    chord_mod_index = random.uniform(2, 5)
    chord_sample = generate_sample_fm(chord_carrier, chord_mod_freq, chord_mod_index, 1.5, 22050, decay_power=0.5)
    kick_sample = generate_kick()
    snare_sample = generate_snare()
    hat_closed_sample = generate_hat(closed=True)
    hat_open_sample = generate_hat(closed=False)
    instrument_data = [
        {"name": "LeadAccent", "vol": 64, "sample": lead_sample},
        {"name": "LeadNormal", "vol": 48, "sample": lead_sample},
        {"name": "LeadEcho", "vol": 32, "sample": lead_sample},
        {"name": "BassSynth", "vol": 56, "sample": bass_sample},
        {"name": "ChordPad", "vol": 48, "sample": chord_sample},
        {"name": "DrumKick", "vol": 64, "sample": kick_sample},
        {"name": "DrumSnare", "vol": 50, "sample": snare_sample},
        {"name": "HatClosed", "vol": 40, "sample": hat_closed_sample},
        {"name": "HatOpen", "vol": 40, "sample": hat_open_sample}
    ]
    return instrument_data

def generate_song(use_last_instruments=False, polyrhythm=False):
    instruments = generate_instruments(use_last_instruments)
    lead_acc = 1
    lead_norm = 2
    lead_echo = 3
    bass_inst = 4
    chord_inst = 5
    kick_inst = 6
    snare_inst = 7
    hat_closed_inst = 8
    hat_open_inst = 9
    root_note = random.choice(["C", "D", "E", "F", "G", "A", "B"])
    root_oct = random.choice([1, 2])
    key_mode = random.choice(["major", "minor"])
    scale_intervals = [0,2,4,5,7,9,11] if key_mode == "major" else [0,2,3,5,7,8,10]
    root_base_index = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}[root_note] + (root_oct - 1) * 12
    def get_scale_period(degree, octave_offset=0):
        octave_add = degree // len(scale_intervals)
        scale_degree = degree % len(scale_intervals)
        semitone = root_base_index + scale_intervals[scale_degree] + 12 * octave_add + 12 * octave_offset
        return math.floor(856 * (2 ** (-semitone / 12)))
    pattern_count = 8
    patterns = [ [ [ [0,0,0,0] for _ in range(4) ] for _ in range(64) ] for _ in range(pattern_count) ]
    vibrato_speed = random.choice([3, 4, 5])
    vibrato_depth = random.choice([1, 2, 3])
    vibrato_cmd = 0x4
    vibrato_param = (vibrato_speed << 4) | (vibrato_depth & 0xF)
    def generate_melody(pattern_index, allow_out_of_scale=False):
        current_degree = random.randrange(len(scale_intervals))
        last_degree = current_degree
        row = 0
        while row < 64:
            step = 2 if random.random() < 0.2 else 4
            if row >= 64: break
            degree_change = random.choice([-3,-2,-1,1,2,3])
            current_degree = (last_degree + degree_change) % (len(scale_intervals) * 2)
            use_scale = True
            if allow_out_of_scale and random.random() < 0.1:
                use_scale = False
            if use_scale:
                period = get_scale_period(current_degree, octave_offset=0)
            else:
                offset = random.choice([-1, 1])
                base_period = get_scale_period(last_degree, octave_offset=0)
                period = int(base_period * (2 ** (offset / 12.0)))
            instrument = lead_acc if (row % 16 == 0 or random.random() < 0.1) else lead_norm
            patterns[pattern_index][row][0] = [instrument, period, 0, 0]
            if pattern_index in [1, 2] and random.random() < 0.3:
                patterns[pattern_index][row][0][2] = vibrato_cmd
                patterns[pattern_index][row][0][3] = vibrato_param
            last_degree = current_degree
            row += step
    generate_melody(0, allow_out_of_scale=True)
    generate_melody(1, allow_out_of_scale=False)
    generate_melody(2, allow_out_of_scale=False)
    for pat in [1, 2]:
        for measure in range(4):
            base = measure * 16
            root_period = get_scale_period(0, octave_offset=0)
            patterns[pat][base][2] = [bass_inst, root_period, 0, 0]
            second_period = root_period
            if random.random() < 0.5:
                second_period = get_scale_period(0, octave_offset=1)
            else:
                second_period = get_scale_period(4, octave_offset=0)
            patterns[pat][base+8][2] = [bass_inst, second_period, 0, 0]
    for pat in [1, 2]:
        for measure in range(4):
            base = measure * 16
            patterns[pat][base+0][3] = [kick_inst, note_to_period("C-2"), 0, 0]
            patterns[pat][base+8][3] = [kick_inst, note_to_period("C-2"), 0, 0]
            patterns[pat][base+4][3] = [snare_inst, note_to_period("C-3"), 0, 0]
            patterns[pat][base+12][3] = [snare_inst, note_to_period("C-3"), 0, 0]
            if random.random() < 0.3:
                patterns[pat][base+8][3] = [0, 0, 0, 0]
            if random.random() < 0.3:
                patterns[pat][base+7][3] = [kick_inst, note_to_period("C-2"), 0, 0]
            if random.random() < 0.2:
                if patterns[pat][base+10][3][0] == 0:
                    patterns[pat][base+10][3] = [kick_inst, note_to_period("C-2"), 0, 0]
            for beat in range(4):
                off1 = base + beat * 4 + 2
                off2 = base + beat * 4 + 6
                if off1 < base+16 and patterns[pat][off1][3][0] == 0:
                    instr = hat_open_inst if random.random() < 0.1 else hat_closed_inst
                    patterns[pat][off1][3] = [instr, note_to_period("C-4"), 0, 0]
                if off2 < base+16 and patterns[pat][off2][3][0] == 0:
                    instr = hat_open_inst if random.random() < 0.1 else hat_closed_inst
                    patterns[pat][off2][3] = [instr, note_to_period("C-4"), 0, 0]
    generate_melody(3, allow_out_of_scale=False)
    for measure in range(4):
        base = measure * 16
        root_period = get_scale_period(0, octave_offset=0)
        patterns[3][base][2] = [bass_inst, root_period, 0, 0]
        second_period = get_scale_period(0, octave_offset=1) if measure % 2 == 0 else get_scale_period(4, octave_offset=0)
        patterns[3][base+8][2] = [bass_inst, second_period, 0, 0]
    for measure in range(4):
        base = measure * 16
        patterns[3][base+0][3] = [kick_inst, note_to_period("C-2"), 0, 0]
        patterns[3][base+8][3] = [kick_inst, note_to_period("C-2"), 0, 0]
        patterns[3][base+4][3] = [snare_inst, note_to_period("C-3"), 0, 0]
        patterns[3][base+12][3] = [snare_inst, note_to_period("C-3"), 0, 0]
        if random.random() < 0.5:
            patterns[3][base+7][3] = [kick_inst, note_to_period("C-2"), 0, 0]
        for beat in range(4):
            off1 = base + beat * 4 + 2
            off2 = base + beat * 4 + 6
            if off1 < base+16 and patterns[3][off1][3][0] == 0:
                instr = hat_open_inst if random.random() < 0.1 else hat_closed_inst
                patterns[3][off1][3] = [instr, note_to_period("C-4"), 0, 0]
            if off2 < base+16 and patterns[3][off2][3][0] == 0:
                instr = hat_open_inst if random.random() < 0.1 else hat_closed_inst
                patterns[3][off2][3] = [instr, note_to_period("C-4"), 0, 0]
    root_period = get_scale_period(0, octave_offset=0)
    patterns[4][0][2] = [bass_inst, root_period, 0, 0]
    for measure in range(4):
        base = measure * 16
        patterns[4][base+0][3] = [kick_inst, note_to_period("C-2"), 0, 0]
        patterns[4][base+8][3] = [kick_inst, note_to_period("C-2"), 0, 0]
        patterns[4][base+4][3] = [snare_inst, note_to_period("C-3"), 0, 0]
        patterns[4][base+12][3] = [snare_inst, note_to_period("C-3"), 0, 0]
        for r in range(base, base+16, 2):
            if patterns[4][r][3][0] == 0:
                patterns[4][r][3] = [hat_closed_inst, note_to_period("C-4"), 0, 0]
    for r in range(48, 64, 2):
        patterns[4][r][3] = [snare_inst, note_to_period("C-3"), 0, 0]
    generate_melody(5, allow_out_of_scale=True)
    for r in range(64):
        patterns[6][r][0] = patterns[3][r][0].copy()
        patterns[6][r][2] = patterns[3][r][2].copy()
        patterns[6][r][3] = patterns[3][r][3].copy()
    arpeggio_cmd = 0x0
    arpeggio_param = 0x47 if key_mode == "major" else 0x37
    patterns[6][0][1] = [chord_inst, get_scale_period(0, octave_offset=1), arpeggio_cmd, arpeggio_param]
    patterns[6][32][1] = [chord_inst, get_scale_period(4, octave_offset=1), arpeggio_cmd, arpeggio_param]
    for r in range(64):
        patterns[7][r][0] = patterns[6][r][0].copy()
        patterns[7][r][1] = patterns[6][r][1].copy()
        patterns[7][r][2] = patterns[6][r][2].copy()
        patterns[7][r][3] = patterns[6][r][3].copy()
    for r in range(48, 64):
        patterns[7][r][3] = [0, 0, 0, 0]
    for r in range(48, 62, 2):
        patterns[7][r][3] = [snare_inst, note_to_period("C-3"), 0, 0]
    patterns[7][62][3] = [hat_open_inst, note_to_period("C-3"), 0, 0]
    for pat in [0, 5]:
        for row in range(64):
            if patterns[pat][row][0][0] != 0:
                target = row + 2
                if target < 64 and patterns[pat][target][1][0] == 0:
                    instr = lead_echo
                    period = patterns[pat][row][0][1]
                    patterns[pat][target][1] = [instr, period, 0, 0]
    def set_speed(pattern_index, value):
        ch = 3 if patterns[pattern_index][0][3][0] != 0 else 0
        if patterns[pattern_index][0][ch][0] != 0:
            patterns[pattern_index][0][ch][2] = 0xF
            patterns[pattern_index][0][ch][3] = value
        else:
            patterns[pattern_index][0][ch] = [0, 0, 0xF, value]
    if polyrhythm:
        set_speed(0, 0x08)
        set_speed(1, 0x06)
        set_speed(4, 0x04)
        set_speed(6, 0x06)
        set_speed(5, 0x08)
    else:
        set_speed(0, 0x06)
    order = []
    order.append(0)
    if random.random() < 0.5: order.append(0)
    order.append(1)
    order.append(2)
    order.append(3)
    order.append(3)
    order.append(4)
    order.append(6)
    order.append(7)
    order.append(5)
    if random.random() < 0.5: order.append(5)
    song_length = len(order)
    num_patterns = max(order) + 1
    title_bytes = "AlgorithmicTrack".encode('ascii')[:20].ljust(20, b'\x00')
    instrument_headers = b""
    for i in range(31):
        if i < len(instruments):
            name = instruments[i]["name"].encode('ascii')[:22].ljust(22, b'\x00')
            sample_len = len(instruments[i]["sample"])
            if sample_len % 2 == 1:
                instruments[i]["sample"] += b'\x00'
                sample_len += 1
            length_words = sample_len // 2
            finetune = 0
            volume = instruments[i]["vol"] & 0xFF
            repeat_offset = 0
            repeat_length = 1
            header = name
            header += bytes([length_words >> 8, length_words & 0xFF])
            header += bytes([finetune])
            header += bytes([volume])
            header += bytes([repeat_offset >> 8, repeat_offset & 0xFF])
            header += bytes([repeat_length >> 8, repeat_length & 0xFF])
            instrument_headers += header
        else:
            instrument_headers += b'\x00' * 30
    song_length_byte = bytes([song_length & 0xFF])
    restart_byte = b'\x00'
    order_table = bytes(order) + b'\x00' * (128 - len(order))
    signature = b'M.K.'
    pattern_data_bytes = b""
    for p in range(num_patterns):
        for r in range(64):
            for c in range(4):
                instr = patterns[p][r][c][0]
                period = patterns[p][r][c][1]
                effect_cmd = patterns[p][r][c][2]
                effect_param = patterns[p][r][c][3]
                byte0 = ((instr & 0xF0) | ((period >> 8) & 0x0F))
                byte1 = period & 0xFF
                byte2 = (((instr & 0x0F) << 4) | (effect_cmd & 0x0F))
                byte3 = effect_param & 0xFF
                pattern_data_bytes += bytes([byte0, byte1, byte2, byte3])
    sample_data_bytes = b""
    for inst in instruments:
        sample_data_bytes += inst["sample"]
    return title_bytes + instrument_headers + song_length_byte + restart_byte + order_table + signature + pattern_data_bytes + sample_data_bytes

def on_generate():
    data = generate_song(var_use_last.get() == 1, var_poly.get() == 1)
    file_path = filedialog.asksaveasfilename(defaultextension=".mod", filetypes=[("ProTracker Module", "*.mod")])
    if file_path:
        with open(file_path, "wb") as f:
            f.write(data)

root = tk.Tk()
root.title("MOD Generator")
var_poly = tk.IntVar()
var_use_last = tk.IntVar()
cb1 = tk.Checkbutton(root, text="Polyrhythmische Variationen", variable=var_poly)
cb2 = tk.Checkbutton(root, text="Use Last Generating Instruments", variable=var_use_last)
btn = tk.Button(root, text="Generate .MOD Song", command=on_generate)
cb1.pack(anchor="w")
cb2.pack(anchor="w")
btn.pack(fill="x")
root.mainloop()
