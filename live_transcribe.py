#!/usr/bin/env python3
"""
Trascrizione live in italiano per conferenze, su Mac.
Lanciato dall'app "Trascrizione Live" tramite avvia.sh.

Durante la conferenza scrive una bozza temporanea (backup) riga per riga.
Alla fine chiede di salvare la conferenza in un file .docx dove si vuole.
"""

import argparse
import os
import queue
import re
import signal
import subprocess
import sys
import termios
import tty
import threading
from datetime import datetime, timedelta

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, VADIterator, get_speech_timestamps

SR = 16000
CHUNK = 512  # obbligatorio per Silero a 16 kHz
PROMPT = "Conferenza in lingua italiana. Termini tecnici e nomi propri vanno scritti con la grafia corretta."
VERDE = "\033[1;32m"
RESET = "\033[0m"

fermata = threading.Event()


def scrivi(testo="", fine="\n"):
    print(f"{VERDE}{testo}{RESET}", end=fine, flush=True)


def chiedi(testo):
    return input(f"{VERDE}{testo}{RESET}")


def su_segnale(signum, frame):
    # finestra del Terminale chiusa o processo terminato: salvo la bozza e mi fermo
    fermata.set()


signal.signal(signal.SIGHUP, su_segnale)
signal.signal(signal.SIGTERM, su_segnale)


def nome_file(testo):
    pulito = re.sub(r"[^\w\- ]", "", testo).strip().replace(" ", "_")
    return pulito[:60] or "Conferenza"


def tieni_sveglio():
    # impedisce al Mac di andare in stop finché il programma gira
    try:
        return subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    except FileNotFoundError:
        return None


def scegli_destinazione(nome_suggerito):
    script = f'POSIX path of (choose file name with prompt "Salva la conferenza" default name "{nome_suggerito}")'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    percorso = r.stdout.strip()
    if not percorso.lower().endswith(".docx"):
        percorso += ".docx"
    return percorso


def esporta_docx(bozza, destinazione):
    from docx import Document
    from docx.shared import Pt

    with open(bozza, encoding="utf-8") as f:
        blocchi = [b.strip() for b in re.split(r"\n\s*\n", f.read()) if b.strip()]

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    for blocco in blocchi:
        p = doc.add_paragraph()
        m = re.match(r"^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\s+(.*)$", blocco, re.DOTALL)
        if m:
            titolo = p.add_run(m.group(1) + "  ")
            titolo.bold = True
            p.add_run(m.group(2).replace("\n", " "))
        else:
            p.add_run(blocco)
    doc.save(destinazione)


def salva_conferenza(bozza, nome):
    """Apre subito la finestra di salvataggio (.docx). Se si annulla, la bozza resta intatta."""
    try:
        scrivi("Scegli dove salvare la conferenza in formato .DOCX.")
        destinazione = scegli_destinazione(nome_file(nome) + ".docx")
        if destinazione is None:
            scrivi("Salvataggio annullato.")
            scrivi(f"La bozza di sicurezza resta in: {bozza}")
            scrivi("Per salvarla in seguito: python live_transcribe.py --esporta FILE")
            return
        esporta_docx(bozza, destinazione)
        scrivi(f"SALVATO: {destinazione}")
        scrivi(f"La bozza di sicurezza resta in: {bozza}")
    except KeyboardInterrupt:
        scrivi(f"Salvataggio interrotto. La bozza di sicurezza resta in: {bozza}")
    except Exception as e:
        scrivi(f"Errore nel salvataggio: {e}")
        scrivi(f"La bozza di sicurezza è intatta in: {bozza}")


def carica_trascrittore(modello_nome):
    """Motore primario Qwen3-ASR bf16; di riserva Parakeet TDT v3, poi Whisper turbo su MLX, poi faster-whisper.
    I modelli MLX vengono caricati al primo audio, dentro il thread di trascrizione:
    MLX lega gli stream al thread che li crea."""
    import tempfile
    import numpy as np
    import soundfile as sf
    tmp = os.path.join(tempfile.gettempdir(), "trascrizione_live_tmp.wav")

    def carica_qwen():
        from qwen3_asr_mlx import Qwen3ASR
        m = Qwen3ASR.from_pretrained("mlx-community/Qwen3-ASR-1.7B-bf16")

        def esegui(audio):
            sf.write(tmp, np.asarray(audio, dtype=np.float32), SR)
            r = m.transcribe(tmp)
            return getattr(r, "text", None) or str(r)
        return esegui

    def carica_parakeet():
        import mlx.core as mx
        from parakeet_mlx import from_pretrained
        from parakeet_mlx.audio import get_logmel
        m = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")

        def esegui(audio):
            x = mx.array(np.asarray(audio, dtype=np.float32))
            return m.generate(get_logmel(x, m.preprocessor_config))[0].text
        return esegui

    def carica_whisper_mlx():
        import mlx_whisper
        repo = "mlx-community/whisper-large-v3-turbo" if "turbo" in modello_nome \
            else "mlx-community/whisper-large-v3-mlx"

        def trascrivi(audio):
            risultato = mlx_whisper.transcribe(
                audio, path_or_hf_repo=repo, language="it",
                initial_prompt=PROMPT, condition_on_previous_text=False)
            return risultato.get("text", "")
        return trascrivi

    def carica_faster_whisper():
        modello = WhisperModel(modello_nome, device="cpu", compute_type="int8")

        def trascrivi(audio):
            segmenti, _ = modello.transcribe(
                audio, language="it", beam_size=1, vad_filter=False,
                condition_on_previous_text=False, initial_prompt=PROMPT)
            return " ".join(s.text.strip() for s in segmenti)
        return trascrivi

    caricatori = [("Qwen3-ASR bf16", carica_qwen), ("Parakeet TDT v3", carica_parakeet)]
    stato = {"attivo": None, "fallito": set(), "whisper": None}

    def trascrivi(audio):
        if stato["attivo"] is None:
            for nome, caricatore in caricatori:
                if nome in stato["fallito"]:
                    continue
                try:
                    stato["attivo"] = (nome, caricatore())
                    break
                except Exception as e:
                    stato["fallito"].add(nome)
                    scrivi(f"{nome} non disponibile ({str(e)[:160]}).")
        if stato["attivo"] is not None:
            try:
                return stato["attivo"][1](audio)
            except Exception as e:
                scrivi(f"{stato['attivo'][0]} errore ({str(e)[:160]}): passo al motore successivo.")
                stato["fallito"].add(stato["attivo"][0])
                stato["attivo"] = None
                return trascrivi(audio)
        if stato["whisper"] is None:
            try:
                stato["whisper"] = carica_whisper_mlx()
            except ImportError:
                stato["whisper"] = carica_faster_whisper()
        return stato["whisper"](audio)

    return trascrivi, "Qwen3-ASR bf16, con Parakeet e Whisper di riserva"


def scegli_file():
    script = 'POSIX path of (choose file with prompt "Scegli il file audio o video da trascrivere")'
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    percorso = r.stdout.strip()
    return percorso if r.returncode == 0 and percorso else None


def scegli_sorgente():
    scrivi("Sorgente audio:")
    scrivi("  1  Microfono del Mac")
    scrivi("  2  Ingresso audio esterno (mixer collegato all'ingresso cuffia)")
    scrivi("  3  File audio o video (MP3, M4A, MP4, MOV)")
    while True:
        scelta = chiedi("Scegli 1, 2 o 3: ").strip()
        if scelta == "1":
            return "live", None
        if scelta == "2":
            ingressi = [(i, d) for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]
            for i, d in ingressi:
                scrivi(f"  {i}  {d['name']}")
            idx = chiedi("Numero dell'ingresso: ").strip()
            if idx.isdigit() and any(i == int(idx) for i, _ in ingressi):
                return "live", int(idx)
            scrivi("Numero non valido.")
        elif scelta == "3":
            percorso = scegli_file()
            if percorso:
                return "file", percorso
            scrivi("Nessun file scelto.")
        else:
            scrivi("Scelta non valida.")


def inizio_registrazione(percorso):
    st = os.stat(percorso)
    return datetime.fromtimestamp(getattr(st, "st_birthtime", st.st_mtime))


def converti_audio(percorso):
    import tempfile
    import soundfile as sf
    tmp = os.path.join(tempfile.gettempdir(), "ldo_file_16k.wav")
    r = subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", percorso, tmp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"impossibile leggere il file: {r.stderr.strip()}")
    x, sr = sf.read(tmp, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x


def trascrivi_file(percorso, args, bf, trascrivi_audio, inizio_reg):
    x = converti_audio(percorso)
    scrivi(f"Audio: {len(x) / SR:.0f} secondi. Trascrizione in corso...")
    segmenti = get_speech_timestamps(torch.from_numpy(x), load_silero_vad(), sampling_rate=SR,
                                     min_silence_duration_ms=args.pausa_frase, speech_pad_ms=30)
    max_frase = int(args.max_frase * SR)
    preroll = int(0.3 * SR)
    blocchi = []
    for sg in segmenti:
        a, b = sg["start"], sg["end"]
        while b - a > max_frase:
            blocchi.append((a, a + max_frase))
            a += max_frase
        blocchi.append((a, b))
    fine_prec = None
    for a, b in blocchi:
        nuovo = fine_prec is None or (a - fine_prec) / SR >= args.pausa_capoverso
        intestazione = None
        if nuovo:
            intestazione = (inizio_reg + timedelta(seconds=a / SR)).strftime("%d/%m/%Y %H:%M:%S")
        fine_prec = b
        testo = trascrivi_audio(x[max(a - preroll, 0):b]).strip()
        if len(testo) < 2:
            continue
        riga = (f"\n\n{intestazione} " if intestazione else " ") + testo
        bf.write(riga)
        bf.flush()
        os.fsync(bf.fileno())
        scrivi(riga, fine="")
    scrivi("")
    scrivi("Trascrizione del file completata.")


def main():
    p = argparse.ArgumentParser(description="Trascrizione live in italiano")
    p.add_argument("--nome", default="Conferenza", help="nome della conferenza")
    p.add_argument("--bozze", default=os.path.expanduser("~/Library/Application Support/TrascrizioneLive/bozze"))
    p.add_argument("--esporta", default=None, help="esporta una bozza esistente in .docx e termina")
    p.add_argument("--device", type=int, default=None, help="indice del microfono")
    p.add_argument("--modello", default="large-v3-turbo")
    p.add_argument("--pausa-capoverso", type=float, default=0.8)
    p.add_argument("--pausa-frase", type=int, default=500)
    p.add_argument("--max-frase", type=float, default=12.0)
    args = p.parse_args()

    if args.esporta:
        salva_conferenza(args.esporta, os.path.splitext(os.path.basename(args.esporta))[0])
        return

    os.makedirs(args.bozze, exist_ok=True)
    inizio = datetime.now()
    bozza = os.path.join(args.bozze, f"{nome_file(args.nome)}_{inizio:%Y%m%d_%H%M%S}.txt")
    bf = open(bozza, "a", encoding="utf-8")
    bf.write(f"CONFERENZA: {args.nome}\nINIZIO: {inizio:%d/%m/%Y %H:%M:%S}\n")
    bf.flush()
    os.fsync(bf.fileno())

    scrivi(f"TRASCRIZIONE LIVE - {args.nome}")
    scrivi("Caricamento del modello...")

    modalita, dato = scegli_sorgente()
    caffe = tieni_sveglio()
    trascrivi_audio, motore = carica_trascrittore(args.modello)
    if modalita == "file":
        try:
            trascrivi_file(dato, args, bf, trascrivi_audio, inizio_registrazione(dato))
        except Exception as e:
            scrivi(f"ERRORE nella trascrizione del file: {e}")
        bf.write("\n")
        bf.flush()
        os.fsync(bf.fileno())
        bf.close()
        if caffe:
            caffe.terminate()
        salva_conferenza(bozza, args.nome)
        return
    if dato is not None:
        args.device = dato
    vad_model = load_silero_vad()
    vad = VADIterator(vad_model, threshold=0.5, sampling_rate=SR,
                      min_silence_duration_ms=args.pausa_frase, speech_pad_ms=30)

    audio_q = queue.Queue()
    jobs = queue.Queue()
    ascolto = threading.Event()  # acceso = il microfono ascolta

    def callback(indata, frames, time_info, status):
        if status:
            scrivi(f"[avviso audio] {status}")
        audio_q.put(indata[:, 0].copy())

    def worker():
        while True:
            job = jobs.get()
            if job is None:
                break
            audio, intestazione = job
            try:
                testo = trascrivi_audio(audio).strip()
            except Exception as e:
                scrivi(f"[errore trascrizione: {e}]")
                continue
            if len(testo) < 2:
                continue
            riga = (f"\n\n{intestazione} " if intestazione else " ") + testo
            bf.write(riga)
            bf.flush()
            os.fsync(bf.fileno())
            scrivi(riga, fine="")

    t_worker = threading.Thread(target=worker, daemon=True)
    t_worker.start()

    def avviso(stato_testo):
        scrivi("")
        scrivi(f"[{stato_testo}]")

    def tastiera(fd):
        while not fermata.is_set():
            c = os.read(fd, 1).decode("utf-8", errors="ignore")
            if c == " ":
                if ascolto.is_set():
                    ascolto.clear()
                    avviso("MICROFONO SPENTO - in pausa")
                else:
                    ascolto.set()
                    avviso("MICROFONO ACCESO - in ascolto")

    preroll = int(0.3 * SR)
    max_frase = int(args.max_frase * SR)
    total = 0
    vad_base = 0  # il VAD riparte da zero dopo ogni pausa: converto i suoi indici
    pending = np.zeros(0, dtype=np.float32)
    pending_off = 0
    active = False
    utt_start = 0
    last_end = None
    nuovo_capoverso = False
    intestazione = None

    def estrai(a, b):
        lo = max(a - preroll - pending_off, 0)
        hi = max(b - pending_off, lo)
        return pending[lo:hi].copy()

    fd = None
    vecchio = None
    if sys.stdin.isatty():
        fd = sys.stdin.fileno()
        vecchio = termios.tcgetattr(fd)
        tty.setcbreak(fd)  # tasti singoli, Ctrl+C resta attivo

    scrivi("[MICROFONO SPENTO]")
    if fd is not None:
        threading.Thread(target=tastiera, args=(fd,), daemon=True).start()

    try:
        while not fermata.is_set():
            if not ascolto.wait(timeout=0.5):
                continue
            with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=CHUNK,
                                device=args.device, callback=callback):
                while not fermata.is_set() and ascolto.is_set():
                    try:
                        chunk = audio_q.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    pending = np.concatenate([pending, chunk])
                    ev = vad(torch.from_numpy(chunk))
                    total += len(chunk)

                    if ev and "start" in ev and not active:
                        s = vad_base + int(ev["start"])
                        active = True
                        utt_start = s
                        gap = (s - last_end) / SR if last_end is not None else float("inf")
                        nuovo_capoverso = gap >= args.pausa_capoverso
                        if nuovo_capoverso:
                            istante = datetime.now() - timedelta(seconds=(total - s) / SR)
                            intestazione = istante.strftime("%d/%m/%Y %H:%M:%S")

                    if ev and "end" in ev and active:
                        e = vad_base + int(ev["end"])
                        active = False
                        last_end = e
                        jobs.put((estrai(utt_start, e), intestazione if nuovo_capoverso else None))
                        nuovo_capoverso = False
                        intestazione = None

                    if active and (total - utt_start) >= max_frase:
                        jobs.put((estrai(utt_start, total), intestazione if nuovo_capoverso else None))
                        nuovo_capoverso = False
                        intestazione = None
                        utt_start = total

                    keep_from = (utt_start - preroll) if active else (total - preroll)
                    keep_from = max(keep_from, pending_off)
                    pending = pending[keep_from - pending_off:]
                    pending_off = keep_from

            # microfono spento: chiudo la frase in corso e azzero il riconoscimento del parlato
            if active:
                jobs.put((estrai(utt_start, total), intestazione if nuovo_capoverso else None))
                active = False
                nuovo_capoverso = False
                intestazione = None
                last_end = None
            while not audio_q.empty():
                audio_q.get_nowait()
            vad.reset_states()
            vad_base = total
            pending = np.zeros(0, dtype=np.float32)
            pending_off = total

    except KeyboardInterrupt:
        scrivi("\n[conferenza terminata con Ctrl+C]")
    except Exception as e:
        scrivi(f"\nERRORE microfono o audio: {e}")
    finally:
        if fd is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, vecchio)
        if active:
            jobs.put((estrai(utt_start, total), intestazione if nuovo_capoverso else None))
        jobs.put(None)
        t_worker.join()
        bf.write("\n")
        bf.flush()
        os.fsync(bf.fileno())
        bf.close()
        if caffe:
            caffe.terminate()

    scrivi("")
    scrivi("==========================================")
    scrivi("  CONFERENZA TERMINATA")
    scrivi("==========================================")

    if fermata.is_set():
        scrivi(f"Finestra chiusa. Bozza salvata in: {bozza}")
        scrivi("Per esportarla in seguito: python live_transcribe.py --esporta FILE")
    else:
        salva_conferenza(bozza, args.nome)


if __name__ == "__main__":
    main()
