import tkinter as tk
import random
import math
import struct
# source: look here github.com/zeittresor
styles = {
    "Techno": {"scale": "minor", "root": "A2", "bpm": 130, "use_filter": True, "use_vibrato": False, "use_slide": False},
    "Breakbeat": {"scale": "minor", "root": "A2", "bpm": 110, "use_filter": False, "use_vibrato": False, "use_slide": False},
    "Acid": {"scale": "minor", "root": "A2", "bpm": 125, "use_filter": True, "use_vibrato": False, "use_slide": True},
    "Drum & Bass": {"scale": "minor", "root": "A2", "bpm": 170, "use_filter": False, "use_vibrato": False, "use_slide": False},
    "Dubstep": {"scale": "minor", "root": "A2", "bpm": 140, "use_filter": True, "use_vibrato": False, "use_slide": False},
    "Swing": {"scale": "major", "root": "C2", "bpm": 120, "use_filter": False, "use_vibrato": False, "use_slide": False},
    "Synthpop": {"scale": "major", "root": "C2", "bpm": 120, "use_filter": False, "use_vibrato": True, "use_slide": False}
}

note_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
base_periods = [1712,1616,1524,1440,1356,1280,1208,1140,1076,1016,960,906]
period_table = []
period_dict = {}
for i, p in enumerate(base_periods):
    note = note_names[i] + "0"
    period_table.append((note, p))
    period_dict[note] = p
current = base_periods
for octv in range(1, 5):
    new = []
    for p in current:
        newp = p // 2
        new.append(newp)
    for i, p in enumerate(new):
        note = note_names[i] + str(octv)
        period_table.append((note, p))
        period_dict[note] = p
    current = new

major_scale = [0,2,4,5,7,9,11]
minor_scale = [0,2,3,5,7,8,10]

def generate_song_name():
    words = ["Cosmic","Nebula","Mystic","Funky","Electric","Phantom","Shadow","Neon","Bass","Groove","Quantum","Retro","Solar","Pulse","Echo","Zenith","Twilight","Crimson","Turbo","Galaxy","Spectrum","Nova","Phoenix","Velocity"]
    name = "_".join(random.sample(words, 3))
    return name[:20]

def generate_fm_sample(length, carrier_freq, mod_freq, mod_index, amplitude_env=None, mod_index_env=None, sample_rate=8000):
    samples = []
    phase_c = 0.0
    phase_m = 0.0
    inc_c = 2 * math.pi * carrier_freq / sample_rate
    inc_m = 2 * math.pi * mod_freq / sample_rate
    for n in range(length):
        mi = mod_index_env[n] if mod_index_env is not None else mod_index
        amp = amplitude_env[n] if amplitude_env is not None else 1.0
        value = math.sin(phase_c + mi * math.sin(phase_m))
        phase_c += inc_c
        phase_m += inc_m
        if phase_c > 2 * math.pi:
            phase_c -= 2 * math.pi
        if phase_m > 2 * math.pi:
            phase_m -= 2 * math.pi
        samples.append(int(max(-127, min(127, value * 127 * amp))))
    return samples

def create_samples():
    kick_len = 1000
    amp_env = [1.0 - (i / kick_len) for i in range(kick_len)]
    mod_index_env = [5.0 * (1 - (i / 200)) if i < 200 else 0.0 for i in range(kick_len)]
    kick = generate_fm_sample(kick_len, 50, 200, 5.0, amplitude_env=amp_env, mod_index_env=mod_index_env)
    snare_len = 1000
    amp_env = [1.0 - (i / snare_len) for i in range(snare_len)]
    mod_index_env = [4.0 if i < 200 else 2.0 if i < 500 else 1.0 for i in range(snare_len)]
    snare = generate_fm_sample(snare_len, 200, 400, 4.0, amplitude_env=amp_env, mod_index_env=mod_index_env)
    hat_len = 500
    amp_env = [1.0 - (i / hat_len) for i in range(hat_len)]
    hat = generate_fm_sample(hat_len, 800, 1200, 4.0, amplitude_env=amp_env)
    bass_len = 64
    bass = generate_fm_sample(bass_len, 125, 250, 2.0)
    pad_len = 64
    pad = generate_fm_sample(pad_len, 125, 250, 5.0)
    lead_len = 64
    lead = generate_fm_sample(lead_len, 125, 375, 3.0)
    def to_bytes(sample_list):
        return bytes([(s & 0xFF) if s >= 0 else (256 + s) for s in sample_list])
    return {
        1: to_bytes(kick),
        2: to_bytes(snare),
        3: to_bytes(hat),
        4: to_bytes(bass),
        5: to_bytes(pad),
        6: to_bytes(lead)
    }

def build_instrument_header(name, sample_data, volume=64, finetune=0, loop_start=0, loop_length=0):
    name_bytes = name.encode('ascii', 'ignore')[:22]
    name_bytes = name_bytes + bytes(22 - len(name_bytes))
    length_words = len(sample_data) // 2
    if length_words > 0xFFFF:
        length_words = 0xFFFF
    finetune_byte = finetune & 0xF
    volume_byte = volume & 0xFF
    loop_start_words = loop_start // 2
    loop_length_words = loop_length // 2
    header = name_bytes
    header += struct.pack('>H', length_words)
    header += bytes([finetune_byte & 0xF])
    header += bytes([volume_byte & 0xFF])
    header += struct.pack('>H', loop_start_words)
    header += struct.pack('>H', loop_length_words)
    return header

def generate_mod(style_name):
    style = styles[style_name]
    scale_type = style["scale"]
    root_note_name = style["root"]
    bpm = style["bpm"]
    use_filter = style["use_filter"]
    use_vibrato = style["use_vibrato"]
    use_slide = style["use_slide"]
    scale_intervals = major_scale if scale_type == "major" else minor_scale
    base_index = None
    for idx, (note, period) in enumerate(period_table):
        if note == root_note_name:
            base_index = idx
            break
    if base_index is None:
        base_index = 0
    if scale_type == "major":
        degrees = [1,2,3,4,5,6]
        chord1 = 1
        chord4 = 5
    else:
        degrees = [1,3,4,5,6,7]
        chord1 = 1
        chord4 = 7
    chord2 = random.choice([d for d in degrees if d not in [chord1, chord4]])
    chord3 = random.choice([d for d in degrees if d not in [chord1, chord2, chord4]])
    progression = [chord1, chord2, chord3, chord4]
    chords_notes = []
    for deg in progression:
        if scale_type == "major":
            if deg in [1,4,5]:
                third_int = 4; fifth_int = 7
            elif deg in [2,3,6]:
                third_int = 3; fifth_int = 7
            else:
                third_int = 3; fifth_int = 6
        else:
            if deg in [3,6,7]:
                third_int = 4; fifth_int = 7
            elif deg in [1,4,5]:
                third_int = 3; fifth_int = 7
            else:
                third_int = 3; fifth_int = 6
        if deg <= 7:
            root_offset = scale_intervals[deg - 1]
        else:
            octaves_up = (deg - 1) // len(scale_intervals)
            index_in_scale = (deg - 1) % len(scale_intervals)
            root_offset = scale_intervals[index_in_scale] + 12 * octaves_up
        root_index = base_index + root_offset
        third_index = root_index + third_int
        fifth_index = root_index + fifth_int
        if fifth_index >= len(period_table):
            fifth_index = len(period_table) - 1
        if third_index >= len(period_table):
            third_index = len(period_table) - 1
        root_period = period_table[root_index][1]
        third_period = period_table[third_index][1]
        fifth_period = period_table[fifth_index][1]
        third_semitone = third_int & 0xF
        fifth_semitone = fifth_int & 0xF
        arpeggio_param = ((third_semitone & 0xF) << 4) | (fifth_semitone & 0xF)
        chords_notes.append({"root_period": root_period, "third_period": third_period, "fifth_period": fifth_period, "arp": arpeggio_param})
    structure = random.choice([(4,16,4), (2,16,8)])
    intro_len, main_len, outro_len = structure
    total_patterns = intro_len + main_len + outro_len
    pattern_data_bytes = b""
    filter_on_pattern = -1
    filter_off_pattern = -1
    if use_filter:
        filter_on_pattern = 0
        filter_off_pattern = intro_len
    for pat in range(total_patterns):
        if pat < intro_len:
            pattern_type = "intro"
        elif pat < intro_len + main_len:
            idx = pat - intro_len
            if idx < main_len / 2:
                pattern_type = "chords"
            else:
                pattern_type = "lead"
        else:
            pattern_type = "outro"
        chan_events = [ [None] * 64 for _ in range(4) ]
        if pat == 0:
            tempo_effect = int(bpm)
            if tempo_effect < 32:
                tempo_effect = 32
            chan_events[1][0] = {"period": 0, "instr": 0, "effect": 0xF, "param": tempo_effect}
        kick_positions = []
        snare_positions = []
        hat_positions = []
        if style_name in ["Techno", "Synthpop"]:
            kick_positions = [0,4,8,12]
            snare_positions = [4,12]
            hat_positions = [2,6,10,14]
        elif style_name == "Breakbeat":
            kick_positions = [0, 8]
            extra_kick = random.choice([2,6,10,14])
            kick_positions.append(extra_kick)
            kick_positions.sort()
            snare_positions = [4,12]
            hat_positions = [0,4,8,12]
        elif style_name == "Drum & Bass":
            kick_positions = [0, 10]
            snare_positions = [4, 12]
            hat_positions = [0,2,4,6,8,10,12,14]
        elif style_name == "Dubstep":
            kick_positions = [0, 12]
            snare_positions = [8]
            hat_positions = [4, 12]
        elif style_name == "Swing":
            kick_positions = [0,8]
            snare_positions = [4,12]
            hat_positions = [0,4,8,12]
        else:
            kick_positions = [0,4,8,12]
            snare_positions = [4,12]
            hat_positions = [2,6,10,14]
        hat_positions = [h for h in hat_positions if h not in snare_positions]
        for measure in range(4):
            base_row = measure * 16
            for k in kick_positions:
                row = base_row + k
                if row < 64:
                    chan_events[0][row] = {"period": period_dict[root_note_name], "instr": 1, "effect": 0, "param": 0}
            for s in snare_positions:
                row = base_row + s
                if row < 64:
                    chan_events[1][row] = {"period": period_dict[root_note_name], "instr": 2, "effect": 0, "param": 0}
            for h in hat_positions:
                row = base_row + h
                if row < 64:
                    chan_events[1][row] = {"period": period_dict[root_note_name], "instr": 3, "effect": 0, "param": 0}
        if pattern_type in ["intro", "outro", "chords", "lead"]:
            for measure in range(4):
                base_row = measure * 16
                chord_idx = measure % 4
                note_period = chords_notes[chord_idx]["root_period"]
                chan_events[2][base_row] = {"period": note_period, "instr": 4, "effect": 0, "param": 0}
                if pattern_type == "lead":
                    mid_row = base_row + 8
                    if mid_row < 64:
                        choice = random.choice(["root", "fifth"])
                        note_period = chords_notes[chord_idx]["root_period"] if choice == "root" else chords_notes[chord_idx]["root_period"] // 2
                        if choice == "fifth":
                            note_period = chords_notes[chord_idx]["fifth_period"] if chords_notes[chord_idx]["fifth_period"] != 0 else chords_notes[chord_idx]["root_period"]
                        chan_events[2][mid_row] = {"period": note_period, "instr": 4, "effect": 0, "param": 0}
        if pattern_type == "chords":
            for measure in range(4):
                base_row = measure * 16
                chord_idx = measure % 4
                arp = chords_notes[chord_idx]["arp"]
                chan_events[3][base_row] = {"period": chords_notes[chord_idx]["root_period"], "instr": 5, "effect": 0x0, "param": arp}
                for r in range(base_row + 1, base_row + 16):
                    if r < 64:
                        chan_events[3][r] = {"period": 0, "instr": 0, "effect": 0x0, "param": arp}
        elif pattern_type == "lead":
            last_note_index = None
            for measure in range(4):
                base_row = measure * 16
                chord_idx = measure % 4
                for beat in [0,4,8,12]:
                    row = base_row + beat
                    if random.random() < 0.2:
                        continue
                    if last_note_index is None:
                        root_idx = base_index
                        chord = chords_notes[chord_idx]
                        root_period = chord["root_period"]
                        third_period = chord["third_period"]
                        fifth_period = chord["fifth_period"]
                        root_idx_pt = next((i for i,(n,p) in enumerate(period_table) if p == root_period), base_index)
                        third_idx_pt = next((i for i,(n,p) in enumerate(period_table) if p == third_period), root_idx_pt)
                        fifth_idx_pt = next((i for i,(n,p) in enumerate(period_table) if p == fifth_period), root_idx_pt)
                        note_index = random.choice([root_idx_pt, third_idx_pt, fifth_idx_pt])
                    else:
                        move = random.choice([-2, -1, 1, 2])
                        note_index = last_note_index + move
                        if note_index < 0:
                            note_index = 0
                        if note_index >= len(period_table):
                            note_index = len(period_table) - 1
                        semitone_from_root = note_index - base_index
                        semitone_mod = semitone_from_root % 12
                        if semitone_mod not in scale_intervals:
                            while semitone_mod not in scale_intervals and semitone_mod >= 0:
                                semitone_mod -= 1
                                note_index -= 1
                    last_note_index = note_index
                    if row < 64:
                        chan_events[3][row] = {"period": period_table[note_index][1], "instr": 6, "effect": 0, "param": 0}
                        if use_vibrato and random.random() < 0.3:
                            vib_rate = 4
                            vib_depth = 2
                            chan_events[3][row]["effect"] = 0x4
                            chan_events[3][row]["param"] = (vib_rate << 4) | vib_depth
        if pat == filter_on_pattern:
            if chan_events[0][0] is not None:
                chan_events[0][0]["effect"] = 0xE
                chan_events[0][0]["param"] = 0x01
            else:
                chan_events[0][0] = {"period": 0, "instr": 0, "effect": 0xE, "param": 0x01}
        if pat == filter_off_pattern:
            if chan_events[0][0] is not None:
                chan_events[0][0]["effect"] = 0xE
                chan_events[0][0]["param"] = 0x00
            else:
                chan_events[0][0] = {"period": 0, "instr": 0, "effect": 0xE, "param": 0x00}
        if use_slide and pattern_type in ["chords", "lead"]:
            bass_events = [ (r, ev) for r, ev in enumerate(chan_events[2]) if ev and ev["instr"] == 4 ]
            for i in range(len(bass_events) - 1):
                r, ev = bass_events[i]
                r_next, ev_next = bass_events[i + 1]
                if ev_next and ev and ev["instr"] == 4 and ev_next["instr"] == 4:
                    if random.random() < 0.5:
                        target_period = ev_next["period"]
                        slide_speed = random.randint(4, 12)
                        chan_events[2][r_next] = {"period": target_period, "instr": 0, "effect": 0x3, "param": slide_speed}
        pattern_bytes = bytearray()
        for row in range(64):
            for ch in range(4):
                event = chan_events[ch][row]
                if event is None:
                    pattern_bytes.extend(b'\x00\x00\x00\x00')
                else:
                    instr = event["instr"] & 0xFF
                    period = event["period"] & 0xFFF
                    effect = event["effect"] & 0xF
                    param = event["param"] & 0xFF
                    byte1 = ((instr >> 4) & 0xF) << 4 | ((period >> 8) & 0xF)
                    byte2 = period & 0xFF
                    byte3 = ((instr & 0xF) << 4) | (effect & 0xF)
                    byte4 = param & 0xFF
                    pattern_bytes.extend(bytes([byte1, byte2, byte3, byte4]))
        pattern_data_bytes += bytes(pattern_bytes)
    song_name = generate_song_name()
    header = song_name.encode('ascii', 'ignore')[:20]
    header = header + bytes(20 - len(header))
    samples = create_samples()
    instrument_names = {1: "Kick", 2: "Snare", 3: "Hihat", 4: "Bass", 5: "ChordPad", 6: "Lead"}
    instrument_headers = b""
    for i in range(1, 32):
        if i in samples:
            name = instrument_names.get(i, "")
            samp = samples[i]
            vol = 64
            loop_start = 0
            loop_length = 0
            if i in [4, 5, 6]:
                loop_start = 0
                loop_length = len(samp)
            instrument_headers += build_instrument_header(name, samp, volume=vol, finetune=0, loop_start=loop_start, loop_length=loop_length)
        else:
            instrument_headers += bytes(22) + struct.pack('>H', 0) + b'\x00' + b'\x00' + struct.pack('>H', 0) + struct.pack('>H', 0)
    song_length = total_patterns
    if song_length > 128:
        song_length = 128
    restart_pos = 0
    song_struct_bytes = bytes([song_length & 0xFF]) + bytes([restart_pos & 0xFF])
    order_table = [i for i in range(total_patterns)]
    order_table_bytes = bytes(order_table) + bytes(128 - len(order_table))
    identifier = b'M.K.'
    module_header = header + instrument_headers + song_struct_bytes + order_table_bytes + identifier
    module_data = module_header + pattern_data_bytes
    for i in range(1, 32):
        if i in samples:
            module_data += samples[i]
    return module_data, song_name

def on_generate():
    style_name = style_var.get()
    mod_bytes, song_name = generate_mod(style_name)
    filename = song_name.replace(" ", "_") + ".mod"
    with open(filename, "wb") as f:
        f.write(mod_bytes)
    status_label.config(text=f"Generated: {filename}")

root = tk.Tk()
root.title("ProTracker .mod Generator")
tk.Label(root, text="Music Style:").pack(pady=5)
style_var = tk.StringVar(value="Techno")
style_menu = tk.OptionMenu(root, style_var, *styles.keys())
style_menu.pack()
generate_btn = tk.Button(root, text="Generate", command=on_generate)
generate_btn.pack(pady=10)
status_label = tk.Label(root, text="")
status_label.pack(pady=5)
root.mainloop()
