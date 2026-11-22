from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


def test_halaman_dataset():
    at = AppTest.from_file(str(ROOT / "halaman" / "dataset.py"), default_timeout=15)
    at.run()
    assert not at.exception
    assert not at.error
    assert len(at.metric) == 4
    total = int(at.metric[0].value)
    assert total >= 100

    # Ganti dokumen terpilih untuk memastikan pemrosesan ulang berjalan tanpa galat
    opsi = at.selectbox[0].options
    assert len(opsi) == total
    at.selectbox[0].set_value(opsi[1]).run()
    assert not at.exception


def test_halaman_inspeksi_ketik_dan_dataset():
    at = AppTest.from_file(str(ROOT / "halaman" / "inspeksi.py"), default_timeout=15)
    at.run()
    assert not at.exception
    assert len(at.info) >= 1

    # Muat contoh kalimat teknis
    at.button[0].click().run()
    assert not at.exception
    assert len(at.dataframe) == 1
    assert len(at.dataframe[0].value) == 7
    assert "cplusplus" in at.code[0].value
    assert "tcpip" in at.code[0].value

    # Matikan normalisasi istilah teknis
    at.checkbox[0].set_value(False).run()
    assert not at.exception
    assert "cplusplus" not in at.code[0].value

    # Uji mode pilih dokumen dari dataset
    at.radio[0].set_value("Pilih dokumen dari dataset").run()
    assert not at.exception
    assert not at.error
    assert len(at.dataframe) == 1


def test_halaman_evaluasi_kosong_dan_pratinjau():
    at = AppTest.from_file(str(ROOT / "halaman" / "evaluasi.py"), default_timeout=15)
    at.run()
    assert not at.exception
    assert not at.error
    assert len(at.info) >= 1

    # Aktifkan pratinjau placeholder jika results.json belum ada
    if at.checkbox:
        at.checkbox[0].set_value(True).run()
        assert not at.exception
        assert len(at.warning) >= 1
        assert len(at.metric) == 4
