"""Genera la guía de voz de la app con Qwen3-TTS (Qwen, licencia Apache 2.0, uso comercial permitido).

No forma parte de la app: se usa en el PC para crear los audios de audio/voz/.

  1. diseño:  python scripts/generate-voice.py design --model <Qwen3-TTS-12Hz-1.7B-VoiceDesign> --out <carpeta>
     Crea la voz a partir de una descripción ("voz cálida, tranquila, acento de España...")
     diciendo una frase de referencia natural en cada idioma. Varias tomas por idioma y voz.
  2. clonado: python scripts/generate-voice.py clone --model <Qwen3-TTS-12Hz-0.6B-Base> --out <carpeta>
     Con la mejor toma de referencia (la elige scripts/process-voice.py refs), dice las 6
     frases de la app con esa misma voz: así "inhala" y "exhala" suenan a la misma persona.
  3. scripts/process-voice.py clips: corta, limpia, comprueba con Whisper y guarda en OGG.

El modelo se carga en bfloat16 (como se publica) y calcula en float32: en una CPU sin bf16
nativo es muchísimo más rápido (unos 20 s de cálculo por segundo de voz en un i7-10750H).
--precision int8 existe solo como referencia: probado el 28.09.2026, pronuncia mal y no va más rápido.
"""
import argparse
import gc
import json
import pathlib
import time

import soundfile as sf
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.ao.nn.quantized.dynamic import Linear as QLinear
from torch.ao.quantization import per_channel_dynamic_qconfig

# Frases de la app, en el orden de VOICE_KEYS de index.html.
LINES = {
    "es": [("ready", "Prepárate."), ("inhale", "Inhala."), ("hold", "Mantén."),
           ("exhale", "Exhala."), ("rest", "Espera."), ("done", "Hecho.")],
    "en": [("ready", "Get ready."), ("inhale", "Inhale."), ("hold", "Hold."),
           ("exhale", "Exhale."), ("rest", "Rest."), ("done", "Done.")],
    "de": [("ready", "Mach dich bereit."), ("inhale", "Einatmen."), ("hold", "Halten."),
           ("exhale", "Ausatmen."), ("rest", "Pause."), ("done", "Fertig.")],
}
# Frases de referencia (solo sirven para crear la voz; no van en la app).
REFERENCE = {
    "es": "Vamos a respirar juntos, con calma. Suelta los hombros y deja que el aire entre despacio.",
    "en": "Let's breathe together, calmly. Relax your shoulders and let the air come in slowly.",
    "de": "Lass uns gemeinsam ruhig atmen. Lass die Schultern locker und atme ganz langsam ein.",
}
LANG_NAME = {"es": "spanish", "en": "english", "de": "german"}
ACCENT = {
    "es": "a native Castilian Spanish accent from Spain",
    "en": "a clear, neutral native English accent",
    "de": "a native standard German (Hochdeutsch) accent",
}
VOICES = {
    "mujer": ("A calm, warm adult female voice with {accent}. She speaks slowly and softly, "
              "in a gentle, soothing, unhurried tone, like a meditation teacher guiding a breathing exercise."),
    "hombre": ("A calm, warm adult male voice with a soft, low pitch and {accent}. He speaks slowly "
               "and softly, in a gentle, soothing, unhurried tone, like a meditation teacher guiding a breathing exercise."),
}


class BF16Linear(nn.Module):
    """Pesos guardados en bfloat16 (como vienen), cálculo en float32: mismos números que el
    modelo original, sin pérdida por cuantizar, y en una CPU sin bf16 nativo va rápido.
    Los pesos van como "buffer" para que el modelo se siga declarando float32."""

    def __init__(self, lin: nn.Linear):
        super().__init__()
        self.register_buffer("weight", lin.weight.detach(), persistent=False)
        self.register_buffer("bias", None if lin.bias is None else lin.bias.detach().float(), persistent=False)

    def forward(self, x):
        return F.linear(x.float(), self.weight.float(), self.bias)


class BF16Embedding(nn.Module):
    """La tabla de texto (enorme) se queda en bfloat16 y devuelve float32."""

    def __init__(self, emb: nn.Embedding):
        super().__init__()
        self.register_buffer("weight", emb.weight.detach(), persistent=False)
        self.padding_idx = emb.padding_idx

    def forward(self, ids):
        return F.embedding(ids, self.weight, self.padding_idx).float()


def load_model(path: str, precision: str = "exact"):
    """precision: "exact" (pesos bf16, cálculo fp32) o "int8" (no recomendado: pronuncia mal)."""
    from qwen_tts import Qwen3TTSModel

    tts = Qwen3TTSModel.from_pretrained(path, device_map="cpu", dtype=torch.bfloat16)
    m = tts.model
    m.talker.model.text_embedding = BF16Embedding(m.talker.model.text_embedding)
    for parent in list(m.talker.model.layers.modules()):
        for name, child in list(parent.named_children()):
            if isinstance(child, nn.Linear):
                if precision == "int8":
                    w = child.float()
                    w.qconfig = per_channel_dynamic_qconfig
                    setattr(parent, name, QLinear.from_float(w))
                else:
                    setattr(parent, name, BF16Linear(child))
    for mod in m.modules():
        if isinstance(mod, (QLinear, BF16Linear, BF16Embedding)):
            continue
        for pn, p in list(mod.named_parameters(recurse=False)):
            if p.dtype == torch.bfloat16:
                mod._parameters[pn] = nn.Parameter(p.detach().float(), requires_grad=False)
        for bn, b in list(mod.named_buffers(recurse=False)):
            if b is not None and b.dtype == torch.bfloat16:
                mod._buffers[bn] = b.float()
    m.speech_tokenizer.model.float()                          # decodificador de audio en float32
    gc.collect()
    return tts


def design(args) -> None:
    out = pathlib.Path(args.out) / "referencias"
    out.mkdir(parents=True, exist_ok=True)
    tts = load_model(args.model, args.precision)
    for lang in args.langs.split(","):
        for voice in args.voices.split(","):
            instruct = VOICES[voice].format(accent=ACCENT[lang])
            for take in range(args.takes):
                name = f"{lang}-{voice}-{take}"
                if (out / f"{name}.wav").exists():
                    continue
                seed = args.seed + 101 * take + (0 if voice == "mujer" else 7)
                torch.manual_seed(seed)
                t = time.time()
                wavs, sr = tts.generate_voice_design(text=REFERENCE[lang], instruct=instruct,
                                                     language=LANG_NAME[lang], max_new_tokens=300)
                sf.write(out / f"{name}.wav", wavs[0], sr)
                (out / f"{name}.json").write_text(json.dumps(
                    {"lang": lang, "voice": voice, "take": take, "seed": seed, "text": REFERENCE[lang],
                     "instruct": instruct}, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"referencia {name}: {len(wavs[0]) / sr:.1f} s en {time.time() - t:.0f} s", flush=True)


def clone(args) -> None:
    base = pathlib.Path(args.out)
    chosen = json.loads((base / "referencias-elegidas.json").read_text(encoding="utf-8"))
    out = base / "frases"
    out.mkdir(parents=True, exist_ok=True)
    tts = load_model(args.model)
    for key, ref in chosen.items():                            # key = "es-mujer"
        lang, voice = key.split("-")
        if lang not in args.langs.split(",") or voice not in args.voices.split(","):
            continue
        prompt = tts.create_voice_clone_prompt(ref_audio=str(base / "referencias" / f"{ref}.wav"),
                                               ref_text=REFERENCE[lang])
        ref_emb = prompt[0].ref_spk_embedding.flatten().float()
        for take in range(args.takes):
            for phrase_key, text in LINES[lang]:
                path = out / f"{key}-{phrase_key}-{take}.wav"
                if path.exists():
                    continue
                torch.manual_seed(args.seed + 31 * take)
                t = time.time()
                wavs, sr = tts.generate_voice_clone(text=text, language=LANG_NAME[lang],
                                                    voice_clone_prompt=prompt, max_new_tokens=80)
                sf.write(path, wavs[0], sr)
                # parecido de la voz con la referencia (coseno entre huellas de voz del propio modelo)
                import librosa
                ssr = tts.model.speaker_encoder_sample_rate
                emb = tts.model.extract_speaker_embedding(audio=librosa.resample(y=wavs[0].astype("float32"), orig_sr=sr, target_sr=ssr), sr=ssr)
                sim = float(F.cosine_similarity(emb.flatten().float(), ref_emb, dim=0))
                path.with_suffix(".json").write_text(json.dumps({"text": text, "ref": ref, "seed": args.seed + 31 * take,
                                                                "similarity": round(sim, 4)}, ensure_ascii=False), encoding="utf-8")
                print(f"{path.name}: {len(wavs[0]) / sr:.2f} s en {time.time() - t:.0f} s, parecido {sim:.3f}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["design", "clone"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--langs", default="es,en,de")
    ap.add_argument("--voices", default="mujer,hombre")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--precision", choices=["exact", "int8"], default="exact")
    args = ap.parse_args()
    (design if args.step == "design" else clone)(args)


if __name__ == "__main__":
    main()

# Entorno usado el 28.09.2026: Python 3.12, torch 2.11 CPU + torchaudio 2.11 CPU,
# qwen-tts 0.1.1 (pip --no-deps) + transformers 4.57.3 + accelerate 1.12.0.
# Modelos (Hugging Face, Apache 2.0): Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign y Qwen/Qwen3-TTS-12Hz-0.6B-Base.
