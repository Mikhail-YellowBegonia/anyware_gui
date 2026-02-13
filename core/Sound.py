import pygame
import numpy as np
import time
import random
import threading



class SoundEngine:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.bits = 16
        # Initialize mixer if not already initialized
        if not pygame.mixer.get_init():
            # Force stereo (channels=2) for better compatibility
            pygame.mixer.init(frequency=sample_rate, size=-self.bits, channels=2, buffer=1024)
        self.max_amp = 2 ** (self.bits - 1) - 1
        
        # Channels
        # 0: BGM Drone
        # 1: SFX (Typing, etc)
        # 2: Melody/Music
        self.channel_bgm = pygame.mixer.Channel(0)
        self.channel_sfx = pygame.mixer.Channel(1)
        self.channel_music = pygame.mixer.Channel(2)
        
        self.bgm_thread = None
        self.running = False
        
        # State
        self.sfx_enabled = True
        self.music_enabled = True

        # Note frequencies (A4 = 440Hz)
        self.notes = {
            'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
            'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
            'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
            'C6': 1046.50
        }

    def _generate_wave(self, freq, duration, wave_type='sine', volume=0.5):
        """Generates a raw audio waveform."""
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        elif wave_type == 'noise':
            wave = np.random.uniform(-1, 1, n_samples)
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        elif wave_type == 'cyber': # A custom gritty texture
            # Mix of detuned saws and noise for that "wired" sound
            w1 = 2 * (t * freq * 0.99 - np.floor(t * freq * 0.99 + 0.5))
            w2 = 2 * (t * freq * 1.01 - np.floor(t * freq * 1.01 + 0.5))
            noise = np.random.uniform(-0.1, 0.1, n_samples)
            wave = (w1 + w2) * 0.5 + noise
        else:
            wave = np.sin(2 * np.pi * freq * t)

        # Simple Envelope (Fade In/Out to prevent clicking)
        attack = int(self.sample_rate * 0.01) # 10ms
        release = int(self.sample_rate * 0.05) # 50ms
        
        if n_samples > attack + release:
            env = np.ones(n_samples)
            env[:attack] = np.linspace(0, 1, attack)
            env[-release:] = np.linspace(1, 0, release)
            wave *= env

        # Create stereo signal by stacking the wave twice
        audio_mono = (wave * volume * self.max_amp).astype(np.int16)
        audio_stereo = np.column_stack((audio_mono, audio_mono))
        return audio_stereo

    def create_sound(self, freq, duration, wave_type='square', volume=0.3):
        """Creates a Pygame Sound object."""
        wave_data = self._generate_wave(freq, duration, wave_type, volume)
        return pygame.sndarray.make_sound(wave_data)

    def toggle_sfx(self, enabled=None):
        """Toggle SFX on/off or set explicitly."""
        if enabled is None: self.sfx_enabled = not self.sfx_enabled
        else: self.sfx_enabled = enabled

    def toggle_music(self, enabled=None):
        """Toggle Music/BGM on/off or set explicitly."""
        if enabled is None: self.music_enabled = not self.music_enabled
        else: self.music_enabled = enabled
        
        if not self.music_enabled:
            self.stop_bgm()
        else:
            self.start_bgm() # Restart ambient loop if it was running

    def play_sfx(self, name):
        """Plays preset GUI sound effects."""
        if not self.sfx_enabled: return
        
        if name == 'typing':
            # High pitched short blip
            snd = self.create_sound(random.randint(800, 1200), 0.02, 'square', 0.1)
            snd.play()
        elif name == 'confirm':
            # Two tone rising
            snd1 = self.create_sound(880, 0.1, 'sine', 0.2)
            # We can't easily chain sounds without composing the array, 
            # so we just play one simple tone for lightness or overlay them
            snd1.play()
        elif name == 'boot':
            # Low hum rising
            # Doing a frequency sweep is harder with static buffers, 
            # we'll simulate a 'power on' noise with a low cyber tone
            snd = self.create_sound(110, 1.5, 'cyber', 0.4)
            snd.fadeout(1000)
            snd.play()
        elif name == 'error':
            # Low square buzz
            snd = self.create_sound(150, 0.3, 'sawtooth', 0.3)
            snd.play()

    def play_melody(self, melody_list, bpm=120, wave_type='triangle'):
        """
        Play a melody sequence in a separate thread.
        melody_list format: [('Note', Duration_beats), ...]
        Example: [('C4', 1), ('E4', 1), ('G4', 2)]
        Use 'R' or None for rest.
        """
        if not self.music_enabled: return

        def _play_thread():
            beat_duration = 60.0 / bpm
            for note, beats in melody_list:
                if not self.music_enabled: break # Allow interrupting
                
                duration_sec = beats * beat_duration
                if note and note != 'R':
                    freq = self.notes.get(note, 440)
                    # Create sound slightly shorter than full duration to separate notes
                    snd = self.create_sound(freq, duration_sec * 0.9, wave_type, 0.2)
                    self.channel_music.play(snd)
                
                time.sleep(duration_sec)
        
        threading.Thread(target=_play_thread, daemon=True).start()

    def _bgm_loop(self):
        """A simple generative ambient loop thread."""
        # Theme: "Wired" - Ethereal, repetitive, slightly unsettling
        sequence = [220, 196, 220, 246] # A3, G3, A3, B3
        base_freq = 55 # A1 (Deep drone)
        
        # Pre-generate drone to save CPU
        drone = self.create_sound(base_freq, 4.0, 'cyber', 0.15)
        
        step = 0
        while self.running:
            if not self.music_enabled: 
                time.sleep(1)
                continue

            # Play Drone Layer every 4 seconds
            if step % 8 == 0:
                # Only play if channel isn't busy (avoid stacking too much)
                if not self.channel_bgm.get_busy():
                    self.channel_bgm.play(drone, fade_ms=500)
            
            # Play melodic bleeps occasionally
            if random.random() > 0.6:
                note = random.choice(sequence)
                # Random octave
                if random.random() > 0.5: note *= 2
                
                tone_type = 'sine' if random.random() > 0.3 else 'triangle'
                bleep = self.create_sound(note, 0.3, tone_type, 0.1)
                # Play bleep on SFX channel to not interrupt drone, or use a separate channel
                # Using sfx channel for random bleeps is fine
                if self.sfx_enabled: 
                    self.channel_sfx.play(bleep)
            
            time.sleep(0.5)
            step += 1

    def start_bgm(self):
        if not self.running:
            self.running = True
            self.bgm_thread = threading.Thread(target=self._bgm_loop, daemon=True)
            self.bgm_thread.start()

    def stop_bgm(self):
        # We don't kill the thread, just pause the sound output logic
        # But for full stop we can set running=False
        # For toggle logic, we just rely on self.music_enabled check in loop
        self.channel_bgm.stop()

# Singleton instance for easy import
sound_sys = SoundEngine()
