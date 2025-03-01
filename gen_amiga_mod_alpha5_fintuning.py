import tkinter as tk
import math, random, struct
#source: https://github.com/zeittresor/py_gen_amiga_mod
# Period values for notes C-1 to B-3 (ProTracker)
period_table = [
    856,808,762,720,678,640,604,570,538,508,480,453,
    428,404,381,360,339,320,302,285,269,254,240,226,
    214,202,190,180,170,160,151,143,135,127,120,113
]

# Sample generation functions for Kick, Snare, Hat, and waveform instruments
def generate_kick():
    length = 2000
    data = []
    phase = 0.0
    for i in range(length):
        # Frequency sweeps down for the kick drum (drop pitch)
        freq = 50.0 + (5.0 - 50.0) * (i / length)
        phase += 2 * math.pi * freq / 44100.0
        # Amplitude decays linearly
        amp = 1.0 - i/length
        sample_val = amp * math.sin(phase)
        # Add a short high-frequency click at the beginning
        if i < length / 20:
            sample_val += 0.5 * math.sin(2 * math.pi * 2000 * (i/44100.0))
        # Clamp to [-1,1] and convert to signed 8-bit
        sample_val = max(-1.0, min(1.0, sample_val))
        data.append(int(sample_val * 127) & 0xFF)
    return bytes(data)

def generate_snare():
    length = 1200
    data = []
    for i in range(length):
        # White noise with exponential decay envelope
        noise = random.uniform(-1, 1)
        envelope = math.exp(-5 * i/length)
        sample_val = noise * envelope
        sample_val = max(-1.0, min(1.0, sample_val))
        data.append(int(sample_val * 127) & 0xFF)
    return bytes(data)

def generate_hat():
    length = 300
    data = []
    prev = 0.0
    for i in range(length):
        # White noise high-frequency content (differentiation) for metallic hat
        noise = random.uniform(-1, 1)
        envelope = math.exp(-10 * i/length)
        sample_val = (noise - prev) * envelope
        prev = noise
        sample_val = max(-1.0, min(1.0, sample_val))
        data.append(int(sample_val * 127) & 0xFF)
    return bytes(data)

def generate_triangle_wave(cycles=1):
    # One cycle of a triangle wave (to loop for sustained tone)
    samples_per_cycle = 32
    data = []
    for i in range(samples_per_cycle * cycles):
        t = (i % samples_per_cycle) / samples_per_cycle
        # Triangle wave from -1 to 1
        val = 2 * abs(2*t - 1) - 1
        val *= 0.8  # slightly reduce amplitude to avoid distortion
        data.append(int(max(-1.0, min(1.0, val)) * 127) & 0xFF)
    return bytes(data)

def generate_sine_wave(cycles=1, harmonics=[]):
    # Base sine wave with optional added harmonics (as (multiple, amplitude) tuples)
    samples_per_cycle = 32
    data = []
    max_amp = 1 + sum(abs(amp) for _, amp in harmonics)
    for i in range(samples_per_cycle * cycles):
        t = (i % samples_per_cycle) / samples_per_cycle
        val = math.sin(2 * math.pi * t)
        for mul, amp in harmonics:
            val += amp * math.sin(2 * math.pi * mul * t)
        # Normalize combined wave
        val /= max_amp
        data.append(int(max(-1.0, min(1.0, val)) * 127) & 0xFF)
    return bytes(data)

# Function to compose and save the ProTracker .MOD file
def compose_mod(style, scale_name, key_name, intro_patterns, main_patterns, outro_patterns,
               bpm, use_arpeggio, use_vibrato, use_tremolo, use_echo, use_filter):
    # Define scale intervals for various modes
    scales = {
        "Dur": [0,2,4,5,7,9,11],       # Major (Ionian)
        "Moll": [0,2,3,5,7,8,10],      # Natural minor (Aeolian)
        "Dorisch": [0,2,3,5,7,9,10],   # Dorian
        "Phrygisch": [0,1,3,5,7,8,10], # Phrygian
        "Lydisch": [0,2,4,6,7,9,11],   # Lydian
        "Mixolydisch": [0,2,4,5,7,9,10],# Mixolydian
        "Lokrich": [0,1,3,5,6,8,10]    # Locrian
    }
    if scale_name not in scales:
        scale_name = "Dur"
    scale = scales[scale_name]
    # Map key name to semitone offset (C=0, C#=1, ..., B=11)
    note_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    key_offset = note_names.index(key_name) if key_name in note_names else 0
    style_lower = style.lower()
    # Set base octaves for bass, chord, and lead instruments (octave numbers relative to ProTracker C-1)
    if style_lower == "blues":
        bass_oct = 1   # C-1 (very low)
        chord_oct = 2  # C-2 (mid-low for organ)
        lead_oct = 3   # C-3 (higher for lead)
    else:  # Techno and others
        bass_oct = 1
        chord_oct = 2
        lead_oct = 3
    # Determine total patterns and measures
    total_patterns = intro_patterns + main_patterns + outro_patterns
    total_measures = total_patterns * 4
    # Generate chord progression (sequence of scale degrees for each measure)
    progression = [0] * total_measures
    # Intro progression: mostly tonic, ending on V (dominant) if possible
    if intro_patterns > 0:
        for m in range(intro_patterns * 4):
            if m == intro_patterns*4 - 1 and len(scale) >= 5:
                progression[m] = 4  # V chord
            else:
                progression[m] = 0  # I chord
    main_start_measure = intro_patterns * 4
    main_measures = main_patterns * 4
    if style_lower == "blues":
        # Use a 12-bar blues pattern if possible
        twelve_bar = [0,0,0,0, 3,3, 0,0, 4,3, 0,4]  # I,I,I,I, IV,IV, I,I, V,IV, I,V
        for i in range(main_measures):
            progression[main_start_measure + i] = twelve_bar[i % 12] if main_measures >= 12 else 0
        if main_measures < 12:
            # Insert IV and V chords in shorter blues patterns
            if main_measures >= 4 and len(scale) >= 4:
                progression[main_start_measure + main_measures//2] = 3  # IV in middle
            if main_measures >= 2 and len(scale) >= 5:
                progression[main_start_measure + main_measures - 2] = 4  # V in penultimate measure
            if main_measures > 0:
                progression[main_start_measure + main_measures - 1] = 4 if outro_patterns > 0 and len(scale)>=5 else 0
    else:
        # Techno: largely static tonic with occasional alternate chord (e.g. VI degree)
        alt_degree = 5 if len(scale) >= 6 else (4 if len(scale) >= 5 else 0)
        for i in range(main_measures):
            if main_measures >= 4 and (i+1) % 4 == 0:
                progression[main_start_measure + i] = alt_degree
            else:
                progression[main_start_measure + i] = 0
        # End on tonic unless outro will handle resolution
        if main_measures > 0 and outro_patterns == 0:
            progression[main_start_measure + main_measures - 1] = 0
    # Outro progression: all tonic (I chord)
    outro_start_measure = main_start_measure + main_measures
    for m in range(outro_patterns * 4):
        progression[outro_start_measure + m] = 0
    # Prepare pattern data structure [pattern][row][channel] for events
    patterns = [[[None for _ in range(4)] for _ in range(64)] for _ in range(total_patterns)]
    # Helper: get triad chord (root, third, fifth) semitone values relative to key
    def get_chord_degrees(deg):
        root = scale[deg % len(scale)] + 12 * (deg // len(scale))
        third_deg = (deg + 2) % len(scale)
        fifth_deg = (deg + 4) % len(scale)
        third = scale[third_deg] + 12 * ((deg + 2) // len(scale))
        fifth = scale[fifth_deg] + 12 * ((deg + 4) // len(scale))
        return root, third, fifth
    # Helper: place a note or effect event into the pattern data
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
    # Compose patterns: iterate measures and beats to place notes
    for pat in range(total_patterns):
        for meas in range(4):
            global_meas = pat * 4 + meas
            if global_meas >= total_measures:
                break
            # Determine chord degrees for this measure
            root_deg = progression[global_meas]
            root_val, third_val, fifth_val = get_chord_degrees(root_deg)
            # Actual note semitones (0-35) for bass, chord, lead instruments (with key and octave)
            chord_root = root_val + key_offset + chord_oct*12
            chord_third = third_val + key_offset + chord_oct*12
            chord_fifth = fifth_val + key_offset + chord_oct*12
            bass_root = root_val + key_offset + bass_oct*12
            bass_third = third_val + key_offset + bass_oct*12
            bass_fifth = fifth_val + key_offset + bass_oct*12
            # Compute arpeggio effect parameters (x = third, y = fifth intervals in semitones)
            arp_x = (third_val - root_val) % 12
            arp_y = (fifth_val - root_val) % 12
            # Place chord accompaniment on channel 2
            if use_arpeggio:
                # Use ProTracker arpeggio effect (0xy) on the chord root note at beat 1 and 3 of the measure
                for half in [0, 2]:  # 0 = beginning of measure, 2 = halfway (2nd half of measure)
                    row = meas * 16 + half * 4
                    set_event(pat, row, 2, inst=5, period_idx=min(35, max(0, chord_root)))
                    set_event(pat, row, 2, effect_cmd=0x0, effect_param=(arp_x << 4) | (arp_y & 0xF))
            else:
                # Without arpeggio, play broken chord (root on beat1, third/fifth on beat3)
                root_row = meas * 16 + 0
                alt_row = meas * 16 + 8
                # Root note
                set_event(pat, root_row, 2, inst=5, period_idx=min(35, max(0, chord_root)))
                # Second chord note (alternate between third and fifth for variety)
                alt_note = chord_third if (global_meas % 2 == 0) else chord_fifth
                set_event(pat, alt_row, 2, inst=5, period_idx=min(35, max(0, alt_note)))
                # Apply tremolo effect to sustained chord if selected (on the root note event)
                if use_tremolo:
                    trem_rate = 8  # speed
                    trem_depth = 4  # depth
                    set_event(pat, root_row, 2, effect_cmd=0x7, effect_param=(trem_rate << 4) | (trem_depth & 0xF))
            # Place drum and bass events for each beat in this measure
            for beat in range(4):
                row = meas * 16 + beat * 4
                if style_lower == "blues":
                    # Blues style: Kick on beats 1 & 3, Snare on 2 & 4, walking Bass on all quarters
                    if beat % 2 == 0:
                        # Kick drum on channel 0
                        set_event(pat, row, 0, inst=1)
                        # Bass note on channel 1 (on beat 1 & 3)
                        bass_note = bass_root if beat == 0 else bass_fifth
                        set_event(pat, row, 1, inst=4, period_idx=min(35, max(0, bass_note)))
                    else:
                        # Snare drum on channel 1
                        set_event(pat, row, 1, inst=2)
                        # Bass note on channel 0 (on beat 2 & 4)
                        if beat == 1:
                            bass_note = bass_third
                        else:
                            # Approach next chord root on beat 4
                            if global_meas < total_measures - 1:
                                next_root_deg = progression[global_meas + 1]
                                next_root_val = get_chord_degrees(next_root_deg)[0]
                                next_root = next_root_val + key_offset + bass_oct*12
                                # approach from below or above
                                if next_root > bass_root:
                                    bass_note = bass_fifth if bass_fifth < next_root else bass_third
                                else:
                                    bass_note = bass_third if bass_third > next_root else bass_fifth
                            else:
                                bass_note = bass_root
                        set_event(pat, row, 0, inst=4, period_idx=min(35, max(0, bass_note)))
                else:
                    # Techno style: 4-on-the-floor kick, off-beat hats, snare on 2 & 4, off-beat bass
                    # Kick on every beat (channel 0)
                    set_event(pat, row, 0, inst=1)
                    # Snare on beats 2 & 4 (channel 1)
                    if beat == 1 or beat == 3:
                        set_event(pat, row, 1, inst=2)
                    # Hi-hat on every off-beat eighth (channel 1), interleaved with snare
                    if beat < 3:
                        hat_row = row + 2  # halfway to next beat
                        set_event(pat, hat_row, 1, inst=3)
                        # Bass on off-beats (channel 0)
                        bass_row = row + 2
                        bass_note = bass_root
                        # Alternate bass octave for variety
                        if ((pat * 4 + meas) + beat) % 2 == 0:
                            bass_choice = bass_root
                        else:
                            bass_choice = bass_root + 12 if bass_root + 12 <= 35 else bass_root
                        set_event(pat, bass_row, 0, inst=4, period_idx=min(35, max(0, bass_choice)))
            # Melody/Lead line on channel 3 (skip in intro and outro)
            if pat < intro_patterns or pat >= intro_patterns + main_patterns:
                continue
            last_pitch = None
            # Melodic probability: Blues tends to more rests, Techno more continuous
            prob_note = 0.7 if style_lower == "blues" else 0.9
            prob_two = 0.2 if style_lower == "blues" else 0.1
            # Consider 8 sub-beats (16th rows) per measure for possible melody note placements
            for sub in range(8):
                sub_row = meas * 16 + sub * 2  # each sub is 2 rows (8th note)
                on_beat = (sub % 2 == 0)
                if on_beat:
                    # Decide if a note starts on this beat
                    if random.random() >= prob_note:
                        continue
                else:
                    # Off-beat note only if a second note in the beat is likely
                    if random.random() >= prob_two:
                        continue
                # Choose a melody note pitch
                if last_pitch is None or (on_beat and sub == 0):
                    # Start of phrase or measure: favor chord tone (root, third, or fifth)
                    choices = []
                    for tone in (chord_root, chord_third, chord_fifth):
                        if 0 <= tone <= 35:
                            choices.append(tone)
                    pitch = random.choice(choices) if choices else chord_root
                else:
                    # Otherwise, select a scale note near the last pitch
                    scale_notes = []
                    for oct_shift in range(lead_oct-1, lead_oct+2):
                        for interval in scale:
                            note_val = interval + key_offset + oct_shift*12
                            if 0 <= note_val <= 35:
                                scale_notes.append(note_val)
                    scale_notes = sorted(set(scale_notes))
                    # Choose a note within ±5 semitones of last pitch for smoothness
                    close_notes = [n for n in scale_notes if last_pitch is not None and abs(n - last_pitch) <= 5]
                    pitch = random.choice(close_notes if close_notes else scale_notes)
                pitch_idx = min(35, max(0, pitch))
                set_event(pat, sub_row, 3, inst=6, period_idx=pitch_idx)
                # Apply vibrato effect to melody note if selected
                if use_vibrato:
                    vib_speed = 8
                    vib_depth = 2
                    set_event(pat, sub_row, 3, effect_cmd=0x4, effect_param=(vib_speed << 4) | (vib_depth & 0xF))
                last_pitch = pitch_idx
    # Echo effect: copy melody notes to chord channel (channel 2) after a delay with lower volume
    if use_echo:
        echo_delay_rows = 8 if style_lower == "blues" else 4  # longer echo for blues (half a measure), shorter (one beat) for techno
        for pat in range(total_patterns):
            for row in range(64):
                evt = patterns[pat][row][3]
                if isinstance(evt, dict) and evt.get("inst") == 6 and evt.get("period") is not None:
                    # Compute target position for echo note
                    total_index = pat * 64 + row + echo_delay_rows
                    target_pat = total_index // 64
                    target_row = total_index % 64
                    if target_pat < total_patterns:
                        # Only place echo if chord channel is free at that position
                        if patterns[target_pat][target_row][2] is None:
                            patterns[target_pat][target_row][2] = {
                                "inst": 6,
                                "period": evt["period"],
                                "effect": 0xC,    # Volume effect Cxx
                                "param": 0x20     # Set volume ~50% (0x20 in hex)
                            }
    # Filter modulation: toggle Amiga low-pass filter at section boundaries
    if use_filter:
        # Turn filter ON at intro start (for muffled intro)
        if intro_patterns > 0:
            set_event(0, 0, 0, effect_cmd=0xE, effect_param=0x01)
        # Turn filter OFF at main start (bright main section)
        if main_patterns > 0:
            first_main_pat = intro_patterns
            set_event(first_main_pat, 0, 0, effect_cmd=0xE, effect_param=0x00)
        # Turn filter ON again at outro start (muffled outro)
        if outro_patterns > 0:
            first_outro_pat = intro_patterns + main_patterns
            set_event(first_outro_pat, 0, 0, effect_cmd=0xE, effect_param=0x01)
    # Set initial tempo (Fxx) and speed (F06) at song start
    set_event(0, 0, 1, effect_cmd=0xF, effect_param=0x06)  # speed 6
    tempo_hex = bpm if bpm >= 32 else 125  # bpm <32 interpreted as speed, ensure reasonable default
    set_event(0, 0, 2, effect_cmd=0xF, effect_param=tempo_hex & 0xFF)
    # Prepare sample instruments data (1-6 as defined above, 7-31 empty)
    samples = {}
    # Instrument 1: Kick
    kick_data = generate_kick()
    samples[1] = {"name": "Kick", "data": kick_data, "volume": 64, "finetune": 0,
                  "loop_start": 0, "loop_length": 1, "length": len(kick_data)}
    # Instrument 2: Snare
    snare_data = generate_snare()
    samples[2] = {"name": "Snare", "data": snare_data, "volume": 48, "finetune": 0,
                  "loop_start": 0, "loop_length": 1, "length": len(snare_data)}
    # Instrument 3: Hat (Hi-hat)
    hat_data = generate_hat()
    samples[3] = {"name": "Hat", "data": hat_data, "volume": 40, "finetune": 0,
                  "loop_start": 0, "loop_length": 1, "length": len(hat_data)}
    # Instrument 4: Bass (triangle wave, looped)
    bass_data = generate_triangle_wave()
    samples[4] = {"name": "Bass", "data": bass_data, "volume": 64, "finetune": 0,
                  "loop_start": 0, "loop_length": len(bass_data), "length": len(bass_data)}
    # Instrument 5: Chord (organ-like sine wave with 1 octave harmonic, looped)
    chord_data = generate_sine_wave(harmonics=[(2, 0.5)])
    samples[5] = {"name": "Chord", "data": chord_data, "volume": 50, "finetune": 0,
                  "loop_start": 0, "loop_length": len(chord_data), "length": len(chord_data)}
    # Instrument 6: Lead (square wave, looped)
    # Create 32-sample square wave (half samples at max, half at min)
    lead_data = bytes([0x7F]*16 + [0x81]*16)
    samples[6] = {"name": "Lead", "data": lead_data, "volume": 64, "finetune": 0,
                  "loop_start": 0, "loop_length": len(lead_data), "length": len(lead_data)}
    # Instruments 7-31: empty
    for inst in range(7, 32):
        samples[inst] = {"name": "", "data": b"", "volume": 0, "finetune": 0,
                         "loop_start": 0, "loop_length": 1, "length": 0}
    # Build .MOD file bytes
    # Header: Title (20 bytes)
    title = f"Generated {style}".encode('ascii')[:20]
    title += bytes(20 - len(title))
    mod_bytes = bytearray(title)
    # Instruments 1-31 descriptors (30 bytes each)
    for inst in range(1, 32):
        s = samples[inst]
        name_bytes = s["name"].encode('ascii')[:22]
        name_bytes += bytes(22 - len(name_bytes))
        mod_bytes.extend(name_bytes)
        # Sample length in words (two bytes, big-endian)
        mod_bytes.extend(struct.pack(">H", s["length"] // 2))
        # Finetune (1 byte) and Volume (1 byte)
        mod_bytes.append(s["finetune"] & 0x0F)
        vol = s["volume"]
        mod_bytes.append(vol if vol <= 64 else 64)
        # Loop start and length in words (each 2 bytes)
        loop_start_words = s["loop_start"] // 2
        loop_length_words = s["loop_length"] // 2
        if loop_length_words == 0:
            loop_length_words = 1  # No loop -> set loop length to 1
        mod_bytes.extend(struct.pack(">H", loop_start_words))
        mod_bytes.extend(struct.pack(">H", loop_length_words))
    # Song length and restart position (2 bytes)
    song_length = total_patterns if total_patterns < 128 else 127
    mod_bytes.append(song_length & 0xFF)
    mod_bytes.append(0x7F)  # 0x7F indicates no specific restart (ProTracker convention)
    # Pattern order table (128 bytes)
    order_list = list(range(total_patterns)) + [0] * (128 - total_patterns)
    mod_bytes.extend(bytes(order_list[:128]))
    # Format tag "M.K." for 4-channel MOD
    mod_bytes.extend(b"M.K.")
    # Pattern data
    for pat in range(total_patterns):
        for row in range(64):
            for ch in range(4):
                cell = patterns[pat][row][ch]
                if cell is None:
                    # No event: 4 zero bytes
                    mod_bytes.extend(b'\x00\x00\x00\x00')
                else:
                    inst_num = cell.get("inst", 0)
                    period_idx = cell.get("period", None)
                    effect = cell.get("effect", 0) or 0
                    param = cell.get("param", 0) or 0
                    # Compute 12-bit period value
                    period_val = period_table[period_idx] if period_idx is not None and inst_num != 0 else 0
                    # Split into four bytes
                    inst_high = (inst_num >> 4) & 0xF
                    inst_low = inst_num & 0xF
                    period_high = (period_val >> 8) & 0xF
                    period_low = period_val & 0xFF
                    byte1 = (inst_high << 4) | period_high
                    byte2 = period_low
                    byte3 = (inst_low << 4) | (effect & 0xF)
                    byte4 = param & 0xFF
                    mod_bytes.extend([byte1, byte2, byte3, byte4])
    # Sample data for all instruments
    for inst in range(1, 32):
        mod_bytes.extend(samples[inst]["data"])
    # Write to file
    with open("generated_song.mod", "wb") as mod_file:
        mod_file.write(mod_bytes)

# Setup GUI
root = tk.Tk()
root.title("MOD Generator")

# Style selection (Techno or Blues)
style_var = tk.StringVar(value="Techno")
tk.Label(root, text="Stil:").grid(row=0, column=0, sticky="e")
tk.OptionMenu(root, style_var, "Techno", "Blues").grid(row=0, column=1, sticky="w")

# Scale (Tonleiter) selection
scale_var = tk.StringVar(value="Dur")
tk.Label(root, text="Skala:").grid(row=1, column=0, sticky="e")
scales_list = ["Dur","Moll","Dorisch","Phrygisch","Lydisch","Mixolydisch","Lokrich"]
tk.OptionMenu(root, scale_var, *scales_list).grid(row=1, column=1, sticky="w")

# Key (Grundton) selection
key_var = tk.StringVar(value="C")
tk.Label(root, text="Grundton:").grid(row=2, column=0, sticky="e")
keys_list = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
tk.OptionMenu(root, key_var, *keys_list).grid(row=2, column=1, sticky="w")

# Pattern count controls for Intro, Main, Outro
tk.Label(root, text="Intro Patterns:").grid(row=3, column=0, sticky="e")
intro_spin = tk.Spinbox(root, from_=0, to=8, width=5)
intro_spin.grid(row=3, column=1, sticky="w")
tk.Label(root, text="Main Patterns:").grid(row=4, column=0, sticky="e")
main_spin = tk.Spinbox(root, from_=1, to=20, width=5)
main_spin.grid(row=4, column=1, sticky="w")
tk.Label(root, text="Outro Patterns:").grid(row=5, column=0, sticky="e")
outro_spin = tk.Spinbox(root, from_=0, to=8, width=5)
outro_spin.grid(row=5, column=1, sticky="w")

# Effect options as checkboxes
arpeggio_var = tk.BooleanVar()
vibrato_var = tk.BooleanVar()
tremolo_var = tk.BooleanVar()
echo_var = tk.BooleanVar()
filter_var = tk.BooleanVar()
tk.Checkbutton(root, text="Arpeggio", variable=arpeggio_var).grid(row=6, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Vibrato", variable=vibrato_var).grid(row=7, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Tremolo", variable=tremolo_var).grid(row=8, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Echo", variable=echo_var).grid(row=9, column=0, columnspan=2, sticky="w")
tk.Checkbutton(root, text="Filter Mod", variable=filter_var).grid(row=10, column=0, columnspan=2, sticky="w")

# Tempo slider (BPM)
tk.Label(root, text="Tempo (BPM):").grid(row=11, column=0, sticky="e")
tempo_scale = tk.Scale(root, from_=60, to=180, orient="horizontal", length=300)
tempo_scale.set(125)
tempo_scale.grid(row=11, column=1, sticky="w")

# Status label to show generation progress
status_label = tk.Label(root, text="")
status_label.grid(row=13, column=0, columnspan=2)

# Generate button callback
def generate_song():
    style = style_var.get()
    scale = scale_var.get()
    key = key_var.get()
    intro = int(intro_spin.get())
    main = int(main_spin.get())
    outro = int(outro_spin.get())
    bpm = int(tempo_scale.get())
    use_arp = arpeggio_var.get()
    use_vib = vibrato_var.get()
    use_trem = tremolo_var.get()
    use_echo_flag = echo_var.get()
    use_filter_flag = filter_var.get()
    status_label.config(text="Generiere .mod Datei...")
    root.update()
    compose_mod(style, scale, key, intro, main, outro, bpm,
               use_arp, use_vib, use_trem, use_echo_flag, use_filter_flag)
    status_label.config(text="Modul generiert: 'generated_song.mod'")

# Generate button
tk.Button(root, text="Generate .MOD", command=generate_song).grid(row=12, column=0, columnspan=2, pady=5)

root.mainloop()
