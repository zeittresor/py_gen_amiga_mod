import tkinter as tk
from tkinter import ttk
import os, math, random
# source: look here github.com/zeittresor
def generate_mod_file(style, tempo=125, volume_dynamic=50, melody_randomness=50,
                      use_echo=False, use_vibrato=False, use_arpeggio=False, use_filter=False,
                      output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    # Prepare audio samples
    def generate_samples():
        # Kick: decaying sine wave
        kick_len = 800
        kick = bytearray(kick_len)
        f_start, f_end = 100.0, 50.0
        phase = 0.0
        rate = 8000.0
        for i in range(kick_len):
            t = i / (kick_len - 1)
            freq = f_start + (f_end - f_start) * t
            amp = (1.0 - t) ** 2
            phase += 2 * math.pi * freq / rate
            val = math.sin(phase)
            sample_val = int(val * 127 * amp)
            if sample_val > 127: sample_val = 127
            if sample_val < -128: sample_val = -128
            kick[i] = sample_val & 0xFF
        # Snare: noise burst
        snare_len = 600
        snare = bytearray(snare_len)
        for i in range(snare_len):
            t = i / (snare_len - 1)
            amp = (1 - t) ** 1.5
            noise_val = random.randint(-128, 127)
            sample_val = int(noise_val * amp)
            if sample_val > 127: sample_val = 127
            if sample_val < -128: sample_val = -128
            snare[i] = sample_val & 0xFF
        # Hi-hat: short high-frequency noise
        hat_len = 150
        hat = bytearray(hat_len)
        for i in range(hat_len):
            t = i / (hat_len - 1)
            amp = (1 - t)
            noise_val = random.randint(-128, 127)
            sample_val = int(noise_val * amp)
            if sample_val > 127: sample_val = 127
            if sample_val < -128: sample_val = -128
            hat[i] = sample_val & 0xFF
        # Bass synth: looped sine wave
        bass_wave_len = 64
        bass = bytearray(bass_wave_len)
        for i in range(bass_wave_len):
            val = math.sin(2 * math.pi * i / bass_wave_len)
            sample_val = int(val * 127)
            if sample_val > 127: sample_val = 127
            if sample_val < -128: sample_val = -128
            bass[i] = sample_val & 0xFF
        # Lead synth: looped saw wave
        lead_wave_len = 64
        lead = bytearray(lead_wave_len)
        for i in range(lead_wave_len):
            sample_val = int(-128 + (256 / lead_wave_len) * i)
            if sample_val > 127: sample_val = 127
            if sample_val < -128: sample_val = -128
            lead[i] = sample_val & 0xFF
        # Prepare sample entries
        samples = []
        samples.append({"name": "Kick", "data": bytes(kick), "volume": 64, "finetune": 0, "loop_start": 0, "loop_len": 1})
        samples.append({"name": "Snare", "data": bytes(snare), "volume": 50, "finetune": 0, "loop_start": 0, "loop_len": 1})
        samples.append({"name": "Hat", "data": bytes(hat), "volume": 40, "finetune": 0, "loop_start": 0, "loop_len": 1})
        samples.append({"name": "BassSynth", "data": bytes(bass), "volume": 50, "finetune": 0, "loop_start": 0, "loop_len": len(bass)//2})
        samples.append({"name": "LeadSynth", "data": bytes(lead), "volume": 48, "finetune": 0, "loop_start": 0, "loop_len": len(lead)//2})
        return samples
    samples = generate_samples()
    # Period table for notes C1-B3 (finetune 0)
    period_table = [856,808,762,720,678,640,604,570,538,508,480,453,
                    428,404,381,360,339,320,302,285,269,254,240,226,
                    214,202,190,180,170,160,151,143,135,127,120,113]
    # Define scale (set of semitone intervals from root)
    if style == "Blues":
        scale_intervals = [0, 3, 5, 6, 7, 10]  # minor blues scale
    elif style == "Swing":
        scale_intervals = [0, 2, 4, 7, 9]      # major pentatonic
    elif style == "Meditation":
        scale_intervals = [0, 2, 4, 7, 9]      # major pentatonic
    elif style == "Ambient":
        scale_intervals = [0, 3, 5, 7, 10]     # minor pentatonic
    elif style == "Chill":
        scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # natural minor
    elif style == "Synthpop":
        scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # major scale
    else:
        scale_intervals = [0, 2, 3, 5, 7, 8, 10]  # natural minor
    # Choose root note index within C1-B3 range
    max_int = max(scale_intervals) if scale_intervals else 0
    root_max = 35 - max_int
    if root_max < 0: root_max = 0
    root_index = random.randint(0, root_max)
    if style in ["Blues","Swing"]:
        if root_max >= 12:
            root_index = random.randint(12, min(root_max, 24))
    # Build scale note indices (two octaves around root)
    scale_notes = []
    for interval in scale_intervals:
        note_idx = root_index + interval
        if 0 <= note_idx <= 35:
            scale_notes.append(note_idx)
    for interval in scale_intervals:
        note_idx = root_index + interval + 12
        if 0 <= note_idx <= 35:
            scale_notes.append(note_idx)
    for interval in scale_intervals:
        note_idx = root_index + interval - 12
        if 0 <= note_idx <= 35:
            scale_notes.append(note_idx)
    scale_notes = sorted(set(scale_notes))
    if not scale_notes:
        scale_notes = [root_index]
    # Determine if break section is used
    use_break_section = style in ["Techno","Breakbeat","Acid","Drum & Bass","Dubstep","Synthpop"]
    # Determine structure pattern counts
    intro_count = 1
    outro_count = 1
    pattern_types = []
    pattern_order = []
    # Intro patterns
    for i in range(intro_count):
        pattern_order.append(len(pattern_types))
        pattern_types.append("intro")
    if style == "Blues":
        # Blues: 12-bar structure (3 main patterns)
        use_break_section = False
        pattern_order.append(len(pattern_types)); pattern_types.append("main")  # I chord pattern
        pattern_order.append(len(pattern_types)); pattern_types.append("main")  # IV->I chord pattern
        pattern_order.append(len(pattern_types)); pattern_types.append("main")  # V->IV->I chord pattern
        pattern_order.append(len(pattern_types)); pattern_types.append("outro")
    else:
        if use_break_section:
            pattern_order.append(len(pattern_types)); pattern_types.append("mainA")
            pattern_order.append(len(pattern_types)); pattern_types.append("mainB")
            pattern_order.append(len(pattern_types)); pattern_types.append("break")
            pattern_order.append(pattern_types.index("mainA"))
            pattern_order.append(len(pattern_types)); pattern_types.append("mainC")
        else:
            pattern_order.append(len(pattern_types)); pattern_types.append("mainA")
            pattern_order.append(len(pattern_types)); pattern_types.append("mainB")
            pattern_order.append(pattern_types.index("mainA"))
            pattern_order.append(len(pattern_types)); pattern_types.append("mainC")
        pattern_order.append(len(pattern_types)); pattern_types.append("outro")
    total_patterns = len(pattern_types)
    # Initialize pattern events matrix
    patterns_events = [ [ [None]*4 for _ in range(64) ] for _ in range(total_patterns) ]
    vib_speed = 4
    vib_depth = 6
    if use_arpeggio:
        # Determine chord type for arpeggio effect
        if (4 in scale_intervals or 11 in scale_intervals) and not (3 in scale_intervals or 10 in scale_intervals):
            arp_x, arp_y = 4, 7  # major chord
        else:
            arp_x, arp_y = 3, 7  # minor chord
    filter_state = False
    # Generate each pattern's events
    for pat_idx, p_type in enumerate(pattern_types):
        is_intro = (p_type == "intro")
        is_outro = (p_type == "outro")
        is_break = (p_type == "break")
        variation_type = p_type
        # Drum channels 0 & 1
        if style not in ["Meditation","Ambient"]:
            chan0 = [None]*64
            chan1 = [None]*64
            kick_positions = []
            snare_positions = []
            hat_positions = []
            if style in ["Techno","Acid"]:
                kick_positions = [0,16,32,48]
                snare_positions = [16,48]
                hat_positions = [8,24,40,56]
                if variation_type in ["mainB","mainC"]:
                    if 48 in kick_positions: kick_positions.remove(48)
                    hat_positions.append(46)
            elif style == "Breakbeat":
                kick_positions = [0,24]
                snare_positions = [16,48]
                if use_filter or volume_dynamic > 70:
                    snare_positions.append(15)
                hat_positions = [8,24,32,40,56]
                if variation_type in ["mainB","mainC"]:
                    kick_positions.append(34)
            elif style == "Drum & Bass":
                kick_positions = [0,20]
                snare_positions = [16,40]
                hat_positions = [8,24,32,48,56]
                if variation_type in ["mainB","mainC"]:
                    snare_positions += [48,49]
            elif style == "Dubstep":
                kick_positions = [0,12]
                snare_positions = [32,34]
                hat_positions = [16,48]
                if variation_type in ["mainB","mainC"]:
                    kick_positions = [0]
                    hat_positions += [8,24,40,56]
            elif style == "Swing":
                kick_positions = [0,32]
                snare_positions = [16,48]
                hat_positions = [8,24,40,56]
                if variation_type in ["mainB","mainC"]:
                    if 32 in kick_positions: kick_positions.remove(32)
            elif style == "Synthpop":
                kick_positions = [0,32]
                snare_positions = [16,48]
                hat_positions = [8,24,40,56]
                if variation_type in ["mainB","mainC"]:
                    kick_positions.append(16)
            elif style == "Chill":
                kick_positions = [0]
                snare_positions = [32]
                hat_positions = [16,48]
                if variation_type in ["mainB","mainC"]:
                    snare_positions = []
            if is_intro:
                kick_positions = [pos for pos in kick_positions if pos >= 16]
                snare_positions = [pos for pos in snare_positions if pos >= 16]
                hat_positions = [pos for pos in hat_positions if pos >= 16]
            if is_outro:
                kick_positions = [pos for pos in kick_positions if pos < 48]
                hat_positions = [pos for pos in hat_positions if pos < 56]
            for pos in kick_positions:
                chan0[pos] = ("note", 1)
            for pos in snare_positions:
                chan1[pos] = ("note", 2)
            for pos in hat_positions:
                if chan0[pos] is None:
                    chan0[pos] = ("note", 3)
                elif chan1[pos] is None:
                    chan1[pos] = ("note", 3)
            for r in range(64):
                if chan0[r]:
                    inst_num = chan0[r][1]; period_val = period_table[12]
                    patterns_events[pat_idx][r][0] = {"inst": inst_num, "period": period_val}
                if chan1[r]:
                    inst_num = chan1[r][1]; period_val = period_table[12]
                    patterns_events[pat_idx][r][1] = {"inst": inst_num, "period": period_val}
        # Bass channel 2
        chan2 = [None]*64
        if style in ["Ambient","Meditation"]:
            if not is_intro:
                chan2[0] = ("note", 4)
        else:
            if style == "Blues":
                base_root_idx = root_index
                IV_root_idx = base_root_idx + 5
                V_root_idx = base_root_idx + 7
                if IV_root_idx > 35: IV_root_idx = 35
                if V_root_idx > 35: V_root_idx = 35
                if pat_idx == pattern_types.index("main"):
                    # First main pattern (I chord)
                    for pos in [0,16,32,48]:
                        chan2[pos] = ("note", 4, base_root_idx)
                elif pat_idx == pattern_types.index("main")+1:
                    # Second main pattern (IV chord for 2 bars, then I)
                    for pos in [0,16]:
                        chan2[pos] = ("note", 4, IV_root_idx)
                    for pos in [32,48]:
                        chan2[pos] = ("note", 4, base_root_idx)
                elif pat_idx == pattern_types.index("main")+2:
                    # Third main pattern (V, IV, then I in last 2 bars)
                    chan2[0] = ("note", 4, V_root_idx)
                    chan2[16] = ("note", 4, IV_root_idx)
                    chan2[32] = ("note", 4, base_root_idx)
                    chan2[48] = ("note", 4, base_root_idx)
            else:
                if style in ["Techno","Acid"]:
                    bass_hits = [0,16,32,48]
                elif style == "Breakbeat":
                    bass_hits = [0,32]
                elif style == "Drum & Bass":
                    bass_hits = [0,16,32,48]
                elif style == "Dubstep":
                    bass_hits = [0,32]
                elif style == "Swing":
                    bass_hits = [0,16,32,48]
                elif style == "Synthpop":
                    bass_hits = [0,32]
                elif style == "Chill":
                    bass_hits = [0,48]
                else:
                    bass_hits = [0,32]
                for pos in bass_hits:
                    chan2[pos] = ("note", 4)
        for r in range(64):
            if chan2[r]:
                inst_num = 4
                note_idx = root_index
                if len(chan2[r]) == 3:
                    note_idx = chan2[r][2]
                else:
                    if style not in ["Blues"]:
                        if style in ["Techno","Acid","Drum & Bass"] and random.random() < 0.3:
                            note_idx = root_index + 7 if root_index+7 <= 35 else root_index
                        else:
                            note_idx = root_index
                if note_idx < 0: note_idx = 0
                if note_idx > 35: note_idx = 35
                period_val = period_table[note_idx]
                patterns_events[pat_idx][r][2] = {"inst": inst_num, "period": period_val}
        # Melody/Lead channel 3
        chan3 = [None]*64
        if style in ["Meditation","Ambient"]:
            if not is_intro and random.random() < 0.5:
                chan3[0] = ("note", 5)
        else:
            if style == "Acid":
                step = 1
            elif style in ["Techno","Drum & Bass","Synthpop","Blues"]:
                step = 2
            elif style in ["Breakbeat","Swing"]:
                step = 2
            elif style in ["Dubstep","Chill"]:
                step = 4
            else:
                step = 4
            possible_positions = list(range(0,64, step))
            melody_positions = []
            if melody_randomness < 30:
                base_positions = [p for p in possible_positions if p < 16]
                count = 2 if style in ["Chill","Dubstep"] else 4
                motif = sorted(random.sample(base_positions, min(count, len(base_positions))))
                melody_positions = []
                for ofs in [0,16,32,48]:
                    melody_positions += [p+ofs for p in motif if p+ofs < 64]
            else:
                if style in ["Acid","Blues"]:
                    count = random.randint(8, 12)
                elif style in ["Techno","Drum & Bass","Swing"]:
                    count = random.randint(6, 10)
                elif style in ["Breakbeat","Synthpop"]:
                    count = random.randint(4, 8)
                elif style in ["Dubstep","Chill"]:
                    count = random.randint(3, 6)
                else:
                    count = random.randint(4, 8)
                if count > len(possible_positions):
                    count = len(possible_positions)
                melody_positions = sorted(random.sample(possible_positions, count))
            last_note_idx = root_index
            for pos in melody_positions:
                if chan3[pos] is None:
                    if melody_randomness < 30:
                        if random.random() < 0.7:
                            if random.random() < 0.4:
                                next_note_idx = last_note_idx
                            else:
                                if last_note_idx in scale_notes:
                                    idx = scale_notes.index(last_note_idx)
                                else:
                                    idx = 0
                                    while idx < len(scale_notes)-1 and scale_notes[idx] < last_note_idx:
                                        idx += 1
                                idx_change = 1 if random.random() < 0.5 else -1
                                new_idx = idx + idx_change
                                if new_idx < 0: new_idx = 0
                                if new_idx >= len(scale_notes): new_idx = len(scale_notes)-1
                                next_note_idx = scale_notes[new_idx]
                        else:
                            next_note_idx = random.choice(scale_notes)
                    else:
                        if random.random() < 0.2 and scale_notes:
                            idx = scale_notes.index(last_note_idx) if last_note_idx in scale_notes else 0
                            new_idx = idx + random.choice([-1,1])
                            if new_idx < 0: new_idx = 0
                            if new_idx >= len(scale_notes): new_idx = len(scale_notes)-1
                            next_note_idx = scale_notes[new_idx]
                        else:
                            next_note_idx = random.choice(scale_notes) if scale_notes else root_index
                    last_note_idx = next_note_idx
                    chan3[pos] = ("note", 5, next_note_idx)
        for r in range(64):
            if chan3[r]:
                inst_num = 5
                note_idx = root_index
                if len(chan3[r]) == 3:
                    note_idx = chan3[r][2]
                if note_idx < 0: note_idx = 0
                if note_idx > 35: note_idx = 35
                period_val = period_table[note_idx]
                patterns_events[pat_idx][r][3] = {"inst": inst_num, "period": period_val}
        # Apply echo (repeat notes with lower volume after delay)
        if use_echo:
            delay = 3
            for r in melody_positions:
                if patterns_events[pat_idx][r][3] and patterns_events[pat_idx][r][3].get("inst") == 5:
                    echo_r = r + delay
                    if echo_r < 64 and patterns_events[pat_idx][echo_r][3] is None:
                        echo_event = patterns_events[pat_idx][r][3].copy()
                        echo_event["effect"] = ("vol", 32)
                        patterns_events[pat_idx][echo_r][3] = echo_event
        # Apply vibrato (continuous pitch modulation)
        if use_vibrato:
            last_note_start = None
            for r in range(64):
                if patterns_events[pat_idx][r][3] and patterns_events[pat_idx][r][3].get("inst") == 5:
                    last_note_start = r
                if last_note_start is not None and r > last_note_start:
                    if patterns_events[pat_idx][r][3] and patterns_events[pat_idx][r][3].get("inst") == 5:
                        last_note_start = r
                    else:
                        if patterns_events[pat_idx][r][3] is None:
                            patterns_events[pat_idx][r][3] = {"effect": ("vib", (vib_speed, vib_depth))}
        # Apply arpeggio (chord) effect
        if use_arpeggio:
            for r in range(64):
                if patterns_events[pat_idx][r][3] and patterns_events[pat_idx][r][3].get("inst") == 5:
                    if random.random() < 0.2:
                        if "effect" not in patterns_events[pat_idx][r][3]:
                            patterns_events[pat_idx][r][3]["effect"] = ("arp", (arp_x, arp_y))
        # Apply random filter toggle (hardware low-pass on/off)
        if use_filter:
            toggles = random.randint(1, 3)
            done = 0
            attempts = 0
            while done < toggles and attempts < 10:
                row = random.randint(1, 62)
                if (patterns_events[pat_idx][row][2] is None or "effect" not in patterns_events[pat_idx][row][2]):
                    ch_free = None
                    for ch in range(4):
                        if patterns_events[pat_idx][row][ch] is None:
                            ch_free = ch
                            break
                    if ch_free is not None:
                        x = 0 if not filter_state else 1
                        patterns_events[pat_idx][row][ch_free] = {"effect": ("filter", x)}
                        filter_state = not filter_state
                        done += 1
                attempts += 1
    # Apply volume dynamics (accents)
    accent_positions = [0, 16, 32, 48]
    if volume_dynamic >= 5:
        for pat_idx in range(len(pattern_types)):
            for r in range(64):
                for ch in [2,3]:
                    event = patterns_events[pat_idx][r][ch]
                    if event and "inst" in event and event["inst"] in [4,5]:
                        is_accent = (r in accent_positions)
                        target_vol = 64 if is_accent else int(64 * (1 - 0.5 * (volume_dynamic/100.0)))
                        if target_vol < 1: target_vol = 1
                        if target_vol > 64: target_vol = 64
                        eff = event.get("effect")
                        if eff:
                            if eff[0] in ("arp","vib","vol"):
                                continue
                        event["effect"] = ("vol", target_vol)
    # Determine tempo changes for smooth transitions
    pattern_bpms = [None] * len(pattern_types)
    base_bpm = tempo if tempo >= 32 else 32
    intro_bpm = base_bpm - 6 if base_bpm - 6 >= 32 else base_bpm
    outro_bpm = base_bpm - 6 if base_bpm - 6 >= 32 else base_bpm
    break_bpm = base_bpm - 4 if base_bpm - 4 >= 32 else base_bpm
    if style in ["Blues","Swing"]:
        intro_bpm = base_bpm
        break_bpm = base_bpm
        outro_bpm = base_bpm
    if intro_count > 0:
        pattern_bpms[0] = intro_bpm
    if use_break_section:
        if "break" in pattern_types:
            break_idx = pattern_types.index("break")
            # Ramp up from intro to base before break
            if break_idx - intro_count > 1:
                span = break_idx - intro_count
                bpm_diff = base_bpm - intro_bpm
                for i in range(1, span+1):
                    pattern_bpms[intro_count + i - 1] = int(intro_bpm + bpm_diff * (i/(span+1)))
            pattern_bpms[break_idx] = break_bpm
            # Ramp up again after break
            if break_idx < len(pattern_types) - outro_count - 1:
                start = break_idx + 1
                end = len(pattern_types) - outro_count - 1
                span2 = end - start + 1
                bpm_diff2 = base_bpm - break_bpm
                for j in range(1, span2+1):
                    pattern_bpms[start + j - 1] = int(break_bpm + bpm_diff2 * (j/(span2+1)))
        if outro_count > 0:
            pattern_bpms[-1] = outro_bpm
    else:
        total_main = len(pattern_types) - intro_count - outro_count
        if total_main > 2:
            mid_idx = intro_count + total_main//2
            if base_bpm + 3 <= 255:
                pattern_bpms[mid_idx] = base_bpm + 3
            if intro_count > 0 and intro_bpm != base_bpm and total_main >= 1:
                pattern_bpms[intro_count] = int((intro_bpm + base_bpm)/2)
            last_main_idx = len(pattern_types) - 1 - (outro_count)
            if last_main_idx >= 0:
                pattern_bpms[last_main_idx] = base_bpm
        if outro_count > 0:
            pattern_bpms[-1] = outro_bpm
    if pattern_bpms[0] is None:
        pattern_bpms[0] = base_bpm
    # Insert initial speed and tempo
    initial_speed = 6
    if patterns_events[0][0][0] is None:
        patterns_events[0][0][0] = {"effect": ("speed", initial_speed)}
    else:
        patterns_events[0][0][0]["effect"] = ("speed", initial_speed)
    bpm_val = pattern_bpms[0] if pattern_bpms[0] else base_bpm
    if patterns_events[0][0][1] is None:
        patterns_events[0][0][1] = {"effect": ("tempo", bpm_val)}
    else:
        if patterns_events[0][0][2] is None:
            patterns_events[0][0][2] = {"effect": ("tempo", bpm_val)}
        else:
            patterns_events[0][0][1]["effect"] = ("tempo", bpm_val)
    # Insert tempo change events for other patterns
    for pi, bpm in enumerate(pattern_bpms):
        if pi == 0 or bpm is None:
            continue
        placed = False
        for ch in range(4):
            if patterns_events[pi][0][ch] is None:
                patterns_events[pi][0][ch] = {"effect": ("tempo", bpm)}
                placed = True
                break
            elif "effect" not in patterns_events[pi][0][ch]:
                patterns_events[pi][0][ch]["effect"] = {"effect": ("tempo", bpm)}
                placed = True
                break
        if not placed:
            patterns_events[pi][0][0]["effect"] = ("tempo", bpm)
    # Generate random song title
    word_list = ["Cool","Hot","Blue","Green","Deep","Dark","Light","Red","Smooth",
                 "Crystal","Electric","Funky","Magic","Digital","Mystic","Zen",
                 "Cosmic","Future","Vintage","Dream"]
    title = " ".join(random.choice(word_list) for _ in range(3))[:20]
    title_bytes = title.encode('ascii').ljust(20, b'\x00')
    # Build file header
    header = bytearray(title_bytes)
    # Sample headers (31 entries)
    for i in range(31):
        if i < len(samples):
            name_bytes = samples[i]["name"].encode('ascii')[:22].ljust(22, b'\x00')
            header.extend(name_bytes)
            length_words = len(samples[i]["data"]) // 2
            header.append((length_words >> 8) & 0xFF)
            header.append(length_words & 0xFF)
            finetune = samples[i].get("finetune", 0) & 0x0F
            header.append(finetune)
            vol = samples[i].get("volume", 64)
            if vol > 64: vol = 64
            header.append(vol & 0xFF)
            loop_start = samples[i].get("loop_start", 0)
            header.append((loop_start >> 8) & 0xFF)
            header.append(loop_start & 0xFF)
            loop_len = samples[i].get("loop_len", 1)
            header.append((loop_len >> 8) & 0xFF)
            header.append(loop_len & 0xFF)
        else:
            header.extend(b'\x00'*22)
            header.extend(b'\x00\x00')
            header.append(0)
            header.append(0)
            header.extend(b'\x00\x00')
            header.extend(b'\x00\x00')
    # Song length and restart
    song_length = len(pattern_order)
    header.append(song_length & 0xFF)
    header.append(0x00)
    # Pattern order table
    for pos in range(128):
        header.append(pattern_order[pos] if pos < len(pattern_order) else 0)
    header.extend(b'M.K.')
    # Pattern data
    pattern_data_bytes = bytearray()
    for pat_idx in range(len(pattern_types)):
        for row in range(64):
            for ch in range(4):
                event = patterns_events[pat_idx][row][ch]
                sample_num = 0
                period_val = 0
                eff_cmd = 0
                eff_param = 0
                if event:
                    if "inst" in event and "period" in event:
                        sample_num = event["inst"]
                        period_val = event["period"]
                    if "effect" in event:
                        eff = event["effect"]
                        if isinstance(eff, tuple):
                            if eff[0] == "arp":
                                eff_cmd = 0x0
                                x, y = eff[1]
                                eff_param = (x << 4) | (y & 0xF)
                            elif eff[0] == "vib":
                                eff_cmd = 0x4
                                x, y = eff[1] if isinstance(eff[1], tuple) else (vib_speed, vib_depth)
                                eff_param = ((x & 0xF) << 4) | (y & 0xF)
                            elif eff[0] == "vol":
                                eff_cmd = 0xC
                                vol_val = eff[1] if isinstance(eff[1], int) else 64
                                if vol_val < 0: vol_val = 0
                                if vol_val > 64: vol_val = 64
                                eff_param = vol_val & 0xFF
                            elif eff[0] == "speed":
                                eff_cmd = 0xF
                                eff_param = eff[1] & 0xFF
                                if eff_param < 1: eff_param = 6
                            elif eff[0] == "tempo":
                                eff_cmd = 0xF
                                param_val = eff[1] & 0xFF
                                if param_val < 32: param_val = 32
                                eff_param = param_val
                            elif eff[0] == "filter":
                                eff_cmd = 0xE
                                x = eff[1] & 0xF
                                eff_param = x
                sample_hi = (sample_num >> 4) & 0xF
                sample_lo = sample_num & 0xF
                period_hi = (period_val >> 8) & 0xF
                period_lo = period_val & 0xFF
                command = eff_cmd & 0xF
                param = eff_param & 0xFF
                byte1 = (sample_hi << 4) | period_hi
                byte2 = period_lo
                byte3 = (sample_lo << 4) | command
                byte4 = param
                pattern_data_bytes += bytes([byte1, byte2, byte3, byte4])
    # Sample data
    sample_data_bytes = bytearray()
    for s in samples:
        sample_data_bytes.extend(s["data"])
    # Write to file
    mod_data = header + pattern_data_bytes + sample_data_bytes
    filename_base = title.strip().replace(" ", "_")
    if not filename_base:
        filename_base = "module"
    file_path = os.path.join(output_dir, filename_base + ".mod")
    if os.path.exists(file_path):
        count = 1
        while os.path.exists(os.path.join(output_dir, f"{filename_base}_{count}.mod")):
            count += 1
        file_path = os.path.join(output_dir, f"{filename_base}_{count}.mod")
    with open(file_path, "wb") as f:
        f.write(mod_data)
    return file_path

# Build GUI
root = tk.Tk()
root.title("MOD Music Generator")
root.geometry("500x400")
style_var = tk.StringVar(value="Techno")
styles = ["Techno","Breakbeat","Acid","Drum & Bass","Dubstep","Swing","Synthpop","Meditation","Ambient","Chill","Blues"]
tk.Label(root, text="Musikstil:").pack(pady=5)
style_menu = ttk.Combobox(root, textvariable=style_var, values=styles, state="readonly")
style_menu.pack()
# Sliders for parameters
tempo_var = tk.IntVar(value=125)
vol_dyn_var = tk.IntVar(value=50)
rand_var = tk.IntVar(value=50)
tk.Label(root, text=f"Tempo (BPM)").pack()
tempo_slider = tk.Scale(root, from_=50, to=200, orient=tk.HORIZONTAL, variable=tempo_var)
tempo_slider.pack()
tk.Label(root, text="Lautstärke-Dynamik").pack()
vol_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, variable=vol_dyn_var)
vol_slider.pack()
tk.Label(root, text="Zufallsgrad der Melodien").pack()
rand_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, variable=rand_var)
rand_slider.pack()
# Effect checkboxes
echo_var = tk.BooleanVar(value=False)
vib_var = tk.BooleanVar(value=False)
arp_var = tk.BooleanVar(value=False)
filter_var = tk.BooleanVar(value=False)
effects_frame = tk.Frame(root)
tk.Checkbutton(effects_frame, text="Echo", variable=echo_var).grid(row=0, column=0, padx=5, sticky="w")
tk.Checkbutton(effects_frame, text="Vibrato", variable=vib_var).grid(row=0, column=1, padx=5, sticky="w")
tk.Checkbutton(effects_frame, text="Arpeggio", variable=arp_var).grid(row=0, column=2, padx=5, sticky="w")
tk.Checkbutton(effects_frame, text="Zufällige Filtermodulationen", variable=filter_var).grid(row=1, column=0, columnspan=3, sticky="w")
effects_frame.pack(pady=5)
# Song name display
song_name_var = tk.StringVar(value="")
tk.Label(root, textvariable=song_name_var, font=("Arial", 12, "italic")).pack(pady=5)
# Generate and Open functions
def generate_song():
    song_name_var.set("Erzeuge Modul...")
    root.update()
    file_path = generate_mod_file(style_var.get(), tempo=tempo_var.get(), volume_dynamic=vol_dyn_var.get(),
                                  melody_randomness=rand_var.get(), use_echo=echo_var.get(),
                                  use_vibrato=vib_var.get(), use_arpeggio=arp_var.get(), use_filter=filter_var.get())
    song_title = os.path.basename(file_path)
    song_name_var.set(f"Generiert: {song_title}")
def open_output_folder():
    folder = os.path.abspath("output")
    if os.name == "nt":
        os.startfile(folder)
    elif os.name == "posix":
        os.system(f'xdg-open "{folder}"')
    elif os.name == "darwin":
        os.system(f'open "{folder}"')
# Buttons
btn_frame = tk.Frame(root)
tk.Button(btn_frame, text="Generate Song", command=generate_song).grid(row=0, column=0, padx=10, pady=10)
tk.Button(btn_frame, text="Open Output Folder", command=open_output_folder).grid(row=0, column=1, padx=10, pady=10)
btn_frame.pack()
root.mainloop()
