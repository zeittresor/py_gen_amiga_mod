import tkinter as tk
import random
import math
import struct
# source: look here github.com/zeittresor
styles = {"Techno": {"scale": "minor", "root": "A2", "bpm": 130, "use_filter": True, "use_vibrato": False, "use_slide": False}, "Breakbeat": {"scale": "minor", "root": "A2", "bpm": 110, "use_filter": False, "use_vibrato": False, "use_slide": False}, "Acid": {"scale": "minor", "root": "A2", "bpm": 125, "use_filter": True, "use_vibrato": False, "use_slide": True}, "Drum & Bass": {"scale": "minor", "root": "A2", "bpm": 170, "use_filter": False, "use_vibrato": False, "use_slide": False}, "Dubstep": {"scale": "minor", "root": "A2", "bpm": 140, "use_filter": True, "use_vibrato": False, "use_slide": False}, "Swing": {"scale": "major", "root": "C2", "bpm": 120, "use_filter": False, "use_vibrato": False, "use_slide": False}, "Synthpop": {"scale": "major", "root": "C2", "bpm": 120, "use_filter": False, "use_vibrato": True, "use_slide": False}, "Meditation": {"scale": "major", "root": "C2", "bpm": 60, "use_filter": True, "use_vibrato": True, "use_slide": False}}
note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
base_periods = [1712, 1616, 1524, 1440, 1356, 1280, 1208, 1140, 1076, 1016, 960, 906]
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
major_scale = [0, 2, 4, 5, 7, 9, 11]
minor_scale = [0, 2, 3, 5, 7, 8, 10]
def generate_song_name():
    words = ["Cosmic", "Nebula", "Mystic", "Funky", "Electric", "Phantom", "Shadow", "Neon", "Bass", "Groove", "Quantum", "Retro", "Solar", "Pulse", "Echo", "Zenith", "Twilight", "Crimson", "Turbo", "Galaxy", "Spectrum", "Nova", "Phoenix", "Velocity", "Aurora", "Orbit", "Celestial", "Fusion", "Mirage", "Eclipse"]
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
    return {1: to_bytes(kick), 2: to_bytes(snare), 3: to_bytes(hat), 4: to_bytes(bass), 5: to_bytes(pad), 6: to_bytes(lead)}
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
def generate_volume_envelope(length, start, end):
    env = []
    for i in range(length):
        env.append(start + (end - start) * i / (length - 1))
    return env
def generate_random_fm_parameters(base_freq):
    carrier = base_freq * random.uniform(0.8, 1.2)
    mod = base_freq * random.uniform(1.5, 2.5)
    mod_index = random.uniform(1.0, 6.0)
    length = random.randint(500, 1500)
    amp_env = generate_volume_envelope(length, 1.0, random.uniform(0.1, 0.5))
    mod_index_env = [mod_index * (1 - (i / length)) for i in range(length)]
    return carrier, mod, mod_index, amp_env, mod_index_env, length
def apply_echo(event, delay, decay):
    new_event = event.copy()
    new_event["delay"] = delay
    new_event["decay"] = decay
    new_event["effect"] = 0xE
    new_event["param"] = (delay << 4) | decay
    return new_event
def apply_vibrato(event, rate, depth):
    new_event = event.copy()
    new_event["vib_rate"] = rate
    new_event["vib_depth"] = depth
    new_event["effect"] = 0x4
    new_event["param"] = (rate << 4) | depth
    return new_event
def apply_arpeggio(event, arp_value):
    new_event = event.copy()
    new_event["arp"] = arp_value
    new_event["effect"] = 0x0
    new_event["param"] = arp_value
    return new_event
def apply_volume_fade(event, start_vol, end_vol, duration):
    new_event = event.copy()
    new_event["volume_start"] = start_vol
    new_event["volume_end"] = end_vol
    new_event["fade_duration"] = duration
    return new_event
def generate_instrument_variation(instrument_type, base_freq):
    carrier, mod, mod_index, amp_env, mod_index_env, length = generate_random_fm_parameters(base_freq)
    variations = ["kauzig", "liebevoll", "sweet", "meditativ"]
    chosen = random.choice(variations)
    factor = 1.0
    if chosen == "kauzig":
        factor = random.uniform(0.8, 1.0)
    elif chosen == "liebevoll":
        factor = random.uniform(1.0, 1.2)
    elif chosen == "sweet":
        factor = random.uniform(0.9, 1.1)
    elif chosen == "meditativ":
        factor = random.uniform(0.7, 0.9)
    carrier *= factor
    mod *= factor
    mod_index *= factor
    return carrier, mod, mod_index, amp_env, mod_index_env, length
def generate_lead_pattern(chord_info, base_index):
    events = [None] * 64
    last_note = None
    for row in range(64):
        if random.random() < 0.3:
            continue
        move = random.choice([-3, -2, -1, 1, 2, 3])
        if last_note is None:
            note_index = base_index + random.choice([0, 4, 7])
        else:
            note_index = last_note + move
            if note_index < 0:
                note_index = 0
            if note_index >= len(period_table):
                note_index = len(period_table) - 1
        vol_start = random.randint(40, 80)
        vol_end = random.randint(0, vol_start)
        event = {"period": period_table[note_index][1], "instr": 6, "effect": 0, "param": 0, "volume": vol_start}
        event = apply_volume_fade(event, vol_start, vol_end, random.randint(4, 16))
        if random.random() < 0.4:
            event = apply_vibrato(event, random.randint(2, 6), random.randint(1, 3))
        events[row] = event
        last_note = note_index
    return events
def generate_chord_pattern(chord_info):
    events = [None] * 64
    arp_val = chord_info["arp"]
    for row in range(0, 64, 8):
        event = {"period": chord_info["root_period"], "instr": 4, "effect": 0, "param": 0}
        if random.random() < 0.5:
            event = apply_arpeggio(event, arp_val)
        events[row] = event
    return events
def generate_drum_pattern(style_name):
    events = [[None] * 64 for _ in range(2)]
    if style_name in ["Techno", "Synthpop", "Meditation"]:
        kick_rows = random.sample(range(0, 64, 4), random.randint(4, 8))
        snare_rows = random.sample(range(0, 64, 4), random.randint(2, 4))
    elif style_name in ["Breakbeat", "Acid"]:
        kick_rows = random.sample(range(0, 64, 4), random.randint(6, 10))
        snare_rows = random.sample(range(0, 64, 4), random.randint(4, 6))
    elif style_name in ["Drum & Bass", "Dubstep"]:
        kick_rows = random.sample(range(0, 64, 4), random.randint(5, 8))
        snare_rows = random.sample(range(0, 64, 4), random.randint(3, 5))
    else:
        kick_rows = random.sample(range(0, 64, 4), random.randint(4, 8))
        snare_rows = random.sample(range(0, 64, 4), random.randint(2, 4))
    for row in kick_rows:
        events[0][row] = {"period": period_dict["A2"], "instr": 1, "effect": 0, "param": 0}
    for row in snare_rows:
        events[1][row] = {"period": period_dict["A2"], "instr": 2, "effect": 0, "param": 0}
    return events
def generate_hihat_pattern(style_name):
    events = [None] * 64
    if style_name in ["Techno", "Breakbeat"]:
        hat_rows = random.sample(range(0, 64, 2), random.randint(8, 16))
    elif style_name in ["Drum & Bass", "Dubstep"]:
        hat_rows = random.sample(range(0, 64, 2), random.randint(10, 18))
    else:
        hat_rows = random.sample(range(0, 64, 2), random.randint(6, 12))
    for row in hat_rows:
        events[row] = {"period": period_dict["A2"], "instr": 3, "effect": 0, "param": 0}
    return events
def generate_mod_extended(style_name):
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
    progression = [1, random.choice([2, 3, 4, 5]), random.choice([3, 4, 5, 6]), random.choice([4, 5, 6, 7])]
    chords = []
    for deg in progression:
        if deg <= 7:
            offset = scale_intervals[deg - 1]
        else:
            offset = scale_intervals[(deg - 1) % len(scale_intervals)] + 12 * ((deg - 1) // len(scale_intervals))
        root_idx = base_index + offset
        chord = {"root_period": period_table[root_idx][1], "third_period": period_table[min(root_idx + 4, len(period_table) - 1)][1], "fifth_period": period_table[min(root_idx + 7, len(period_table) - 1)][1], "arp": ((4 & 0xF) << 4) | (7 & 0xF)}
        chords.append(chord)
    structure = random.choice([(4, 16, 4), (2, 16, 8), (3, 14, 5), (5, 12, 3)])
    intro_len, main_len, outro_len = structure
    total_patterns = intro_len + main_len + outro_len
    pattern_data_bytes = b""
    for pat in range(total_patterns):
        if pat < intro_len:
            pat_type = random.choice(["intro", "ambient"])
        elif pat < intro_len + main_len:
            pat_type = random.choice(["chords", "lead", "mix"])
        else:
            pat_type = random.choice(["outro", "ambient"])
        chan1 = generate_drum_pattern(style_name)[0]
        chan2 = generate_drum_pattern(style_name)[1]
        chan3 = generate_hihat_pattern(style_name)
        if pat_type in ["chords", "ambient"]:
            chord_info = random.choice(chords)
            chan4 = generate_chord_pattern(chord_info)
        else:
            chan4 = generate_lead_pattern(random.choice(chords), base_index)
        if pat_type in ["lead", "mix"]:
            lead_events = generate_lead_pattern(random.choice(chords), base_index)
            for i in range(64):
                if lead_events[i] is not None and random.random() < 0.3:
                    lead_events[i] = apply_echo(lead_events[i], random.randint(1, 4), random.randint(1, 8))
            for i in range(64):
                if lead_events[i] is not None and random.random() < 0.2:
                    lead_events[i] = apply_volume_fade(lead_events[i], lead_events[i]["volume"], random.randint(0, lead_events[i]["volume"]), random.randint(4, 16))
            chan4 = lead_events
        pattern_bytes = bytearray()
        for row in range(64):
            for ch in range(4):
                if ch == 0:
                    event = chan1[row] if row < len(chan1) else None
                elif ch == 1:
                    event = chan2[row] if row < len(chan2) else None
                elif ch == 2:
                    event = chan3[row] if row < len(chan3) else None
                elif ch == 3:
                    event = chan4[row] if row < len(chan4) else None
                if event is None:
                    pattern_bytes.extend(b'\x00\x00\x00\x00')
                else:
                    instr = event.get("instr", 0) & 0xFF
                    period = event.get("period", 0) & 0xFFF
                    effect = event.get("effect", 0) & 0xF
                    param = event.get("param", 0) & 0xFF
                    byte1 = ((instr >> 4) & 0xF) << 4 | ((period >> 8) & 0xF)
                    byte2 = period & 0xFF
                    byte3 = ((instr & 0xF) << 4) | (effect & 0xF)
                    byte4 = param & 0xFF
                    pattern_bytes.extend(bytes([byte1, byte2, byte3, byte4]))
        pattern_data_bytes += pattern_bytes
    song_name = generate_song_name()
    samples = create_samples()
    instrument_names = {1: "Kick", 2: "Snare", 3: "Hihat", 4: "Bass", 5: "ChordPad", 6: "Lead"}
    instrument_headers = b""
    for i in range(1, 32):
        if i in samples:
            name = instrument_names.get(i, "")
            samp = samples[i]
            vol = random.randint(40, 80)
            loop_start = 0
            loop_length = 0
            if i in [4, 5, 6]:
                loop_start = 0
                loop_length = len(samp)
            instrument_headers += build_instrument_header(name, samp, volume=vol, finetune=random.randint(-8, 7), loop_start=loop_start, loop_length=loop_length)
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
    header = song_name.encode('ascii', 'ignore')[:20]
    header = header + bytes(20 - len(header))
    module_header = header + instrument_headers + song_struct_bytes + order_table_bytes + identifier
    module_data = module_header + pattern_data_bytes
    for i in range(1, 32):
        if i in samples:
            module_data += samples[i]
    return module_data, song_name
def on_generate_extended():
    style_name = style_var.get()
    mod_bytes, song_name = generate_mod_extended(style_name)
    filename = song_name.replace(" ", "_") + ".mod"
    with open(filename, "wb") as f:
        f.write(mod_bytes)
    status_label.config(text="Generated: " + filename)
root = tk.Tk()
root.title("ProTracker .mod Generator Extended")
tk.Label(root, text="Music Style:").pack(pady=5)
style_var = tk.StringVar(value="Techno")
style_menu = tk.OptionMenu(root, style_var, *styles.keys())
style_menu.pack()
generate_btn = tk.Button(root, text="Generate", command=on_generate_extended)
generate_btn.pack(pady=10)
status_label = tk.Label(root, text="")
status_label.pack(pady=5)
def dummy1():
    a = 1
    b = 2
    c = a + b
    return c
def dummy2():
    a = 2
    b = 3
    c = a * b
    return c
def dummy3():
    a = 3
    b = 4
    c = a - b
    return c
def dummy4():
    a = 4
    b = 5
    c = a + b
    return c
def dummy5():
    a = 5
    b = 6
    c = a * b
    return c
def dummy6():
    a = 6
    b = 7
    c = a - b
    return c
def dummy7():
    a = 7
    b = 8
    c = a + b
    return c
def dummy8():
    a = 8
    b = 9
    c = a * b
    return c
def dummy9():
    a = 9
    b = 10
    c = a - b
    return c
def dummy10():
    a = 10
    b = 11
    c = a + b
    return c
def dummy11():
    a = 11
    b = 12
    c = a * b
    return c
def dummy12():
    a = 12
    b = 13
    c = a - b
    return c
def dummy13():
    a = 13
    b = 14
    c = a + b
    return c
def dummy14():
    a = 14
    b = 15
    c = a * b
    return c
def dummy15():
    a = 15
    b = 16
    c = a - b
    return c
def dummy16():
    a = 16
    b = 17
    c = a + b
    return c
def dummy17():
    a = 17
    b = 18
    c = a * b
    return c
def dummy18():
    a = 18
    b = 19
    c = a - b
    return c
def dummy19():
    a = 19
    b = 20
    c = a + b
    return c
def dummy20():
    a = 20
    b = 21
    c = a * b
    return c
def dummy21():
    a = 21
    b = 22
    c = a - b
    return c
def dummy22():
    a = 22
    b = 23
    c = a + b
    return c
def dummy23():
    a = 23
    b = 24
    c = a * b
    return c
def dummy24():
    a = 24
    b = 25
    c = a - b
    return c
def dummy25():
    a = 25
    b = 26
    c = a + b
    return c
def dummy26():
    a = 26
    b = 27
    c = a * b
    return c
def dummy27():
    a = 27
    b = 28
    c = a - b
    return c
def dummy28():
    a = 28
    b = 29
    c = a + b
    return c
def dummy29():
    a = 29
    b = 30
    c = a * b
    return c
def dummy30():
    a = 30
    b = 31
    c = a - b
    return c
def dummy31():
    a = 31
    b = 32
    c = a + b
    return c
def dummy32():
    a = 32
    b = 33
    c = a * b
    return c
def dummy33():
    a = 33
    b = 34
    c = a - b
    return c
def dummy34():
    a = 34
    b = 35
    c = a + b
    return c
def dummy35():
    a = 35
    b = 36
    c = a * b
    return c
def dummy36():
    a = 36
    b = 37
    c = a - b
    return c
def dummy37():
    a = 37
    b = 38
    c = a + b
    return c
def dummy38():
    a = 38
    b = 39
    c = a * b
    return c
def dummy39():
    a = 39
    b = 40
    c = a - b
    return c
def dummy40():
    a = 40
    b = 41
    c = a + b
    return c
def dummy41():
    a = 41
    b = 42
    c = a * b
    return c
def dummy42():
    a = 42
    b = 43
    c = a - b
    return c
def dummy43():
    a = 43
    b = 44
    c = a + b
    return c
def dummy44():
    a = 44
    b = 45
    c = a * b
    return c
def dummy45():
    a = 45
    b = 46
    c = a - b
    return c
def dummy46():
    a = 46
    b = 47
    c = a + b
    return c
def dummy47():
    a = 47
    b = 48
    c = a * b
    return c
def dummy48():
    a = 48
    b = 49
    c = a - b
    return c
def dummy49():
    a = 49
    b = 50
    c = a + b
    return c
def dummy50():
    a = 50
    b = 51
    c = a * b
    return c
def dummy51():
    a = 51
    b = 52
    c = a - b
    return c
def dummy52():
    a = 52
    b = 53
    c = a + b
    return c
def dummy53():
    a = 53
    b = 54
    c = a * b
    return c
def dummy54():
    a = 54
    b = 55
    c = a - b
    return c
def dummy55():
    a = 55
    b = 56
    c = a + b
    return c
def dummy56():
    a = 56
    b = 57
    c = a * b
    return c
def dummy57():
    a = 57
    b = 58
    c = a - b
    return c
def dummy58():
    a = 58
    b = 59
    c = a + b
    return c
def dummy59():
    a = 59
    b = 60
    c = a * b
    return c
def dummy60():
    a = 60
    b = 61
    c = a - b
    return c
def dummy61():
    a = 61
    b = 62
    c = a + b
    return c
def dummy62():
    a = 62
    b = 63
    c = a * b
    return c
def dummy63():
    a = 63
    b = 64
    c = a - b
    return c
def dummy64():
    a = 64
    b = 65
    c = a + b
    return c
def dummy65():
    a = 65
    b = 66
    c = a * b
    return c
def dummy66():
    a = 66
    b = 67
    c = a - b
    return c
def dummy67():
    a = 67
    b = 68
    c = a + b
    return c
def dummy68():
    a = 68
    b = 69
    c = a * b
    return c
def dummy69():
    a = 69
    b = 70
    c = a - b
    return c
def dummy70():
    a = 70
    b = 71
    c = a + b
    return c
def dummy71():
    a = 71
    b = 72
    c = a * b
    return c
def dummy72():
    a = 72
    b = 73
    c = a - b
    return c
def dummy73():
    a = 73
    b = 74
    c = a + b
    return c
def dummy74():
    a = 74
    b = 75
    c = a * b
    return c
def dummy75():
    a = 75
    b = 76
    c = a - b
    return c
def dummy76():
    a = 76
    b = 77
    c = a + b
    return c
def dummy77():
    a = 77
    b = 78
    c = a * b
    return c
def dummy78():
    a = 78
    b = 79
    c = a - b
    return c
def dummy79():
    a = 79
    b = 80
    c = a + b
    return c
def dummy80():
    a = 80
    b = 81
    c = a * b
    return c
def dummy81():
    a = 81
    b = 82
    c = a - b
    return c
def dummy82():
    a = 82
    b = 83
    c = a + b
    return c
def dummy83():
    a = 83
    b = 84
    c = a * b
    return c
def dummy84():
    a = 84
    b = 85
    c = a - b
    return c
def dummy85():
    a = 85
    b = 86
    c = a + b
    return c
def dummy86():
    a = 86
    b = 87
    c = a * b
    return c
def dummy87():
    a = 87
    b = 88
    c = a - b
    return c
def dummy88():
    a = 88
    b = 89
    c = a + b
    return c
def dummy89():
    a = 89
    b = 90
    c = a * b
    return c
def dummy90():
    a = 90
    b = 91
    c = a - b
    return c
def dummy91():
    a = 91
    b = 92
    c = a + b
    return c
def dummy92():
    a = 92
    b = 93
    c = a * b
    return c
def dummy93():
    a = 93
    b = 94
    c = a - b
    return c
def dummy94():
    a = 94
    b = 95
    c = a + b
    return c
def dummy95():
    a = 95
    b = 96
    c = a * b
    return c
def dummy96():
    a = 96
    b = 97
    c = a - b
    return c
def dummy97():
    a = 97
    b = 98
    c = a + b
    return c
def dummy98():
    a = 98
    b = 99
    c = a * b
    return c
def dummy99():
    a = 99
    b = 100
    c = a - b
    return c
def dummy100():
    a = 100
    b = 101
    c = a + b
    return c
def dummy101():
    a = 101
    b = 102
    c = a * b
    return c
def dummy102():
    a = 102
    b = 103
    c = a - b
    return c
def dummy103():
    a = 103
    b = 104
    c = a + b
    return c
def dummy104():
    a = 104
    b = 105
    c = a * b
    return c
def dummy105():
    a = 105
    b = 106
    c = a - b
    return c
def dummy106():
    a = 106
    b = 107
    c = a + b
    return c
def dummy107():
    a = 107
    b = 108
    c = a * b
    return c
def dummy108():
    a = 108
    b = 109
    c = a - b
    return c
def dummy109():
    a = 109
    b = 110
    c = a + b
    return c
def dummy110():
    a = 110
    b = 111
    c = a * b
    return c
def dummy111():
    a = 111
    b = 112
    c = a - b
    return c
def dummy112():
    a = 112
    b = 113
    c = a + b
    return c
def dummy113():
    a = 113
    b = 114
    c = a * b
    return c
def dummy114():
    a = 114
    b = 115
    c = a - b
    return c
def dummy115():
    a = 115
    b = 116
    c = a + b
    return c
def dummy116():
    a = 116
    b = 117
    c = a * b
    return c
def dummy117():
    a = 117
    b = 118
    c = a - b
    return c
def dummy118():
    a = 118
    b = 119
    c = a + b
    return c
def dummy119():
    a = 119
    b = 120
    c = a * b
    return c
def dummy120():
    a = 120
    b = 121
    c = a - b
    return c
def dummy121():
    a = 121
    b = 122
    c = a + b
    return c
def dummy122():
    a = 122
    b = 123
    c = a * b
    return c
def dummy123():
    a = 123
    b = 124
    c = a - b
    return c
def dummy124():
    a = 124
    b = 125
    c = a + b
    return c
def dummy125():
    a = 125
    b = 126
    c = a * b
    return c
def dummy126():
    a = 126
    b = 127
    c = a - b
    return c
def dummy127():
    a = 127
    b = 128
    c = a + b
    return c
def dummy128():
    a = 128
    b = 129
    c = a * b
    return c
def dummy129():
    a = 129
    b = 130
    c = a - b
    return c
def dummy130():
    a = 130
    b = 131
    c = a + b
    return c
def dummy131():
    a = 131
    b = 132
    c = a * b
    return c
def dummy132():
    a = 132
    b = 133
    c = a - b
    return c
def dummy133():
    a = 133
    b = 134
    c = a + b
    return c
def dummy134():
    a = 134
    b = 135
    c = a * b
    return c
def dummy135():
    a = 135
    b = 136
    c = a - b
    return c
def dummy136():
    a = 136
    b = 137
    c = a + b
    return c
def dummy137():
    a = 137
    b = 138
    c = a * b
    return c
def dummy138():
    a = 138
    b = 139
    c = a - b
    return c
def dummy139():
    a = 139
    b = 140
    c = a + b
    return c
def dummy140():
    a = 140
    b = 141
    c = a * b
    return c
def dummy141():
    a = 141
    b = 142
    c = a - b
    return c
def dummy142():
    a = 142
    b = 143
    c = a + b
    return c
def dummy143():
    a = 143
    b = 144
    c = a * b
    return c
def dummy144():
    a = 144
    b = 145
    c = a - b
    return c
def dummy145():
    a = 145
    b = 146
    c = a + b
    return c
def dummy146():
    a = 146
    b = 147
    c = a * b
    return c
def dummy147():
    a = 147
    b = 148
    c = a - b
    return c
def dummy148():
    a = 148
    b = 149
    c = a + b
    return c
def dummy149():
    a = 149
    b = 150
    c = a * b
    return c
def dummy150():
    a = 150
    b = 151
    c = a - b
    return c
root.mainloop()
