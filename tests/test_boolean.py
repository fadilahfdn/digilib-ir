from src.boolean import bangun_indeks, boolean_search
from src.preprocessing import preprocess

TEKS = {
    "D1": "python untuk analisis data",
    "D2": "pemrograman web dengan python",
    "D3": "jaringan komputer dasar",
    "D4": "keamanan data dan jaringan",
    "D5": "pemrograman c++ untuk pemula",
}
INDEKS = bangun_indeks({d: preprocess(t) for d, t in TEKS.items()})
SEMUA = list(TEKS)


def cari(q):
    return boolean_search(q, INDEKS, SEMUA)


def ids(q):
    return cari(q)["doc_ids"]


def test_istilah_tunggal():
    assert ids("python") == ["D1", "D2"]


def test_and_atau_irisan():
    assert ids("python AND data") == ["D1"]


def test_or_atau_gabungan():
    assert ids("python OR jaringan") == ["D1", "D2", "D3", "D4"]


def test_not_komplemen():
    assert ids("NOT python") == ["D3", "D4", "D5"]


def test_and_not():
    assert ids("python AND NOT web") == ["D1"]


def test_not_tanpa_and_sama_dengan_and_not():
    assert ids("python NOT web") == ids("python AND NOT web")


def test_istilah_berurutan_adalah_and():
    assert ids("python data") == ["D1"]


def test_prioritas_and_lebih_tinggi_dari_or():
    # python OR (data AND jaringan) = D1, D2, D4 ; bila salah dibaca kiri ke kanan hasilnya hanya D4
    assert ids("python OR data AND jaringan") == ["D1", "D2", "D4"]


def test_hasil_terurut_menurut_doc_id():
    assert ids("python OR jaringan OR web") == sorted(ids("python OR jaringan OR web"))


def test_istilah_tidak_ada_di_indeks():
    hasil = cari("python AND quantum")
    assert hasil["doc_ids"] == [] and hasil["peringatan"]
    assert ids("python OR quantum") == ["D1", "D2"]
    assert ids("NOT quantum") == SEMUA


def test_stopword_diabaikan_dengan_peringatan():
    hasil = cari("python AND yang")
    assert hasil["doc_ids"] == ["D1", "D2"] and hasil["peringatan"]


def test_operator_huruf_kecil_dianggap_kata_biasa():
    hasil = cari("python and data")
    assert hasil["doc_ids"] == ["D1"] and any("huruf kapital" in p for p in hasil["peringatan"])


def test_istilah_teknis():
    assert ids("C++") == ["D5"]


def test_query_tidak_valid_tidak_membuat_program_berhenti():
    for q in ["", "   ", "AND python", "python AND", "python AND OR data", "python OR", "NOT", "(python)"]:
        hasil = cari(q)
        assert hasil["galat"] and hasil["doc_ids"] == []


def test_query_hanya_stopword():
    hasil = cari("yang dan untuk")
    assert hasil["galat"] and hasil["doc_ids"] == []


def test_bentuk_keluaran_sesuai_kontrak():
    assert set(cari("python")) == {"doc_ids", "peringatan", "galat"}