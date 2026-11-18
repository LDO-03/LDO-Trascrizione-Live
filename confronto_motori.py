#!/usr/bin/env python3
"""Confronto Parakeet TDT v3 e Qwen3-ASR 1.7B su un file audio, con WER rispetto a un testo di riferimento.

Uso:
  python confronto_motori.py audio.wav riferimento.txt [secondi]

audio.wav deve essere a 16 kHz (vedi istruzioni). riferimento.txt deve contenere il testo
scritto a mano per gli stessi secondi di audio.
"""
import os
import re
import sys
import tempfile
import time

import numpy as np
import soundfile as sf


def parole(testo):
    testo = re.sub(r"[^\w\s']", " ", testo.lower())
    return testo.split()


def wer(riferimento, ipotesi):
    r, h = parole(riferimento), parole(ipotesi)
    prev = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        cur = [i]
        for j, hw in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rw != hw)))
        prev = cur
    return prev[-1] / max(len(r), 1) * 100


def carica(path, secondi):
    x, sr = sf.read(path, dtype="float32")
    if sr != 16000:
        sys.exit(f"Il file è a {sr} Hz: convertilo a 16 kHz (vedi istruzioni).")
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x[: int(secondi * 16000)] if secondi else x


def parakeet():
    import mlx.core as mx
    from parakeet_mlx import from_pretrained
    from parakeet_mlx.audio import get_logmel
    m = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")

    def run(a):
        mel = get_logmel(mx.array(a.astype(np.float32)), m.preprocessor_config)
        return m.generate(mel)[0].text
    return run


def qwen(percorso_tmp):
    from qwen3_asr_mlx import Qwen3ASR
    m = Qwen3ASR.from_pretrained("mlx-community/Qwen3-ASR-1.7B-bf16")

    def run(a):
        sf.write(percorso_tmp, a, 16000)
        r = m.transcribe(percorso_tmp)
        return getattr(r, "text", None) or str(r)
    return run


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    audio = carica(sys.argv[1], float(sys.argv[3]) if len(sys.argv) > 3 else 60)
    with open(sys.argv[2], encoding="utf-8") as f:
        riferimento = f.read()
    tmp = os.path.join(tempfile.gettempdir(), "confronto_tmp.wav")

    motori = [("Parakeet TDT v3", lambda: parakeet()),
              ("Qwen3-ASR 1.7B bf16", lambda: qwen(tmp))]
    print(f"Audio: {len(audio) / 16000:.1f} secondi")
    for nome, costruisci in motori:
        try:
            t0 = time.time()
            run = costruisci()
            t1 = time.time()
            testo = run(audio)
            t2 = time.time()
            print(f"\n== {nome}")
            print(f"caricamento: {t1 - t0:.1f} s, trascrizione: {t2 - t1:.1f} s")
            print(f"WER: {wer(riferimento, testo):.2f}%")
            print(f"testo: {testo[:300]}")
            nomefile = "ipotesi_" + nome.split()[0].lower() + ".txt"
            with open(nomefile, "w", encoding="utf-8") as out:
                out.write(testo)
            print(f"testo completo salvato in: {nomefile}")
        except Exception as e:
            print(f"\n== {nome}: ERRORE {str(e)[:300]}")


if __name__ == "__main__":
    main()
