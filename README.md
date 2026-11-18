# LDO Trascrizione Live

**Italiano** | [English](#english)


App per Mac che trascrive in italiano conferenze e interviste, in locale e senza Internet dopo il primo avvio.
Finestra Terminale in verde su nero, bozza di sicurezza durante la trascrizione, esportazione finale in `.docx`.

## Funzioni

- **Tre sorgenti**: microfono del Mac, ingresso audio esterno (mixer sull'ingresso cuffia), file audio o video (MP3, M4A, MP4, MOV).
- **Capoversi con orario**: a ogni pausa di 0,8 s va a capo con una riga vuota e data e ora `GG/MM/AAAA HH:MM:SS`. Per i file l'orario è la data di creazione del file più il tempo di audio.
- **Barra spaziatrice** accende/spegne il microfono; **Ctrl+C** termina e apre il salvataggio del `.docx`.
- Finestra separata con la legenda dei comandi.
- **Motore**: Qwen3-ASR (MLX); di riserva Parakeet TDT v3 e Whisper large-v3-turbo.

## Requisiti

- Mac con chip Apple Silicon (MLX non funziona sui Mac Intel)
- Python 3.11 (`installa_python.command` lo installa se manca)
- circa 7 GB liberi e una connessione per il primo avvio (librerie e modelli)

## Installazione

1. Scarica `LDO_Trascrizione_Live.dmg` dalla sezione *Releases*, oppure costruiscilo con `crea_dmg.command`.
2. Esegui `installa_python.command` se Python 3.11 non c'è.
3. Apri il DMG e trascina l'app in Applicazioni. Se macOS la blocca: tasto destro > Apri, oppure
   `xattr -cr "/Applications/LDO Trascrizione Live.app"`.
4. Al primo avvio consenti il microfono e attendi l'installazione dei componenti.

Per costruire dal sorgente: `crea_dmg.command` (crea `LDO_Trascrizione_Live.dmg`), poi `installa.command` (copia l'app in `~/Applications`).

## Confronto tra motori

`confronto_motori.py` misura tempi e WER di Parakeet e Qwen3-ASR su un file a 16 kHz con un testo di riferimento.
Nei test fatti, su un file di circa 3,5 minuti, Parakeet trascrive in circa 2 s e Qwen in circa 18 s. L'accuratezza dipende dal tipo di audio: verifica sul tuo materiale.

## Note

- Trascrivi solo con il consenso delle persone registrate.
- Il programma scarica i modelli da Hugging Face, ognuno con la propria licenza (Qwen3-ASR: Apache-2.0; Parakeet TDT v3: CC-BY-4.0; Whisper: MIT).
- Non testato su Mac Intel.

## Licenza

MIT, vedi `LICENSE`.

---

## English

**LDO Trascrizione Live** is a Mac app that transcribes Italian conferences and interviews locally, with no Internet connection needed after the first launch. It runs in a green-on-black Terminal window, writes a safety draft while transcribing, and exports a `.docx` file at the end.

### Features

- **Three sources**: Mac microphone, external audio input (a mixer plugged into the headphone jack), or an audio/video file (MP3, M4A, MP4, MOV).
- **Timestamped paragraphs**: after each 0.8 s pause it starts a new paragraph, separated by a blank line, with date and time `DD/MM/YYYY HH:MM:SS`. For files, the time is the file's creation date plus the elapsed audio time.
- **Spacebar** turns the microphone on and off; **Ctrl+C** ends the session and opens the save dialog for the `.docx`.
- A separate window shows the command legend.
- **Engine**: Qwen3-ASR (MLX), with Parakeet TDT v3 and Whisper large-v3-turbo as fallbacks.

### Requirements

- Mac with Apple Silicon (MLX does not run on Intel Macs)
- Python 3.11 (`installa_python.command` installs it if missing)
- About 7 GB of free space and an Internet connection on first launch (libraries and models)

### Installation

1. Download `LDO_Trascrizione_Live.dmg` from *Releases*, or build it with `crea_dmg.command`.
2. Run `installa_python.command` if Python 3.11 is missing.
3. Open the DMG and drag the app to Applications. If macOS blocks it: right-click > Open, or run
   `xattr -cr "/Applications/LDO Trascrizione Live.app"`.
4. On first launch, allow microphone access and wait for the components to install.

To build from source: `crea_dmg.command` (creates `LDO_Trascrizione_Live.dmg`), then `installa.command` (copies the app to `~/Applications`).

### Engine comparison

`confronto_motori.py` measures speed and WER of Parakeet and Qwen3-ASR on a 16 kHz file with a reference text. In our tests on a ~3.5-minute file, Parakeet took about 2 s and Qwen about 18 s. Accuracy depends on the audio: test on your own material.

### Notes

- Only transcribe with the consent of the people being recorded.
- Models are downloaded from Hugging Face under their own licenses (Qwen3-ASR: Apache-2.0; Parakeet TDT v3: CC-BY-4.0; Whisper: MIT).
- Not tested on Intel Macs.

### License

MIT, see `LICENSE`.
