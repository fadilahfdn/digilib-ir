def rank(skor, k, judul_token=None, query_token=None):
    urut = sorted(skor.items(), key=lambda x: (-x[1], x[0]))
    return urut[:k] if k else urut