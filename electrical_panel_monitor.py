import logging
import queue
import threading
import json
import pyaudio
import os
from collections import deque
import wave
import numpy as np
import time
import datetime
from scipy.signal import butter, lfilter


class ElectricalPanelMonitor:
    def __init__(self, config_file='monitor_config.json'):
        self.load_config(config_file)

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1

        self.ORDER = self.config.get('order', 5)
        self.CUTOFF = self.config.get('cutoff', 50)
        self.RATE = self.config.get('sample_rate', 44100)
        self.CHUNK = self.config.get('chunk_size', 512)
        self.TRIGGER_THRESHOLD = self.config.get('trigger_threshold', 50)

        self.PRE_RECORD_BUFFER = self.config.get('pre_record_seconds', 2.0)
        self.POST_RECORD_TIME = self.config.get('post_record_seconds', 5.0)
        self.MIN_SILENCE_TIME = self.config.get('min_silence_seconds', 2.0)

        self.ELECTRICAL_FREQS = [120]

        self.p = pyaudio.PyAudio()
        self.stream = None

        self.recording = False
        self.pre_buffer = deque(maxlen=int(self.PRE_RECORD_BUFFER * self.RATE / self.CHUNK))

        self.audio_queue = queue.Queue()
        self.writer_thread = None
        self.writer_thread_stop_event = threading.Event()

        self.detections = 0
        self.start_time = time.time()

        # Setup logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger('ElectricalPanelMonitor')

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        default_config = {
            "output_directory": "./recordings",
            "max_file_size_mb": 50,
            "trigger_threshold": 40,
            "pre_record_seconds": 2.0,
            "post_record_seconds": 5.0
        }

        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = default_config
            self.save_config(config_file)
            
        # Create output directory
        os.makedirs(self.config.get('output_directory', './recordings/'), exist_ok=True)

    def save_config(self, config_file):
        """Save configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def calculate_peak(self, data):
        audio_data = np.frombuffer(data, dtype=np.int16)
        if len(audio_data) == 0:
            return 0
        audio_data = np.nan_to_num(audio_data)
        return np.max(np.abs(audio_data))

    def find_usb_microphone(self):
        """Find the USB microphone device"""
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if ('USB' in device_info['name'] or 'Microphone' in device_info['name']) and device_info['maxInputChannels'] > 0:
                print(f"Found USB microphone: {device_info['name']}")
                return i
        return None
        
    def calculate_rms(self, data):
        audio_data = np.frombuffer(data, dtype=np.int16)
        if len(audio_data) == 0:
            return 0
        squared = np.mean(np.nan_to_num(audio_data) ** 2)
        if squared < 0 or np.isnan(squared):
            return 0  # or handle gracefully
        return np.sqrt(squared)

    def butter_highpass(self, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return b, a

    def highpass_filter(self, data, cutoff, fs, order=5):
        b, a = self.butter_highpass(cutoff, fs, order=order)
        filtered_data = lfilter(b, a, data)
        return filtered_data

    def butter_lowpass(self, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    def lowpass_filter(self, data, cutoff, fs, order=5):
        b, a = self.butter_lowpass(cutoff, fs, order=order)
        filtered_data = lfilter(b, a, data)
        return filtered_data

    def calculate_filtered_rms(self, data, cutoff=50, fs=44100, order=5):
        audio_data = np.frombuffer(data, dtype=np.int16)
        if len(audio_data) == 0:
            return 0
        audio_data = np.nan_to_num(audio_data)
        filtered_audio = self.highpass_filter(audio_data, cutoff, fs, order)
        squared = np.mean(filtered_audio ** 2)
        return np.sqrt(squared)

    def analyze_frequencies(self, data):
        """Analyze frequency content for electrical signatures"""
        audio_data = np.frombuffer(data, dtype=np.int16)
        fft = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(audio_data), 1/self.RATE)

        # Check for electrical frequency signatures
        electrical_detected = False
        freq_info = {}

        for freq in self.ELECTRICAL_FREQS:
            # Find the closest frequency bin
            freq_idx = np.argmin(np.abs(freqs - freq))
            magnitude = np.abs(fft[freq_idx])
            freq_info[f"{freq}Hz"] = magnitude

            # Check if this frequency is prominent
            if magnitude > np.mean(np.abs(fft)) * 2:
                electrical_detected = True

        return electrical_detected, freq_info

    def start_monitoring(self):
        device_index = self.find_usb_microphone()
        if device_index is None:
            self.logger.error("No USB microphone found! Please check connection.")
            return

        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.CHUNK
        )

        self.writer_thread_stop_event.clear()
        self.writer_thread = threading.Thread(target=self.audio_writer_thread, daemon=True)
        self.writer_thread.start()

        self.logger.info("Monitoring started. Press Ctrl+C to stop.")

        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.logger.info("Stopping monitor due to keyboard interrupt...")
        finally:
            self.clean_up()

    def monitor_loop(self):
        silence_start_time = None

        while True:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            except IOError:
                self.logger.warning("Input overflow detected, audio frame dropped.")
                continue

            # rms = self.calculate_rms(data)
            rms = self.calculate_filtered_rms(data, cutoff=self.CUTOFF, fs=self.RATE, order=self.ORDER)
            self.pre_buffer.append(data)
            current_time = datetime.datetime.now()

            if not self.recording and rms > self.TRIGGER_THRESHOLD:
                self.logger.info(f"TRIGGER DETECTED! RMS: {rms:.1f} at {current_time.strftime('%H:%M:%S')}")
                self.start_recording()
                silence_start_time = None

            if self.recording:
                self.audio_queue.put(data)

                if rms < self.TRIGGER_THRESHOLD:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time > self.MIN_SILENCE_TIME:
                        self.stop_recording(datetime.datetime.now())
                        silence_start_time = None
                else:
                    silence_start_time = None

            if int(time.time()) % 5 == 0 and time.time() - int(time.time()) < 0.02:
                status = "RECORDING" if self.recording else "LISTENING"
                self.logger.info(f"{status} - RMS: {rms:6.1f} - Detections: {self.detections}")

    def start_recording(self):
        self.recording = True
        self.logger.info("Recording started with pre-buffer...")
        for buf in list(self.pre_buffer):
            self.audio_queue.put(buf)

    def stop_recording(self, timestamp):
        self.recording = False
        self.detections += 1
        self.audio_queue.put(None)  # Sentinel to indicate recording end
        self.logger.info(f"Trigger recording stopped at {timestamp.strftime('%H:%M:%S')}")

    def audio_writer_thread(self):
        recording_data = []
        current_filename = None
        current_filepath = None
        analysis_report = None
        timestamps = []
        

        while not self.writer_thread_stop_event.is_set():
            try:
                data = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            if data is None:
                # Finish current recording file
                if recording_data:
                    timestamp_str = timestamps[0].strftime('%Y%m%d_%H%M%S') if timestamps else datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    current_filename = f"panel_buzz_{timestamp_str}.wav"
                    current_filepath = os.path.join(self.config['output_directory'], current_filename)
                    self.logger.info(f"Saving recording to {current_filepath}")
                    self._save_recording(recording_data, current_filepath, timestamps)
                    recording_data = []
                    timestamps = []
                continue

            recording_data.append(data)
            timestamps.append(datetime.datetime.now())

    def _save_recording(self, data_chunks, filepath, timestamps):
        all_data = b''.join(data_chunks)
        electrical_detected, freq_info = self.analyze_frequencies(all_data)

        # Save audio file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(all_data)

        # Save analysis report
        report_file = filepath.replace('.wav', '_analysis.txt')
        with open(report_file, 'w') as f:
            f.write(f"Electrical Panel Audio Analysis\n")
            f.write(f"Recording Time: {timestamps[0] if timestamps else ''}\n")
            f.write(f"Duration: {len(data_chunks) * self.CHUNK / self.RATE:.2f} seconds\n")
            f.write(f"Electrical Frequencies Detected: {electrical_detected}\n\nFrequency Analysis:\n")
            for freq, magnitude in freq_info.items():
                f.write(f"  {freq}: {magnitude:.1f}\n")
            f.write(f"\nFile: {os.path.basename(filepath)}\n")

        self.logger.info(f"Recording saved: {os.path.basename(filepath)}")
        self.logger.info(f"Electrical frequencies detected: {electrical_detected}")

    def clean_up(self):
        self.logger.info("Stopping writer thread and cleaning up...")
        self.writer_thread_stop_event.set()
        if self.writer_thread:
            self.writer_thread.join(timeout=5)

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

        runtime = time.time() - self.start_time
        self.logger.info(f"Monitoring session ended. Runtime: {runtime / 60:.1f} minutes")
        self.logger.info(f"Total detections: {self.detections}")
        
if __name__ == "__main__":
    panel_qc = ElectricalPanelMonitor()
    panel_qc.start_monitoring()
