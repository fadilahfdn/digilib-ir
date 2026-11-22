import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw_openalex.json"
CSV_PATH = ROOT / "data" / "dataset.csv"
OPENALEX_URL = "https://api.openalex.org/works"
SELECT_FIELDS = (
    "id,title,publication_year,authorships,doi,"
    "primary_location,abstract_inverted_index,language"
)

QUERIES_PER_CATEGORY = {
    "Pemrograman": [
        "pemrograman python",
        "algoritma pemrograman",
        "pemrograman web java",
    ],
    "Basis Data": [
        "basis data",
        "sistem basis data sql",
        "perancangan basis data mysql",
        "database nosql dbms",
    ],
    "Jaringan": [
        "jaringan komputer",
        "jaringan komputer tcp ip",
        "administrasi jaringan komputer",
    ],
    "Kecerdasan Buatan": [
        "machine learning deep learning",
        "data mining sistem pakar",
        "jaringan saraf tiruan fuzzy",
        "kecerdasan buatan",
    ],
    "Rekayasa Perangkat Lunak": [
        "rekayasa perangkat lunak",
        "software engineering perangkat lunak",
        "pengujian perangkat lunak uml",
        "pengembangan perangkat lunak analisis sistem",
    ],
    "Keamanan Siber": [
        "keamanan siber",
        "kriptografi",
        "keamanan sistem informasi",
        "keamanan komputer jaringan audit it",
    ],
}

# Kata kunci yang wajib muncul pada judul agar buku benar-benar sesuai subkategori.
TITLE_REQUIRED_KEYWORDS = {
    "Pemrograman": (
        "pemrograman", "algoritma", "algoritme", "python", "java", "c++", "c#",
        "php", "javascript", "delphi", "pascal", "golang", "kotlin", "flutter",
        "struktur data",
    ),
    "Basis Data": (
        "basis data", "database", "sql", "mysql", "postgresql", "nosql",
        "mongodb", "dbms", "smbd", "oracle", "sqlite",
    ),
    "Jaringan": (
        "jaringan komputer", "jaringan dan komunikasi data", "administrator jaringan",
        "pengelolaan jaringan", "manajemen jaringan", "tcp/ip", "mikrotik", "cisco",
        "komunikasi data", "protokol jaringan", "server dan jaringan",
    ),
    "Kecerdasan Buatan": (
        "kecerdasan buatan", "artificial intelligence", "machine learning",
        "deep learning", "pembelajaran mesin", "neural network", "jaringan saraf",
        "soft computing", "data mining", "sistem pakar", "fuzzy", "algoritma genetika",
        "computer vision", "visi komputer", "natural language", "generative ai",
    ),
    "Rekayasa Perangkat Lunak": (
        "rekayasa perangkat lunak", "software engineering", "perangkat lunak",
        "blackbox testing", "whitebox testing", "pengujian perangkat", "uml",
        "analisis dan perancangan sistem", "analisis & perancangan sistem",
        "analisa & perancangan sistem", "software development", "agile", "scrum",
        "manajemen proyek perangkat", "pemodelan sistem informasi",
    ),
    "Keamanan Siber": (
        "keamanan siber", "cyber security", "cybersecurity", "keamanan informasi",
        "keamanan komputer", "keamanan jaringan", "kriptografi", "enkripsi",
        "malware", "forensik digital", "digital forensics", "cyber threat",
        "cybercrime", "security analytics", "keamanan sistem", "keamanan data",
        "penetration testing", "keamanan aplikasi", "keamanan teknologi informasi",
        "audit it", "audit dan kontrol teknologi informasi", "oauth",
        "watermarking untuk mendukung keamanan", "blockchain dan ethereum",
        "pemeliharaan dan keamanan",
    ),
}

# Judul yang mengandung istilah lintas-disiplin atau laporan non-buku disaring keluar.
OFF_DOMAIN_TITLE_TERMS = (
    "ginjal", "kesehatan", "keperawatan", "kedokteran", "kebidanan", "farmasi",
    "pertanian", "peternakan", "perikanan", "hukum", "syariah", "pancasila",
    "teologi", "ilahi", "agama", "pemerintahan", "pelayanan publik", "kerjasama",
    "perang asimetris", "maritim", "pelayaran", "pendidikan", "pembelajaran bagi siswa",
    "sekolah menengah", "laporan individu", "laporan praktik", "ppl ", "smk ",
    "sel darah", "stunting", "kanker", "psikologi", "akuntansi", "perpajakan",
    "pariwisata", "geografi", "media siber", "the future human", "etika publik",
    "etika profesi", "smart farming", "birokrasi", "perguruan tinggi",
    "peserta didik", "hiperaktif", "sejarah", "rekrutmen", "sdm",
    "energi indonesia", "otomatisasi layanan",
)

PREFACE_MARKERS = (
    "alhamdulillah", "puji syukur", "shalawat", "kata pengantar", "assalamu",
)

ID_FUNCTION_WORDS = {
    "yang", "dan", "ini", "untuk", "dengan", "pada", "dalam", "dari",
    "buku", "adalah", "merupakan", "sebagai", "dapat", "membahas",
    "serta", "atau", "juga", "tentang", "secara", "oleh",
}

EN_STOPWORDS = {
    "the", "this", "book", "with", "from", "that", "which", "their",
    "have", "are", "was", "were", "these", "those", "into", "between",
}

MIXED_TECH_TERMS = {
    "python", "java", "sql", "mysql", "nosql", "database", "software",
    "engineering", "machine", "learning", "deep", "artificial", "intelligence",
    "network", "cyber", "security", "malware", "framework", "tcp/ip", "web",
    "html", "css", "javascript", "php", "cloud", "uml", "testing", "agile",
    "scrum", "blockchain", "firewall", "iot", "api", "neural", "linux",
    "android", "c++", "c#", "node.js", "dbms", "routing", "server", "client",
    "windows", "docker", "git", "laravel", "react", "flutter", "kotlin",
    "golang", "cybersecurity", "encryption", "cryptography", "forensics",
}

CSV_FIELDS = [
    "doc_id", "title", "author", "year", "category", "language",
    "source", "source_id", "source_url", "retrieved_at", "content",
]


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    words = {}
    for token, positions in inverted_index.items():
        for pos in positions:
            words[pos] = token
    raw = " ".join(words[i] for i in sorted(words))
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_title(title):
    return re.sub(r"\s+", " ", title.lower()).strip()


def is_indonesian(text):
    tokens = re.findall(r"[a-z]+", text.lower())
    id_count = sum(1 for t in tokens if t in ID_FUNCTION_WORDS)
    en_count = sum(1 for t in tokens if t in EN_STOPWORDS)
    return id_count >= 4 and id_count > en_count


def is_relevant_cs(title, synopsis, category):
    title_low = title.lower()
    if any(bad in title_low for bad in OFF_DOMAIN_TITLE_TERMS):
        return False
    if category == "Jaringan" and ("keamanan" in title_low or "saraf" in title_low):
        return False
    if category == "Basis Data" and "pemrograman" in title_low and "basis data" not in title_low and "database" not in title_low:
        return False
    return any(kw in title_low for kw in TITLE_REQUIRED_KEYWORDS[category])


def detect_language(synopsis):
    # Preserve symbols like +, #, / so c++, c#, tcp/ip are detected accurately.
    words = set(re.findall(r"[a-z0-9+#./-]+", synopsis.lower()))
    stripped = {w.strip(".,;:!?()[]{}\"'") for w in words}
    return "mixed" if len(stripped & MIXED_TECH_TERMS) >= 2 else "id"


def format_authors(authorships):
    names = []
    for entry in authorships or []:
        name = ((entry or {}).get("author") or {}).get("display_name") or ""
        name = re.sub(r"\s+", " ", name).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def fetch_raw_payloads():
    retrieved_at = dt.date.today().isoformat()
    payloads = []
    for category, queries in QUERIES_PER_CATEGORY.items():
        for query in queries:
            resp = requests.get(
                OPENALEX_URL,
                params={
                    "search": query,
                    "filter": "type:book,language:id,has_abstract:true",
                    "per-page": 50,
                    "select": SELECT_FIELDS,
                },
                timeout=30,
                headers={"User-Agent": "DigiLib-IR/1.0"},
            )
            resp.raise_for_status()
            payloads.append({
                "category": category,
                "query": query,
                "retrieved_at": retrieved_at,
                "results": resp.json().get("results", []),
            })
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps(payloads, ensure_ascii=False, indent=2), encoding="utf-8")
    return payloads


def build_dataset(payloads, per_category=20):
    seen_ids = set()
    seen_titles = set()
    selected = []
    counts = {cat: 0 for cat in QUERIES_PER_CATEGORY}

    # Prioritaskan batch query spesifik ML/DL sebelum query umum kecerdasan buatan.
    ordered_payloads = sorted(
        payloads,
        key=lambda b: (b["category"] == "Kecerdasan Buatan" and b["query"] == "kecerdasan buatan"),
    )

    for batch in ordered_payloads:
        category = batch["category"]
        retrieved_at = batch["retrieved_at"]
        if counts[category] >= per_category:
            continue
        for work in batch.get("results", []):
            if counts[category] >= per_category:
                break
            work_url = work.get("id") or ""
            source_id = work_url.rsplit("/", 1)[-1]
            title = re.sub(r"\s+", " ", (work.get("title") or "")).strip()
            synopsis = reconstruct_abstract(work.get("abstract_inverted_index"))
            if not source_id or not title or not synopsis:
                continue
            if source_id in seen_ids:
                continue
            norm_title = normalize_title(title)
            if norm_title in seen_titles:
                continue
            if len(synopsis.split()) < 30:
                continue
            head_low = synopsis[:160].lower()
            if any(marker in head_low for marker in PREFACE_MARKERS):
                continue
            if not is_indonesian(synopsis):
                continue
            if not is_relevant_cs(title, synopsis, category):
                continue

            seen_ids.add(source_id)
            seen_titles.add(norm_title)
            counts[category] += 1

            loc = work.get("primary_location") or {}
            source_url = loc.get("landing_page_url") or work.get("doi") or work_url
            year = work.get("publication_year")
            selected.append({
                "title": title,
                "author": format_authors(work.get("authorships")),
                "year": "" if year is None else str(year),
                "category": category,
                "language": detect_language(synopsis),
                "source": "openalex_api",
                "source_id": source_id,
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "content": f"{title}. {synopsis}",
                "_synopsis_words": len(synopsis.split()),
            })

    rows = []
    for idx, item in enumerate(selected, start=1):
        row = {"doc_id": f"DOC{idx:03d}"}
        for key in CSV_FIELDS[1:]:
            row[key] = item[key]
        rows.append(row)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return rows, counts, selected


def main():
    parser = argparse.ArgumentParser(description="Build offline DigiLib-IR dataset from OpenAlex.")
    parser.add_argument("--from-raw", action="store_true", help="Rebuild CSV from cached raw_openalex.json")
    parser.add_argument("--per-category", type=int, default=20)
    args = parser.parse_args()

    if args.from_raw:
        payloads = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    else:
        payloads = fetch_raw_payloads()

    rows, counts, selected = build_dataset(payloads, per_category=args.per_category)
    print(f"Total dokumen: {len(rows)}")
    for cat, cnt in counts.items():
        print(f"  {cat}: {cnt}")
    word_counts = [item["_synopsis_words"] for item in selected]
    lang_counts = {
        "id": sum(1 for r in rows if r["language"] == "id"),
        "mixed": sum(1 for r in rows if r["language"] == "mixed"),
    }
    print(f"Sinopsis kata min/max: {min(word_counts)} / {max(word_counts)}")
    print(f"Bahasa: {lang_counts}")


if __name__ == "__main__":
    main()
