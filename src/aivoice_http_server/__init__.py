import io
from typing import Required, TypedDict

import soundfile as sf
import soxr
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from .aivoice import AIVoice, MergedVoiceContainer, Style, VoicePreset

aivoice = AIVoice()
app = FastAPI()


class PartialVoicePreset(TypedDict, total=False):
    PresetName: Required[str]
    MergedVoiceContainer: MergedVoiceContainer
    Volume: float
    Speed: float
    Pitch: float
    PitchRange: float
    MiddlePause: int
    LongPause: int
    Styles: list[Style]


class SynthesizeRequest(BaseModel):
    text: str
    preset: PartialVoicePreset
    sample_rate: int | None = None


class SynthesizeResponse(Response):
    media_type = "audio/wav"


@app.get("/presets")
def voice_presets() -> list[str]:
    return aivoice.get_voice_preset_names()


@app.get("/presets/{name}")
def voice_preset(name: str) -> VoicePreset:
    try:
        return aivoice.get_voice_preset(name)
    except KeyError:
        raise HTTPException(status_code=404)


@app.post("/synthesize", response_class=SynthesizeResponse)
def synthesize(request: SynthesizeRequest) -> SynthesizeResponse:
    try:
        base = aivoice.get_voice_preset(request.preset["PresetName"])
    except KeyError:
        raise HTTPException(status_code=422)

    def to_dict(l: list[Style]) -> dict[str, float]:
        return {item["Name"]: item["Value"] for item in l}

    def to_list(d: dict[str, float]) -> list[Style]:
        return [{"Name": name, "Value": value} for name, value in d.items()]

    def merge_styles(
        base_styles: list[Style], request_styles: list[Style]
    ) -> list[Style]:
        return to_list(to_dict(base_styles) | to_dict(request_styles))

    styles = merge_styles(base["Styles"], request.preset.get("Styles") or [])
    preset = base | request.preset | {"Styles": styles}
    wav = aivoice.synthesize(request.text, preset)

    with sf.SoundFile(io.BytesIO(wav)) as f:
        sample_rate = request.sample_rate or f.samplerate
        if sample_rate == f.samplerate and f.subtype == "PCM_16" and f.channels == 1:
            return SynthesizeResponse(wav)
        samples = f.read()
        if f.channels > 1:
            samples = samples.mean(axis=1)
        if sample_rate != f.samplerate:
            samples = soxr.resample(samples, f.samplerate, sample_rate)

    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, subtype="PCM_16", format="WAV")
    return SynthesizeResponse(buffer.getvalue())
