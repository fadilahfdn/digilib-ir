import json
import re
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

FOLDER_RESOURCES = Path(__file__).resolve().parent.parent / "resources"
KONFIG_DEFAULT = {"normalisasi_istilah": True, "stopword": True, "stemming": True}


def _baca_stopword():
    kata = set()
    for nama in ("stopwords_id.txt", "stopwords_en.txt"):
        berkas = FOLDER_RESOURCES / nama
        if berkas.exists():
            kata |= {b.strip() for b in berkas.read_text(encoding="utf-8").splitlines() if b.strip()}
    return kata


def _baca_istilah_teknis():
    berkas = FOLDER_RESOURCES / "technical_terms.json"
    if not berkas.exists():
        return {}
    return json.loads(berkas.read_text(encoding="utf-8"))


STOPWORD = _baca_stopword()
ISTILAH = _baca_istilah_teknis()
TERLINDUNGI = set(ISTILAH.values()) # token yang tidak boleh dibuang atau di-stem
_STEMMER = StemmerFactory().create_stemmer()


@lru_cache(maxsize=None)
def _stem(kata):
    return _STEMMER.stem(kata)


def _normalisasi_istilah(teks):
    # Ganti istilah teknis (c++, tcp/ip, ...) dengan token aman, yang terpanjang lebih dulu
    for asli in sorted(ISTILAH, key=len, reverse=True):
        pola = r"(?<![a-z0-9])" + re.escape(asli) + r"(?![a-z0-9])"
        teks = re.sub(pola, " " + ISTILAH[asli] + " ", teks)
    return teks


def preprocess_steps(text, config=None):
    config = {**KONFIG_DEFAULT, **(config or {})}

    # case folding
    teks = text.lower()

    # normalisasi istilah teknis
    if config["normalisasi_istilah"]:
        teks = _normalisasi_istilah(teks)
    setelah_normalisasi = teks

    # sanitasi: semua selain huruf dan angka menjadi spasi (tanda hubung ikut)
    teks = re.sub(r"[^a-z0-9]+", " ", teks).strip()

    # tokenisasi: pisah spasi, buang angka murni dan token satu huruf
    token = [t for t in teks.split()
             if t in TERLINDUNGI or (len(t) > 1 and not t.isdigit())]

    # stopword removal (token terlindungi tidak pernah dibuang)
    if config["stopword"]:
        tanpa_stop = [t for t in token if t in TERLINDUNGI or t not in STOPWORD]
    else:
        tanpa_stop = list(token)

    # stemming (token terlindungi tidak di-stem)
    if config["stemming"]:
        stem = [t if t in TERLINDUNGI else _stem(t) for t in tanpa_stop]
    else:
        stem = list(tanpa_stop)

    return OrderedDict([
        ("teks_asli", text),
        ("case_folding", text.lower()),
        ("normalisasi_istilah", setelah_normalisasi.strip()),
        ("sanitasi", teks),
        ("token", token),
        ("stopword_dibuang", tanpa_stop),
        ("stem", stem),
    ])


def preprocess(text, config=None):
    return preprocess_steps(text, config)["stem"]