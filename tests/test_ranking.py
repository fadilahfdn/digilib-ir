import pytest

from src.ranking import TOLERANSI, rank


def test_urut_menurun_dan_buang_nol_atau_negatif():
    skor = {"DOC001": 0.0, "DOC002": -0.2, "DOC003": 0.45, "DOC004": 0.85}
    hasil = rank(skor, k=10)
    assert hasil == [("DOC004", 0.85), ("DOC003", 0.45)]
    assert all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], float) for item in hasil)


def test_topk_dan_batas_k():
    skor = {f"DOC{i:03d}": i * 0.1 for i in range(1, 13)}
    top5 = rank(skor, k=5)
    top10 = rank(skor, k=10)
    semua = rank(skor, k=None)
    assert len(top5) == 5
    assert top5[0][0] == "DOC012"
    assert len(top10) == 10
    assert len(semua) == 12

    sedikit = {"DOC001": 0.5, "DOC002": 0.3}
    assert len(rank(sedikit, k=5)) == 2

    with pytest.raises(ValueError):
        rank(skor, k=-1)


def test_tie_breaking_exact_dan_token_judul_unik():
    skor = {"DOC001": 0.75, "DOC002": 0.75, "DOC003": 0.75}
    judul = {
        "DOC001": ["python", "python", "python"],  # duplikat tetap dihitung 1 istilah unik
        "DOC002": ["python", "data", "basis"],
        "DOC003": ["data"],
    }
    query = ["python", "python", "data"]
    hasil = rank(skor, k=5, judul_token=judul, query_token=query)
    assert [d for d, _ in hasil] == ["DOC002", "DOC001", "DOC003"]


def test_tie_breaking_toleransi_dan_batas_pisah():
    # Selisih < 1e-9 dianggap seri sehingga dimenangkan kecocokan judul
    skor_seri = {"DOC001": 0.5 + 5e-10, "DOC002": 0.5}
    judul = {"DOC001": ["umum"], "DOC002": ["python", "algoritma"]}
    hasil_seri = rank(skor_seri, k=5, judul_token=judul, query_token=["python", "algoritma"])
    assert [d for d, _ in hasil_seri] == ["DOC002", "DOC001"]

    # Selisih >= 1e-9 tidak dianggap seri sehingga skor lebih tinggi tetap unggul
    skor_beda = {"DOC001": 0.5 + 2 * TOLERANSI, "DOC002": 0.5}
    hasil_beda = rank(skor_beda, k=5, judul_token=judul, query_token=["python", "algoritma"])
    assert [d for d, _ in hasil_beda] == ["DOC001", "DOC002"]


def test_tie_breaking_doc_id_leksikografis():
    skor = {"DOC010": 0.6, "DOC002": 0.6, "DOC001": 0.6}
    judul = {"DOC010": ["python"], "DOC002": ["python"], "DOC001": ["python"]}
    hasil = rank(skor, k=5, judul_token=judul, query_token=["python"])
    assert [d for d, _ in hasil] == ["DOC001", "DOC002", "DOC010"]


def test_kasus_kosong_dan_parameter_opsional():
    assert rank({}, k=5) == []
    assert rank({"DOC001": 0.0, "DOC002": 0.0}, k=5) == []

    skor = {"DOC003": 0.4, "DOC001": 0.4}
    assert rank(skor, k=5, judul_token=None, query_token=None) == [("DOC001", 0.4), ("DOC003", 0.4)]
    assert rank(skor, k=5, judul_token={"DOC003": ["python"]}, query_token=["python"]) == [
        ("DOC003", 0.4),
        ("DOC001", 0.4),
    ]
