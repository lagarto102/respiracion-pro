"""Guía de voz, pasos de control: elige las referencias y deja las frases listas para la app.

    python scripts/process-voice.py refs  --work <carpeta de generate-voice.py>
        Transcribe con Whisper las frases de referencia y elige, por idioma y voz, la toma que
        mejor se entiende. Escribe <work>/referencias-elegidas.json (lo usa "generate-voice.py clone").

    python scripts/process-voice.py clips --work <carpeta> --out <carpeta de salida>
        Para cada frase clonada: recorta el silencio, pone fundidos cortos, normaliza el volumen
        (-18 LUFS, pico máximo -1,5 dBFS) y comprueba con Whisper que dice lo que debe decir.
        Elige la mejor toma de cada frase (se entiende + voz más parecida a la referencia) y la
        guarda en <out>/<voz>/<idioma>/<frase>.ogg (Opus). Deja un informe en <work>/informe.json.
"""
import argparse
import difflib
import json
import pathlib
import re
import unicodedata

import numpy as np
import soundfile as sf

TARGET_LUFS = -18.0
PEAK_MAX = 10 ** (-1.5 / 20)
WHISPER = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-zß ]", " ", s)).strip()


def similar(a: str, b: str) -> float:
    # parecido y no idéntico: Whisper escribe "inala" por "inhala" (la h no suena)
    return difflib.SequenceMatcher(None, norm_text(a), norm_text(b)).ratio()


def to16k(x: np.ndarray, sr: int) -> np.ndarray:
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(sr, 16000)
    return resample_poly(x, 16000 // g, sr // g).astype(np.float32)


def transcribe(asr, x, sr, lang):
    pad = np.zeros(int(sr * 0.3), np.float32)
    res, _ = asr.transcribe(to16k(np.concatenate([pad, x, pad]), sr), language=lang, beam_size=5,
                            without_timestamps=True, condition_on_previous_text=False)
    res = list(res)
    return " ".join(r.text for r in res).strip(), (float(np.mean([r.avg_logprob for r in res])) if res else -9.0)


def trim(x: np.ndarray, sr: int) -> np.ndarray:
    """Quita el silencio de los extremos (umbral -40 dB respecto al pico)."""
    hop = int(sr * 0.005)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(env / (env.max() + 1e-12))
    idx = np.where(db > -40)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] * hop - int(sr * 0.015))
    b = min(len(x), (idx[-1] + 1) * hop + int(sr * 0.12))
    return x[a:b].copy()


def finish(x: np.ndarray, sr: int, meter) -> np.ndarray:
    x = x - np.mean(x)
    n_in, n_out = int(sr * 0.01), int(sr * 0.08)
    x[:n_in] *= np.linspace(0, 1, n_in)
    x[-n_out:] *= np.linspace(1, 0, n_out) ** 2
    try:
        loud = meter.integrated_loudness(np.concatenate([x, np.zeros(int(sr * 0.4), np.float32)]))
        gain = 10 ** ((TARGET_LUFS - loud) / 20) if np.isfinite(loud) else 1.0
    except Exception:
        gain = 1.0
    x = x * gain
    peak = float(np.max(np.abs(x)))
    if peak > PEAK_MAX:
        x = x * (PEAK_MAX / peak)
    return x.astype(np.float32)


def refs(work: pathlib.Path) -> None:
    from faster_whisper import WhisperModel
    asr = WhisperModel(WHISPER, device="cpu", compute_type="int8")
    best, report = {}, {}
    for meta_path in sorted((work / "referencias").glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        x, sr = sf.read(meta_path.with_suffix(".wav"), dtype="float32")
        heard, lp = transcribe(asr, x, sr, meta["lang"])
        score = similar(heard, meta["text"])
        report[meta_path.stem] = {"heard": heard, "match": round(score, 3), "logprob": round(lp, 3), "secs": round(len(x) / sr, 1)}
        print(meta_path.stem, round(score, 3), round(lp, 3), heard, flush=True)
        key = f"{meta['lang']}-{meta['voice']}"
        if score >= 0.9 and (key not in best or lp > report[best[key]]["logprob"]):
            best[key] = meta_path.stem
    (work / "referencias-informe.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (work / "referencias-elegidas.json").write_text(json.dumps(best, ensure_ascii=False, indent=1), encoding="utf-8")
    print("elegidas:", best, flush=True)


def clips(work: pathlib.Path, out: pathlib.Path) -> None:
    import pyloudnorm
    from faster_whisper import WhisperModel
    asr = WhisperModel(WHISPER, device="cpu", compute_type="int8")
    rows = {}
    for wav in sorted((work / "frases").glob("*.wav")):
        lang, voice, key, take = wav.stem.split("-")
        meta = json.loads(wav.with_suffix(".json").read_text(encoding="utf-8")) if wav.with_suffix(".json").exists() else {}
        x, sr = sf.read(wav, dtype="float32")
        y = finish(trim(x, sr), sr, pyloudnorm.Meter(sr, block_size=0.2))
        heard, lp = transcribe(asr, y, sr, lang)
        want = meta.get("text", "")
        match = similar(heard, want)
        secs = len(y) / sr
        ok = match >= 0.75 and 0.3 <= secs <= 2.4
        rows.setdefault(f"{lang}-{voice}-{key}", []).append(
            {"take": take, "heard": heard, "match": round(match, 3), "logprob": round(lp, 3), "secs": round(secs, 2),
             "sim": meta.get("similarity"), "ok": ok, "audio": y, "sr": sr})
        print(wav.stem, "ok" if ok else "--", round(match, 2), round(lp, 2), meta.get("similarity"), f"{secs:.2f}s", heard, flush=True)
    report = {}
    for name, takes in sorted(rows.items()):
        lang, voice, key = name.split("-")
        good = [t for t in takes if t["ok"]] or takes
        pick = max(good, key=lambda t: ((t["sim"] or 0) * 2 + t["logprob"] + t["match"]))
        dest = out / voice / lang / f"{key}.ogg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        sf.write(dest, pick["audio"], pick["sr"], format="OGG", subtype="OPUS", compression_level=0.7)
        report[name] = {"elegida": pick["take"], "todas": [{k: v for k, v in t.items() if k not in ("audio", "sr")} for t in takes]}
        print("elegida", name, "toma", pick["take"], "ok" if pick["ok"] else "REVISAR", flush=True)
    (work / "informe.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["refs", "clips"])
    ap.add_argument("--work", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.step == "refs":
        refs(pathlib.Path(args.work))
    else:
        clips(pathlib.Path(args.work), pathlib.Path(args.out))


if __name__ == "__main__":
    main()
