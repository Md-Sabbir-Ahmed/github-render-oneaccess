"""Voice every line of build/script.json with ElevenLabs (with timestamps) → assets/voice/<id>.mp3 + build/cues.json.

usage:  set ELEVENLABS_API_KEY=sk_...   then   python -I -X utf8 build/tts.py [--force]
Lines whose text has not changed (hash in cues.json) are skipped, so a rerun only voices new or edited lines.
Numbers are written in words in `vo` (Bangla TTS reads digits badly); digits stay on screen in `cap`.
"""
import base64
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
API = "https://api.elevenlabs.io"


def tts(key, text, voice, model, lang, prev, nxt):
    body = {"text": text, "model_id": model, "language_code": lang, "seed": 2026,
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}}
    if prev:
        body["previous_text"] = prev
    if nxt:
        body["next_text"] = nxt
    req = urllib.request.Request(f"{API}/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    al = d.get("alignment") or d.get("normalized_alignment")
    return base64.b64decode(d["audio_base64"]), al


def main():
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        sys.exit("set ELEVENLABS_API_KEY first")
    force = "--force" in sys.argv
    sc = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
    cues_p = HERE / "cues.json"
    cues = json.loads(cues_p.read_text(encoding="utf-8")) if cues_p.exists() else {}
    lines = sc["lines"]
    (ROOT / "assets/voice").mkdir(parents=True, exist_ok=True)
    for i, ln in enumerate(lines):
        h = hashlib.sha1(ln["vo"].encode()).hexdigest()[:8]
        out = ROOT / "assets/voice" / f"{ln['id']}.mp3"
        if not force and out.exists() and cues.get(ln["id"], {}).get("hash") == h:
            print(ln["id"], "kept", cues[ln["id"]]["duration"])
            continue
        prev = lines[i - 1]["vo"] if i else None
        nxt = lines[i + 1]["vo"] if i + 1 < len(lines) else None
        audio, al = tts(key, ln["vo"], sc["voice_id"], sc["model"], sc["lang"], prev, nxt)
        out.write_bytes(audio)
        ends = al["character_end_times_seconds"]
        starts = al["character_start_times_seconds"]
        # first/last spoken (non-space) character → trims leading/trailing silence from the timing
        chars = al["characters"]
        spoken = [k for k, c in enumerate(chars) if c.strip()]
        dur = ends[spoken[-1]] if spoken else ends[-1]
        first = starts[spoken[0]] if spoken else 0.0
        cues[ln["id"]] = {"file": f"assets/voice/{ln['id']}.mp3", "duration": round(dur, 3), "speech_start": round(first, 3), "hash": h}
        cues_p.write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
        print(ln["id"], "voiced", round(dur, 2), "s")
    total = sum(c["duration"] for c in cues.values())
    print(f"{len(cues)} clips, speech total {total:.1f} s")


if __name__ == "__main__":
    main()
