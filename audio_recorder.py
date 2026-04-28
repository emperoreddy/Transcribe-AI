import sounddevice as sd
import soundfile as sf
import queue
import threading
import numpy as np

class AudioRecorder:
    def __init__(self, output_filename="recordings/recording.wav", sample_rate=16000, channels=1):
        self.output_filename = output_filename
        self.sample_rate = sample_rate
        self.channels = channels
        self.q = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.recording_thread = None

    def get_input_devices(self):
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        # Return device name and its index
        return {d['name']: d['index'] for d in input_devices}

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(indata.copy())

    def _record(self, device_index):
        try:
            with sf.SoundFile(self.output_filename, mode='w', samplerate=self.sample_rate,
                              channels=self.channels, subtype='PCM_16') as file:
                with sd.InputStream(samplerate=self.sample_rate, device=device_index,
                                    channels=self.channels, callback=self._audio_callback):
                    while self.is_recording:
                        file.write(self.q.get())
        except Exception as e:
            print(f"Error recording audio: {e}")
        finally:
            self.is_recording = False

    def start_recording(self, device_index=None):
        if self.is_recording:
            return
        self.is_recording = True
        # Clear the queue
        while not self.q.empty():
            self.q.get()
        self.recording_thread = threading.Thread(target=self._record, args=(device_index,))
        self.recording_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join()
        return self.output_filename
