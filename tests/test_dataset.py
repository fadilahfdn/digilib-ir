import re
from pathlib import Path

import pandas as pd

from src.preprocessing import preprocess

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "dataset.csv"
RAW_PATH = ROOT / "data" / "raw_openalex.json"

WAJIB_KOLOM = [
    "doc_id", "title", "category", "language",
    "source", "source_id", "retrieved_at", "content",
]
SUBKATEGORI_PRD = {
    "Pemrograman",
    "Basis Data",
    "Jaringan",
    "Kecerdasan Buatan",
    "Rekayasa Perangkat Lunak",
    "Keamanan Siber",
}


def _ekstrak_sinopsis(title, content):
    awal = f"{title}."
    if content.startswith(awal):
        return content[len(awal):].strip()
    return content


def test_berkas_dataset_dan_raw_tersedia():
    assert CSV_PATH.exists(), "data/dataset.csv belum tersedia"
    assert RAW_PATH.exists(), "data/raw_openalex.json belum tersedia"


def test_skema_sebaran_dan_kualitas_dataset():
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    assert len(df) >= 100

    for col in WAJIB_KOLOM:
        assert col in df.columns
        assert (df[col].str.strip() != "").all(), f"Ada nilai kosong pada kolom {col}"

    assert df["doc_id"].is_unique
    assert df["doc_id"].str.match(r"^DOC\d{3,}$").all()

    norm_titles = df["title"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    assert norm_titles.is_unique

    assert set(df["category"]).issubset(SUBKATEGORI_PRD)
    sebaran = df["category"].value_counts()
    for cat in SUBKATEGORI_PRD:
        assert sebaran.get(cat, 0) >= 15, f"Subkategori {cat} kurang dari 15"

    assert set(df["language"]).issubset({"id", "mixed"})

    for _, row in df.iterrows():
        sinopsis = _ekstrak_sinopsis(row["title"], row["content"])
        assert len(sinopsis.split()) >= 30, f"Sinopsis {row['doc_id']} kurang dari 30 kata"


def test_preprocessing_berjalan_pada_seluruh_dataset():
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    for _, row in df.iterrows():
        tokens = preprocess(row["content"])
        assert len(tokens) > 0, f"Token kosong pada {row['doc_id']}"
