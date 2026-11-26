# The Vault Job: desain math

Status: disimulasikan 2026-11-25 (lihat "Terukur"). Belum dilihat pengguna, belum diunggah ke
Studio. Semua pilihan di bawah adalah pilihan lead selama pengguna tidur (aturan roadmap: keputusan
yang terlambat diambil lead dan dicatat).

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`.

## Ide dalam angka

Video slot lines 5×4, 20 line, keluarga dengan turnover terbesar di Engine. Yang khas adalah
**Crew Wilds**: empat wild, satu peran masing-masing.

- **Driver** ×2. Di The Job ia lengket dan menyetir satu reel ke kiri tiap spin sampai keluar papan.
- **Safecracker** ×2 di base. Di The Job ia lengket, mulai ×1, dan naik satu anak tangga tiap kali
  ikut menang: 1 → 2 → 3 → 5 → 8 → 12 → 20 → 30 → 50 → 80 → 120 → 200 → 300 → 500 → 1.000.
- **Muscle** melebar menutup reelnya.
- **Hacker** menyalin multiplier tertinggi di papan (minimal ×2).

Multiplier kru di satu line **dijumlahkan**, lalu dikalikan ke menang line itu. The Job (free
spins) selalu dimulai dengan satu Safecracker di reel 2, jadi setiap sesi punya inti mekaniknya.
Menang besar datang dari Safecracker yang sudah tinggi di reel 2, Hacker yang menyalinnya di
spin yang sama, dan retrigger.

Kelas volatilitas: tinggi, profil petaruh besar, dijaga di bawah batas std dev Engine (60).
Pembanding (dari `reports/Ide 4 game baru 2026-11-16.md`, data Engine 16 Nov 2026): Lazy Vampire
(wild penutup reel sampai 1000×, std dev 36,5), Private Jet (wild bermultiplier dijumlahkan per
line, 38,9), Waylanders Forge (91,8).

## Aturan yang menggerakkan math

- Papan 5×4, 20 line tetap, kiri ke kanan, 3/4/5 sejenis.
- 8 simbol bayar, 4 kru (reel 2–5 saja), scatter (semua reel).
- Paytable per line: H1 1,5 / 6 / 25 sampai L4 0,1 / 0,3 / 1,2 (semua kelipatan 0,1).
- Line kru saja dibayar seperti H1.
- 3/4/5 scatter → 10/12/15 free spin; tiap scatter di The Job menambah 1 spin.
- Reel base: 2 scatter per reel, 1 kru tiap jenis per reel 2–5, 108 stop. Reel The Job: 1 scatter
  dan 1 kru tiap jenis per reel, 209 stop (kru setengah sepadat base, karena kru lengket menumpuk).
- Batas menang 20.000× di semua mode.

## Target dan terukur

Diukur dari lookup table terbitan, 2026-11-25. Sampel: 300.000 ronde (base, ante) dan 100.000 per
mode beli, ditambah sampel ekor. 37 dari 37 target di `math_targets.json` terpenuhi.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine; mayoritas game teratas | 96,698% di kelima mode |
| Hit rate base | 36–42% | Angka reel tanpa paksaan: 39,7% | 40,0% |
| The Job muncul | 1 dari 265–320 | Angka reel tanpa paksaan: 1 dari 276,8 | 1 dari 277,0 |
| Rata-rata menang The Job | 125–160× | Campuran 3/4/5 scatter | 131,4× |
| RTP base / The Job | 44–52% / 46–55% porsi | Lines volatil: fitur membawa sekitar separuh | 49,3% / 47,4% (porsi 49,0%) |
| Std dev base | 25–58 | Volatil tinggi, di bawah batas Engine 60 | 27,4 |
| Max win dan peluangnya | 20.000×, 1 dari 1–10 juta | Pedoman Engine: lebih sering dari 1 dari 10 juta | 20.000×, 1 dari 6.324.971 |
| Menang di bawah taruhan (dari semua hit) | ≤ 75%, dilaporkan | Tidak ada batas resmi | 70,9% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,473 |
| Beli bonus: balik modal / median / di bawah 10% harga | ≥ 18% / ≥ 0,25× / ≤ 26% | Sesi tanpa paksaan | 19,8% / 0,27× / 25,2% |
| Beli inside: sama | ≥ 20% / ≥ 0,33× / ≤ 15% | sama | 21,9% / 0,36× / 14,1% |
| Beli heist: sama | ≥ 21% / ≥ 0,38× / ≤ 9% | sama | 23,5% / 0,42× / 8,3% |

Frekuensi The Job adalah satu-satunya angka yang diselesaikan agar RTP tepat; ia jatuh tepat di
angka reel (1 dari 277,0 lawan 1 dari 276,8 pada 10 juta spin), jadi base tidak diberi bobot apa pun
di luar frekuensi alaminya.

## Anggaran

Semua dalam kelipatan taruhan dasar.

- Spin base yang tidak memicu The Job: menang 1 dari 2,52 spin, rata-rata 1,24× → 0,493.
- The Job: 131,4× ÷ 277,0 → 0,474. Jumlah: 0,493 + 0,474 = 0,967.
- Max win di dalam porsi The Job: 20.000 ÷ 6.324.971 = 0,0032.
- Pemicu alami: 96,2% tiga scatter, 3,8% empat, 0,05% lima (10 juta spin, 36.124 pemicu). Sesi 4
  dan 5 scatter jauh lebih kuat (sekitar 330× dan 1.170× rata-rata) karena 12 dan 15 spin.
- Bonus: sesi tiga scatter 125,6× ÷ 0,967 = 129,9× → harga 130× (koreksi bobot ±0).
- Inside: 275,3× ÷ 0,967 = 284,7× → harga 290× (θ = +0,018 pada rata-rata).
- Heist (dua Safecracker tambahan ×3): sesi tanpa paksaan 567,9× ÷ 0,967 = 587,3× → harga 600× (+2,1% pada rata-rata).
- Ante 2×: 2 × 0,967 = 1,934 = bagian base + The Job 131,4× sebanyak 1 dari 91,0 (3,0× lebih sering).

## Mode

| Mode | Harga | Yang berubah bagi pemain | RTP | Balik modal | Median | Di bawah 10% harga | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | 96,698% | 11,7% | 0 | — | 1 dari 6.324.971 |
| ante | 2× | The Job sekitar 3× lebih sering (1 dari 91) | 96,698% | 6,9% | 0 | — | 1 dari 2.077.493 |
| bonus | 130× | Langsung The Job, 10 spin, satu Safecracker | 96,698% | 19,8% | 0,27× harga | 25,2% | 1 dari 43.824 |
| inside | 290× | The Job dengan Safecracker kedua ×2 | 96,698% | 21,9% | 0,36× harga | 14,1% | 1 dari 10.417 |
| heist | 600× | The Job dengan dua Safecracker tambahan ×3 | 96,698% | 23,5% | 0,42× harga | 8,3% | 1 dari 2.218 |

Buku mode ante sama dengan buku mode base; yang berbeda hanya bobotnya.

## Di mana varians tinggal

Di tangga Safecracker. Safecracker awal duduk di reel 2, jadi ia ikut di hampir semua menang line
yang melewati selnya; rata-rata sesi bonus menaikkannya 8,4 kali. Tangga 1 → 2 → 3 → 5 → 8 → …
tumbuh pelan di awal (pembelian yang lebih tenang daripada penggandaan murni) dan cepat di atas
50. Multiplier kru di satu line dijumlahkan, jadi Hacker yang menyalin Safecracker tinggi di spin
yang sama menggandakan line itu.

Diukur dari sesi tanpa paksaan (`run.py --feature`, 400.000 sesi bonus): Safecracker tertinggi di
akhir sesi: ×12 13,1%, ×20 14,4%, ×30 14,9%, ×50 13,7%, ×80 10,5%, ×120 6,6%, ×200 2,9%, ×300 1,0%,
×500 0,3%, ×1.000 0,1%. Safecracker baru yang mendarat per sesi 0,76, Driver 0,76.

Ekor distribusi mode base, tanpa celah (peluang turun terus dari pita ke pita):

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 8.811 | 8,2% |
| 1.000–2.000× | 1 dari 19.854 | 7,0% |
| 2.000–5.000× | 1 dari 49.766 | 6,0% |
| 5.000–10.000× | 1 dari 299.829 | 2,3% |
| 10.000–20.000× | 1 dari 1.045.861 | 1,4% |
| di antaranya tepat 20.000× | 1 dari 6.324.971 | 0,3% |

Rentang 10.000–20.000× lebih sering daripada max win di semua mode (base: setengah max win sampai
max win 1 dari 1.253.060). Tidak ada ronde yang dipaksa ke max win; buku ekor berasal dari sampel
`freegame_tail` (menang ≥ 2.000× di base dan bonus, ≥ 5.000× di inside, ≥ 8.000× di heist) dengan
bobot = buku ekor yang diterima ÷ ronde yang dicoba.

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca dari halaman Studio 12 Nov 2026).

- Tes kritis: semua lolos (mode termurah 1×, std dev base 27,4, RTP 96,698% di semua mode, max win
  20.000×, harga tertinggi 600×, 5 mode, 299.988 ronde).
- Kelas risiko: **0 dari 6 gagal**. Std dev tertinggi 27,4 dari 60; ETL > 40× tertinggi 0,627
  (ante) dari 0,9; peluang ≥ 5.000× tertinggi 1,14% (heist) dari 5%; ≥ 10.000× 0,25% dari 1%.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000. Taruhan dasar terbesar yang
  diizinkan $833 (biaya heist 600×), jadi template $1.000 tidak terpakai penuh di mode itu.
- Tes format SDK: hash buku dan payout cocok di kelima mode. Peringatan `etl40b`/`etl10k` untuk
  ante dan mode beli berasal dari SDK yang tidak membagi dengan harga mode.
- Semua bayaran kelipatan 0,1× (format Engine); paytable diubah ke kelipatan 0,1 setelah tes
  format pertama menolaknya.
- Aturan diputar ulang terpisah dari kode game (`verify_books.py`): 599.980 buku base, bonus,
  inside dan heist (ante memakai buku base), semuanya mengikuti `readme.txt` (menang line dihitung
  ulang dari papan, Muscle, Hacker, kru lengket, langkah Driver, satu anak tangga Safecracker per
  menang, +1 spin per scatter, total sama dengan lookup table). Pemeriksa ini menemukan satu
  ketidakcocokan yang lalu diperbaiki: heist dulu memulai Safecracker di ×4, nilai yang tidak ada
  di tangga; sekarang ×3.

## Keputusan dan pertanyaan terbuka

Belum ada keputusan pengguna untuk math ini. Pilihan lead (2026-11-25, pengguna tidur):

1. **Safecracker naik tangga, bukan berlipat dua.** Penggandaan murni memberi sesi bonus sekitar
   1.200× (batas ×1.024) atau 294× dengan median 0,12× harga (batas ×128); penambahan +1 memberi 48×
   tanpa ekor. Tangga 1-2-3-5-8-… memberi bentuk yang tenang dan tetap punya ekor.
2. **The Job selalu dimulai dengan Safecracker di reel 2.** Tanpa itu 43% sesi tidak punya
   Safecracker dan median pembelian 0,08× harga.
3. **Hanya Driver dan Safecracker yang lengket di The Job**; Muscle dan Hacker bertindak di spin
   mereka mendarat. Roadmap menulis "semua wild lengket", tetapi Muscle lengket berarti satu reel
   wild penuh di setiap spin sisa.
4. **Getaway dihapus** (multiplier akhir ketika Driver mencapai reel 1 di ide awal). Tangga
   Safecracker sudah membawa ekor; Getaway menambah aturan tanpa mengubah bentuk.
5. **Max win 20.000×, bukan 50.000×.** 25.000× jatuh sekitar 1 dari 22 juta dari base, di luar
   pedoman Engine; 20.000× jatuh 1 dari 6,3 juta.
6. **Lima mode, bukan tujuh**; super ante 6× dan Getaway 1.000× dihapus. Ante 2× (bukan 3×).
7. **Harga mengikuti nilai**: bonus 130×, inside 290×, heist 600×.
8. Driver melewati sel kru lengket lain; Muscle tidak menutup scatter atau kru lain.
9. Bobot alami (`game_weights.py`), bukan optimizer Rust. Reel dari jumlah stop pasti dan seed
   tetap (`reels/make_reels.py`).

Risiko yang diterima atau masih terbuka:

1. **Std dev base 27,4**, lebih rendah dari ide awal (50–80, profil petaruh besar). Game ini
   bervolatilitas tinggi tetapi tidak "whale". Menaikkannya berarti fitur yang lebih jarang dan
   lebih besar, dan max win yang lebih jauh dari 1 dari 10 juta.
2. **Menang di bawah taruhan 70,9% dari semua hit di base** (lines 20 baris dengan simbol rendah).
   Frontend tidak merayakan menang di bawah taruhan.
3. **Pembelian bonus: 25,2% kembali di bawah sepersepuluh harga.** Lebih kasar daripada Floppy
   Rabbit (16%); itu sifat lines dengan satu multiplier yang tumbuh.
4. **Empat peran harus terbaca dalam satu detik di ponsel** (risiko dari laporan ide).
5. Belum diunggah ke Studio; belum di-commit.
