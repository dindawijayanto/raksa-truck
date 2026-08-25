# Offline modelling package

Paket ini adalah kode reproduksi AIC yang sengaja dipisahkan dari FastAPI
runtime di `backend/app/`. Gunakan `requirements.txt` atau `pip install -e .`
di folder ini untuk menjalankan notebook dan skrip benchmark.

Default path setiap skrip sudah diarahkan ke struktur Raksa Truck:

- `backend/data/` untuk input dan fixture sintetis;
- `backend/models/research/` untuk bobot riset;
- `backend/models/` untuk ekspor CatBoost yang dipakai API;
- `reports/modeling/` untuk output eksperimen.

Lihat [`../../docs/modeling/README.md`](../../docs/modeling/README.md) untuk
status model, batas validasi, dan urutan reproduksi.
