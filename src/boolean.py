from src.preprocessing import preprocess

OPERATOR = {"AND", "OR", "NOT"}


class QueryTidakValid(Exception):
    pass


def bangun_indeks(dokumen_token):
    # {doc_id: [token]} -> {istilah: [doc_id terurut]}
    indeks = {}
    for doc_id, tokens in dokumen_token.items():
        for t in set(tokens):
            indeks.setdefault(t, []).append(doc_id)
    return {t: sorted(ids) for t, ids in indeks.items()}


def _dan(a, b):
    # None berarti "istilah diabaikan": tidak ikut menyaring
    if a is None:
        return b
    if b is None:
        return a
    return a & b


def _atau(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return a | b


class _Pengurai:
    def __init__(self, bagian, indeks, semua_id, config):
        self.bagian, self.i = bagian, 0
        self.indeks, self.semua, self.config = indeks, set(semua_id), config
        self.peringatan = []

    def _lihat(self):
        return self.bagian[self.i] if self.i < len(self.bagian) else None

    def _istilah(self, mentah):
        if mentah.lower() in ("and", "or", "not"):
            self.peringatan.append(f"'{mentah}' dianggap kata biasa. Tulis operator dengan huruf kapital: AND, OR, NOT.")
            return None
        token = preprocess(mentah, self.config)
        if not token:
            self.peringatan.append(f"Istilah '{mentah}' diabaikan karena dibuang preprocessing (misalnya stopword).")
            return None
        hasil = None
        for t in token:
            if t not in self.indeks:
                self.peringatan.append(f"Istilah '{t}' tidak ditemukan di indeks.")
            ids = set(self.indeks.get(t, ()))
            hasil = ids if hasil is None else hasil & ids     # istilah jadi beberapa token: digabung AND
        return hasil

    # tata bahasa: ekspresi := dan (OR dan)* ; dan := tidak ((AND | kosong) tidak)* ; tidak := NOT tidak | istilah
    def ekspresi(self):
        kiri = self.dan()
        while self._lihat() == "OR":
            self.i += 1
            kiri = _atau(kiri, self.dan())
        return kiri

    def dan(self):
        kiri = self.tidak()
        while True:
            x = self._lihat()
            if x is None or x == "OR":
                break
            if x == "AND":
                self.i += 1            # selain itu: istilah atau NOT berurutan = AND implisit
            kiri = _dan(kiri, self.tidak())
        return kiri

    def tidak(self):
        x = self._lihat()
        if x is None:
            raise QueryTidakValid("Query berakhir dengan operator yang tidak punya operand.")
        if x in ("AND", "OR"):
            raise QueryTidakValid(f"Operator {x} harus berada di antara dua istilah.")
        self.i += 1
        if x == "NOT":
            nilai = self.tidak()
            return None if nilai is None else self.semua - nilai
        return self._istilah(x)


def boolean_search(query, indeks, semua_id, config=None):
    hasil = {"doc_ids": [], "peringatan": [], "galat": None}
    if not query or not query.strip():
        hasil["galat"] = "Query kosong."
        return hasil
    if "(" in query or ")" in query:
        hasil["galat"] = "Tanda kurung belum didukung."
        return hasil
    # operator dikenali dari teks mentah, SEBELUM preprocessing
    pengurai = _Pengurai(query.split(), indeks, semua_id, config)
    try:
        himpunan = pengurai.ekspresi()
    except QueryTidakValid as e:
        hasil["galat"] = str(e)
        return hasil
    hasil["peringatan"] = list(dict.fromkeys(pengurai.peringatan))
    if himpunan is None:
        hasil["galat"] = "Semua istilah query dibuang preprocessing, sehingga tidak ada yang dicari."
        return hasil
    hasil["doc_ids"] = sorted(himpunan)
    return hasil