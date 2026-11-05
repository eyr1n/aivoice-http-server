import json
import tempfile
import threading
import winreg
from pathlib import Path
from typing import TypedDict

import pythonnet

pythonnet.load("netfx")
import clr

with winreg.OpenKey(
    winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AI\AIVoice\AIVoiceEditor\1.0"
) as key:
    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
clr.AddReference(str(Path(install_dir) / "AI.Talk.Editor.Api.dll"))
from AI.Talk.Editor import Api

WORK_PRESET_NAME = "aivoice-http-server"


class Style(TypedDict):
    Name: str
    Value: float


class MergedVoice(TypedDict):
    VoiceName: str


class MergedVoiceContainer(TypedDict):
    BasePitchVoiceName: str
    MergedVoices: list[MergedVoice]


class VoicePreset(TypedDict):
    PresetName: str
    VoiceName: str
    MergedVoiceContainer: MergedVoiceContainer
    Volume: float
    Speed: float
    Pitch: float
    PitchRange: float
    MiddlePause: int
    LongPause: int
    Styles: list[Style]


class AIVoice:
    def __init__(self) -> None:
        self._tts = Api.TtsControl()
        self._lock = threading.RLock()

    def connect(self) -> None:
        with self._lock:
            host_names = self._tts.GetAvailableHostNames()
            if not host_names:
                raise RuntimeError("no available host")
            self._tts.Initialize(host_names[0])
            if self._tts.Status == Api.HostStatus.NotRunning:
                self._tts.StartHost()
            self._tts.Connect()

    def disconnect(self) -> None:
        with self._lock:
            self._tts.Disconnect()

    def _reconnect_if_disconnected(self) -> None:
        if not self._tts.IsInitialized or self._tts.Status in (
            Api.HostStatus.NotRunning,
            Api.HostStatus.NotConnected,
        ):
            self.connect()

    def get_voice_preset_names(self) -> list[str]:
        with self._lock:
            self._reconnect_if_disconnected()
            return [
                name for name in self._tts.VoicePresetNames if name != WORK_PRESET_NAME
            ]

    def get_voice_preset(self, name: str) -> VoicePreset:
        with self._lock:
            self._reconnect_if_disconnected()
            if name not in self.get_voice_preset_names():
                raise KeyError(name)
            return json.loads(self._tts.GetVoicePreset(name))

    def synthesize(self, text: str, preset: VoicePreset) -> bytes:
        preset = {**preset, "PresetName": WORK_PRESET_NAME}
        with self._lock:
            self._reconnect_if_disconnected()
            if WORK_PRESET_NAME not in self._tts.VoicePresetNames:
                self._tts.AddVoicePreset(json.dumps(preset))
            else:
                self._tts.SetVoicePreset(json.dumps(preset))
            self._tts.CurrentVoicePresetName = WORK_PRESET_NAME

            self._tts.TextEditMode = Api.TextEditMode.Text
            self._tts.Text = text
            self._tts.TextSelectionStart = 0
            self._tts.TextSelectionLength = 0

            with tempfile.TemporaryDirectory() as tmp:
                wav = Path(tmp) / "output.wav"
                self._tts.SaveAudioToFile(str(wav))
                if not wav.is_file():
                    raise RuntimeError("could not save wav file")
                return wav.read_bytes()
