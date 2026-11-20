# LDO Trascrizione Live

**Italiano** | [English](#english)

App per Mac che trascrive in italiano il parlato di interviste, conferenze, lezioni e riunioni: in locale, senza inviare l'audio a server esterni, e senza Internet dopo il primo avvio.
Finestra Terminale in verde su nero, bozza di sicurezza durante la trascrizione, esportazione finale in `.docx` (Word).

## A cosa serve

- **Giornalismo e televisione**: sbobinare interviste (anche video, con data e ora a ogni capoverso per ritrovare il punto esatto), trascrivere dal vivo un intervento, ricavare citazioni, articoli e didascalie per i social.
- **Conferenze e convegni**: trascrizione dal vivo da microfono o dall'uscita audio del mixer di sala.
- **Scuola e università**: trascrivere lezioni, seminari e interviste per ricerche e tesi, e ripassare dal testo invece che dalla registrazione.
- **Uso in mobilità**: dopo il primo avvio funziona offline, quindi anche in treno o in trasferta.
- **Riservatezza**: l'audio e il testo restano sul Mac. Solo il primo avvio scarica da Internet i modelli.

## Funzioni

- **Tre sorgenti**: microfono del Mac, ingresso audio esterno (mixer sull'ingresso cuffia, con elenco dei dispositivi), file audio o video (MP3, M4A, MP4, MOV).
- **Capoversi con orario**: a ogni pausa di 0,8 s va a capo con una riga vuota e data e ora `GG/MM/AAAA HH:MM:SS`. Per i file l'orario è la data di creazione del file più il tempo di audio.
- **Titolo**: all'avvio chiede il titolo della conferenza o dell'intervista, che finisce nel nome del file Word.
- **Barra spaziatrice** accende/spegne il microfono (parte spento); **Ctrl+C** termina e apre il salvataggio del `.docx`.
- **Bozza di sicurezza** salvata durante la sessione, per non perdere il testo se qualcosa si interrompe.
- Finestra separata con la legenda dei comandi; la finestra principale mostra solo titolo, stato del microfono e testo.
- **Veloce**: un'intervista di circa 3,5 minuti viene trascritta in circa 18 s con Qwen3-ASR, in circa 2 s con Parakeet (misurato su un Mac Apple Silicon).

## Motori di trascrizione

| Motore | Origine | Uso nell'app |
|---|---|---|
| **Qwen3-ASR** 1,7 miliardi di parametri | Alibaba | Primario sui Mac con 16 GB di RAM o più. Nel confronto fatto a mano è il più preciso su nomi propri e sigle |
| **Parakeet TDT v3** 0,6 miliardi di parametri | NVIDIA | Primario sui Mac con meno di 16 GB; molto più veloce e leggero, con qualche errore in più su nomi e sigle |
| **Whisper large-v3-turbo** | OpenAI | Ultima riserva se gli altri non partono |

La scelta è automatica in base alla RAM del Mac, perché Qwen occupa circa 4 GB e su un Mac da 8 GB rallenta il sistema. Si può forzare con `--motore qwen|parakeet|auto` (nell'app, con la variabile d'ambiente `LDO_MOTORE`).

## Requisiti

- Mac con chip Apple Silicon: M1 o successivi (MLX non funziona sui Mac Intel)
- Python 3.11 (`installa_python.command` lo installa se manca)
- circa 7 GB liberi e una connessione Internet per il primo avvio (librerie e modelli)
- consigliati 16 GB di RAM; con 8 GB funziona con Parakeet

## Installazione

1. Scarica `LDO_Trascrizione_Live.dmg` dalla sezione *Releases*, oppure costruiscilo con `crea_dmg.command`.
2. Esegui `installa_python.command` se Python 3.11 non c'è.
3. Apri il DMG e trascina l'app in Applicazioni. Se macOS la blocca: tasto destro > Apri, oppure
   `xattr -cr "/Applications/LDO Trascrizione Live.app"`.
4. Al primo avvio consenti il microfono e attendi l'installazione dei componenti.

Per costruire dal sorgente: `crea_dmg.command` (crea `LDO_Trascrizione_Live.dmg`), poi `installa.command` (copia l'app in `~/Applications`).

## Limiti

- **Non distingue chi parla**: il testo non indica quale persona ha detto cosa. Per le interviste, aggiungi i nomi a mano o usa gli orari per ritrovare il punto nel video.
- Solo italiano.
- La precisione dipende dalla qualità dell'audio: parlato sovrapposto, rumore e voci lontane dal microfono peggiorano il risultato. Rileggi sempre il testo prima di pubblicarlo o citarlo.
- Non testato su Mac Intel e su Windows (il motore MLX funziona solo su Apple Silicon).

## Confronto tra motori

`confronto_motori.py` misura tempi e WER di Parakeet e Qwen3-ASR su un file a 16 kHz con un testo di riferimento. I numeri dipendono dal materiale e da come si costruisce il riferimento: verifica sul tuo audio.

## Note

- Trascrivi solo con il consenso delle persone registrate.
- Il programma scarica i modelli da Hugging Face, ognuno con la propria licenza (Qwen3-ASR: Apache-2.0; Parakeet TDT v3: CC-BY-4.0; Whisper: MIT).

## Licenza

MIT, vedi `LICENSE`.

---

## English

**LDO Trascrizione Live** is a Mac app that transcribes spoken Italian from interviews, conferences, lectures and meetings locally: audio is not sent to external servers, and no Internet connection is needed after the first launch. It runs in a green-on-black Terminal window, writes a safety draft while transcribing, and exports a Word `.docx` file at the end.

### What it is for

- **Journalism and TV**: transcribe interviews (including video, with date and time on every paragraph so you can find the exact spot), transcribe a speech live, pull quotes, articles and social captions.
- **Conferences**: live transcription from the microphone or from the venue mixer's audio output.
- **School and university**: transcribe lectures, seminars and research interviews, and study from the text instead of the recording.
- **On the move**: after the first launch it works offline, e.g. on a train or on assignment.
- **Privacy**: audio and text stay on the Mac. Only the first launch downloads the models from the Internet.

### Features

- **Three sources**: Mac microphone, external audio input (a mixer plugged into the headphone jack, with a device list), or an audio/video file (MP3, M4A, MP4, MOV).
- **Timestamped paragraphs**: after each 0.8 s pause it starts a new paragraph, separated by a blank line, with date and time `DD/MM/YYYY HH:MM:SS`. For files, the time is the file's creation date plus the elapsed audio time.
- **Title**: it asks for the conference or interview title at start, which goes into the Word file name.
- **Spacebar** turns the microphone on and off (it starts off); **Ctrl+C** ends the session and opens the save dialog for the `.docx`.
- **Safety draft** saved during the session, so text is not lost if something breaks.
- A separate window shows the command legend; the main window shows only the title, microphone state and text.
- **Fast**: a ~3.5-minute interview takes about 18 s with Qwen3-ASR and about 2 s with Parakeet (measured on an Apple Silicon Mac).

### Engines

| Engine | Origin | Role in the app |
|---|---|---|
| **Qwen3-ASR** 1.7B parameters | Alibaba | Primary on Macs with 16 GB of RAM or more. In our manual comparison it was the most accurate on proper names and acronyms |
| **Parakeet TDT v3** 0.6B parameters | NVIDIA | Primary on Macs with less than 16 GB; much faster and lighter, with a few more errors on names and acronyms |
| **Whisper large-v3-turbo** | OpenAI | Last-resort fallback if the others fail to start |

The choice is automatic based on the Mac's RAM, because Qwen takes about 4 GB and slows down an 8 GB Mac. You can force it with `--motore qwen|parakeet|auto` (in the app, with the `LDO_MOTORE` environment variable).

### Requirements

- Mac with Apple Silicon: M1 or later (MLX does not run on Intel Macs)
- Python 3.11 (`installa_python.command` installs it if missing)
- About 7 GB of free space and an Internet connection on first launch (libraries and models)
- 16 GB of RAM recommended; with 8 GB it runs with Parakeet

### Installation

1. Download `LDO_Trascrizione_Live.dmg` from *Releases*, or build it with `crea_dmg.command`.
2. Run `installa_python.command` if Python 3.11 is missing.
3. Open the DMG and drag the app to Applications. If macOS blocks it: right-click > Open, or run
   `xattr -cr "/Applications/LDO Trascrizione Live.app"`.
4. On first launch, allow microphone access and wait for the components to install.

To build from source: `crea_dmg.command` (creates `LDO_Trascrizione_Live.dmg`), then `installa.command` (copies the app to `~/Applications`).

### Limitations

- **It does not tell speakers apart**: the text does not say who said what. For interviews, add the names by hand or use the timestamps to find the spot in the video.
- Italian only.
- Accuracy depends on audio quality: overlapping speech, noise and voices far from the microphone make results worse. Always proofread before publishing or quoting.
- Not tested on Intel Macs or Windows (the MLX engine runs only on Apple Silicon).

### Engine comparison

`confronto_motori.py` measures speed and WER of Parakeet and Qwen3-ASR on a 16 kHz file with a reference text. Numbers depend on the material and on how the reference is built: test on your own audio.

### Notes

- Only transcribe with the consent of the people being recorded.
- Models are downloaded from Hugging Face under their own licenses (Qwen3-ASR: Apache-2.0; Parakeet TDT v3: CC-BY-4.0; Whisper: MIT).

### License

MIT, see `LICENSE`.
