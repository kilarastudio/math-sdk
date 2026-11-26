# Floppy Rabbit: desain math

Status: disimulasikan 2026-11-24, 200.000 ronde per mode spin (base, ante) dan 100.000 per mode
beli (bonus, double, fluffle). Disetujui pengguna 2026-11-24. Belum diunggah ke Studio.

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`.

## Ide dalam angka

Cluster pays 7×7 dengan cascade, kerangka dengan pemain terbanyak di Engine. Yang khas adalah
kelinci di atas papan dan dua aksinya:

- **Hop.** Kelinci melompat ke sel lain dan meninggalkan jejak 2× di sana. Jejak adalah
  multiplier sel; cluster dibayar × jumlah jejak di bawahnya.
- **Flop.** Kelinci rebah, dan **semua jejak di papan berlipat dua**. Hop menambah jumlah jejak,
  Flop menaikkan nilainya.
- **Flop Time** (free spins): jejak dan kelinci bertahan sepanjang sesi. 3 scatter membawa satu
  kelinci, 4 scatter dua, 5 scatter tiga (**Fluffle**). Sebelum free spin ke-9 kelinci pasti
  rebah, jadi tidak ada sesi tanpa Flop.

Menang besar datang dari Flop Time: beberapa Flop di atas papan yang sudah penuh jejak, sesi yang
retrigger, dan sesi dua atau tiga kelinci.

Kelas volatilitas: tinggi, profil pemain massal (std dev base 22,8). Pembanding di Engine
(Engine Players dan Engine Insights, dibaca 16 Nov 2026; `reports/Riset Chill Capy 2026-11-16.md`):

| Game | Aturan multiplier sel | RTP | Max win | Std dev |
| --- | --- | --- | --- | --- |
| Ganja Snail (Donut) | modifier melipatgandakan sel | 96,70% | 50.000× | 27,4 |
| Midas Squares (Paperclip) | tidak dipublikasikan | 96,70% | 25.000× | 29,8 |
| Candy Dash 2 (Paperclip) | sel yang meledak berlipat dua sampai 4.096× | 96,00% | 50.000× | 49,3 |
| Stoned Pandas (Lucky Bastards) | sel yang menang naik satu level sampai 1.024× | 96,5% | 20.000× | 18,3 |
| Floppy Rabbit | jejak dari Hop; Flop melipatgandakan seluruh papan, sampai 4.096× | 96,70% | 25.000× | 22,8 |

Di game-game itu sel tumbuh karena menang di atasnya. Di sini sel tumbuh karena aksi maskot, dan
satu aksi (Flop) menaikkan seluruh papan sekaligus.

## Aturan yang menggerakkan math

- Papan 7×7. Cluster 5+ simbol sama yang bersentuhan sisi; simbol menang hilang dan papan cascade.
- Tujuh simbol bayar (4 tinggi, 3 rendah) dan scatter. Tanpa wild.
- Paytable empat kolom: 5 / 6–8 / 9–12 / 13+. H1 membayar 5 / 12 / 25 / 60, L3 membayar
  0,2 / 0,7 / 2,5 / 5.
- Jejak: 2× → 4× → … sampai 4.096×. Cluster dibayar × **jumlah** jejak di sel-selnya (tanpa
  jejak: ×1). Jejak menempel di posisi, tidak ikut jatuh.
- Hop: kelinci pindah paling jauh dua sel ke segala arah; sel tujuan mendapat jejak 2×, atau
  jejaknya berlipat dua.
- Flop: kelinci tetap di tempat; semua jejak di papan berlipat dua.
- Base: saat papan dibuka kelinci melompat sekali ke sel mana pun. Setelah tiap cascade menang
  satu aksi: Hop, atau Flop (peluang 20%) mulai cascade kedua. Jejak dihapus tiap ronde.
- Flop Time: 12 free spin di papan bersih; tiap kelinci mulai di sel acak dengan jejak 2×.
  Sebelum tiap spin dievaluasi dan setelah tiap cascade menang, setiap kelinci beraksi sekali.
  Sebelum free spin ke-9 kelinci pertama pasti rebah. 3+ scatter di dalam sesi menambah 5 spin.
- Peluang Flop per aksi adalah bobot buku: 11,4% dengan satu kelinci, 4,9% per kelinci dengan
  dua, 3,35% dengan tiga.
- Ronde yang dibeli menampilkan tepat jumlah scatter modenya.
- Batas menang 25.000× di semua mode; mencapainya mengakhiri ronde.

## Target

Diukur dari lookup table terbitan. Sampel: 200.000 ronde (base), kecuali disebut lain.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine; mayoritas game teratas | 96,698% di kelima mode |
| Hit rate base | 35–43% | Patokan cluster 32–35%; maskot butuh cascade untuk beraksi | 40,9% |
| Flop Time muncul | 1 dari 335–380 | Angka reel sendiri: 1 dari 346,5 | 1 dari 362,9 |
| Rata-rata menang Flop Time | 108–118× | Campuran satu, dua dan tiga kelinci | 113,1× |
| RTP base / Flop Time | 62–67% / 30–36% | Patokan 59/38 sampai 75/25 | 65,5% / 31,2% |
| Std dev base | 23–32 | Profil pemenang jumlah pemain (27–30) | **22,8 (meleset)** |
| Max win dan peluangnya | 25.000×, 1 dari 2–9 juta | Pedoman Engine: lebih sering dari 1 dari 10 juta | 25.000×, 1 dari 8.133.955 |
| Menang di bawah taruhan (dari semua hit) | ≤ 55%, dilaporkan | Tidak ada batas resmi | 45,4% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,290 |
| Beli bonus: balik modal / median / di bawah 10% harga | ≥ 21% / ≥ 0,36× / ≤ 18% | Sesi tanpa paksaan sebelum simulasi penuh | 21,4% / 0,37× / 16,1% |
| Beli double: sama | ≥ 20% / ≥ 0,35× / ≤ 17% | sama | 20,6% / **0,349× (meleset)** / 16,8% |
| Beli fluffle: sama | ≥ 19% / ≥ 0,31× / ≤ 20% | sama | 19,4% / **0,305× (meleset)** / **20,1% (meleset)** |

Empat dari 41 target di `math_targets.json` meleset, semuanya tipis; lihat "Risiko".

Frekuensi Flop Time adalah satu-satunya angka yang diselesaikan agar RTP tepat. Di base ia 4,7%
lebih jarang daripada yang diberikan reel tanpa paksaan (1 dari 362,9 lawan 1 dari 346,5 pada
10 juta spin).

## Anggaran

Semua dalam kelipatan taruhan dasar.

- Spin base yang tidak memicu Flop Time: menang 1 dari 2,46 spin, rata-rata 1,61× → 0,655.
- Flop Time: 113,1× ÷ 362,9 → 0,312. Jumlah: 0,655 + 0,312 = 0,967.
- Max win ada di dalam porsi Flop Time: 25.000 ÷ 8.133.955 = 0,0031.
- Campuran kelinci di sesi alami: satu 95,53% (28,2 poin RTP), dua 4,32% (2,9 poin), tiga 0,15%
  (0,2 poin).
- Bonus: sesi alami 106,93× ÷ 0,967 = 110,6× → harga 110× (koreksi bobot θ = −0,0025).
- Double: 247,16× ÷ 0,967 = 255,6× → harga 250× (θ = −0,0101).
- Fluffle: 498,28× ÷ 0,967 = 515,3× → harga 500× (θ = −0,0127).
- Ante 3×: 3 × 0,967 = 2,901 = bagian base + Flop Time 113,1× sebanyak 1 dari 50,3 (7,2× lebih
  sering).

## Mode

| Mode | Harga | Yang berubah bagi pemain | RTP | Balik modal | Median | Di bawah 10% harga | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | 96,698% | 22,3% | 0 | — | 1 dari 8.133.955 |
| ante | 3× | Flop Time sekitar 7× lebih sering (1 dari 50) | 96,698% | 7,7% | 0 | — | 1 dari 1.127.174 |
| bonus | 110× | Langsung Flop Time, 3 scatter: satu kelinci | 96,698% | 21,4% | 0,37× harga | 16,1% | 1 dari 26.217 |
| double | 250× | Flop Time, 4 scatter: dua kelinci | 96,698% | 20,6% | 0,35× harga | 16,8% | 1 dari 4.013 |
| fluffle | 500× | Flop Time, 5 scatter: tiga kelinci | 96,698% | 19,4% | 0,30× harga | 20,1% | 1 dari 896 |

Lima mode. Buku mode ante sama dengan buku mode base (aturan dan seed sama); yang berbeda hanya
bobotnya.

Scatter saat papan pemicu dibuka di mode base ditarik dengan bobot 96.414 / 3.476 / 110 untuk
3 / 4 / 5, supaya jumlah akhirnya setelah cascade sama dengan permainan tanpa paksaan: 95,53% /
4,33% / 0,14% (10 juta spin, 28.860 pemicu; 600.000 papan paksaan per jumlah).

## Di mana varians tinggal

Di Flop. Sesi satu kelinci rata-rata punya 16,4 Hop dan 3,1 Flop; jejak yang sudah ada saat Flop
terjadi berlipat dua semuanya. Flop pasti sebelum spin ke-9 memberi setiap sesi satu lipatan atas
papan yang sudah terisi; Flop acak dan retrigger (14% sesi) membawa ekor.

Diukur dari buku terbitan (`analyze_books.py`, `library/book_stats.json`):

| Penghitung | base | bonus | double | fluffle |
| --- | --- | --- | --- | --- |
| Cascade menang per papan | 0,52 | 0,52 | 0,51 | 0,51 |
| Ronde dengan menang base yang kena jejak | 7,7% (1 dari 13) | — | — | — |
| Ronde dengan Flop di base | 2,2% | — | — | — |
| Porsi RTP yang lewat jejak | 50,8% | 97,1% | 99,4% | 99,8% |
| Spin yang dimainkan per sesi | 12,8 | 12,8 | 12,8 | 12,8 |
| Sesi yang retrigger | 14,2% | 13,8% | 13,5% | 13,5% |
| Hop per sesi | 17,4 | 16,4 | 36,2 | 55,6 |
| Flop per sesi | 3,09 | 3,12 | 2,85 | 2,91 |
| Sesi tanpa Flop | 0% | 0% | 0% | 0% |
| Sel berjejak di akhir sesi | 14,4 | 13,8 | 25,2 | 32,8 |

Jejak terbesar di akhir sesi bonus: 32× paling sering (26,9%), 16× 23,9%, 64× 19,9%, 128× 11,1%,
8× 10,0%, 256× 5,0%, 512× 1,9%, 1.024×+ 1,1%. Di fluffle: 128× 23,3%, 64× 23,1%, 256× 16,8%,
4.096× 1,7%.

Ekor distribusi mode base, tanpa celah (peluang turun terus dari pita ke pita):

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 16.429 | 4,3% |
| 1.000–2.000× | 1 dari 45.103 | 3,2% |
| 2.000–5.000× | 1 dari 114.636 | 2,7% |
| 5.000–10.000× | 1 dari 491.613 | 1,4% |
| 10.000–25.000× | 1 dari 1.192.980 | 1,4% |
| di antaranya tepat 25.000× | 1 dari 8.133.955 | 0,3% |

Tidak ada ronde yang dipaksa ke max win dan tidak ada reel khusus untuk mencapainya. Rentang
12.500–25.000× lebih sering daripada max win di semua mode (base: 1 dari 2.418.203).

Catatan sampel: rentang di atas 2.000× di mode base bertumpu pada 2.075 buku, dan max win pada
22 buku (bonus 25, double 164, fluffle 119). Bobot rentang itu adalah frekuensi alaminya: buku
ekor yang diterima ÷ ronde yang dicoba saat mengambil sampel.

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca dari halaman Studio 12 Nov 2026).

- Tes kritis: semua lolos (mode termurah 1×, std dev base 22,8, RTP 96,698% di semua mode, max win
  25.000×, harga tertinggi 500×, 5 mode, 200.000 ronde).
- Kelas risiko: **0 dari 6 gagal**. Yang paling dekat ke batas, semuanya di fluffle: peluang
  menang ≥ 10.000× sebesar 0,49% (batas 1%), CVaR absolut 25.000 (batas 50.000), peluang ≥ 5.000×
  1,25% (batas 5%), ≥ 25.000× 0,11% (batas 0,5%). Std dev tertinggi 22,8 dari 60; ETL > 40×
  tertinggi 0,550 (ante) dari 0,9.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000. Taruhan dasar terbesar yang
  diizinkan $1.000, jadi template $1.000 terpakai penuh.
- Tes format SDK (`execute_all_tests`): hash buku dan payout cocok di kelima mode. Peringatan
  `etl40b` dan `etl10k` untuk ante dan mode beli berasal dari SDK yang tidak membagi dengan harga
  mode; angka yang berlaku adalah audit di atas.
- Aturan diputar ulang terpisah dari kode game (`verify_books.py`): 700.000 buku, semuanya
  mengikuti `readme.txt` (cluster yang dibayar sama dengan pencarian cluster independen, bayaran ×
  jumlah jejak, jangkauan Hop, Flop melipatgandakan semua jejak, urutan aksi, Flop pasti sebelum
  spin ke-9, jumlah kelinci, scatter mode beli, retrigger, total sama dengan lookup table).
  Pemeriksa diuji dengan tiga aturan yang sengaja disalahkan dan menangkap ketiganya.

## Keputusan dan pertanyaan terbuka

Keputusan pengguna:

- 2026-11-16: maskot fuzzy lop.
- 2026-11-23: nama Floppy Rabbit; mekanik Hop & Flop; mode teratas Fluffle (tiga kelinci).
- 2026-11-24: math dikerjakan dulu, visual frontend setelahnya.
- 2026-11-24: math ini disetujui dengan pilihan desain di bawah dan empat target yang meleset
  tipis diterima apa adanya (risiko 1).

Pilihan desain lead, disetujui pengguna 2026-11-24:

1. **Flop melipatgandakan semua jejak, bukan hanya sel kelinci.** Dengan aturan awal sesi Flop
   Time bernilai sekitar 18× di model desain (`design_model.py`, model cepat sebelum kode SDK) dan
   tidak pernah mendekati 5.000×.
2. **Aksi juga terjadi sebelum tiap free spin**, bukan hanya setelah cascade: cascade menang
   hanya 0,52 per papan, jadi tanpa ini kelinci terlalu jarang beraksi.
3. **12 free spin**, dan **jumlah kelinci mengikuti scatter** (1 / 2 / 3), menggantikan usulan
   lama "dua aksi per cascade" dan "baris jejak".
4. **Flop pasti sebelum free spin ke-9.** Tanpa itu 5,5% sesi tidak punya Flop dan beli bonus
   balik modal 19,6% dengan median 0,34× harga. Flop pasti di spin ke-7 memberi pembelian yang
   lebih tenang (22,1% / 0,39×) tetapi max win base menjadi 1 dari 12,2 juta, di luar pedoman
   Engine. Spin ke-9 adalah titik tengah: 21,4% / 0,37× dan 1 dari 8,1 juta.
5. **Bonus 110×, bukan 100×.** Harga mengikuti nilai. Pada varian Flop pasti di spin ke-7,
   menurunkan peluang Flop sampai bonus bernilai 100× membawa max win base ke sekitar 1 dari
   11 juta (perkiraan dari sesi tanpa paksaan); untuk spin ke-9 harga 100× belum diukur.
6. **Max win 25.000×, bukan 50.000×.** Sesi tanpa paksaan mencapai 50.000× sekitar 5 sampai 10
   kali lebih jarang daripada 25.000×; dari base itu jauh di luar 1 dari 10 juta.
7. **Fluffle 500×, bukan sekitar 1.000×**: template taruhan $1.000 terpakai penuh dan semua
   kelas risiko lolos dengan jarak.
8. **Batas jejak 4.096×** (preseden Candy Dash 2).
9. Reel dibangun dari tumpukan simbol dengan jumlah pasti (`reels/make_reels.py`), karena
   susunan acak menggeser hit rate beberapa persen dari satu pengocokan ke pengocokan berikutnya.
   Bobot alami (`game_weights.py`), bukan optimizer Rust.

Ditolak setelah diukur: Flop saat retrigger (membuat double dan fluffle balik modal 17–18%).

Risiko yang diterima atau masih terbuka:

1. **Empat target meleset tipis.** Std dev base 22,8 (target 23); median double 0,349× (0,35×);
   median fluffle 0,305× (0,31×) dan 20,1% pembelian fluffle kembali di bawah 10% harga (20%).
   Target itu ditulis dari sesi tanpa paksaan dengan Flop pasti di spin ke-7; memindahkannya ke
   spin ke-9 menukar sedikit ketenangan pembelian dengan max win yang masuk pedoman. Diterima
   pengguna 2026-11-24; target di `math_targets.json` tidak diubah. Bila ingin ditutup: setel
   ulang peluang Flop double dan fluffle (nilai alaminya 2–3% di atas harga) dan simulasikan
   ulang dua mode itu.
2. **Max win base 1 dari 8,1 juta bertumpu pada 22 buku.** Jaraknya ke pedoman 1 dari 10 juta
   hanya 19%. Sampel ekor yang lebih besar akan memastikannya.
3. **Headline 25.000×** di bawah median 50.000× game teratas Engine.
4. **Tangga mode berhenti di 500×** dan hanya lima mode; patokan pasar 5–8 mode sampai
   1.000–5.000×.
5. **Ante 3×**: 7,7% spin mengembalikan harga spin. Frontend tidak merayakan menang yang tidak
   melebihi harga ronde.
6. **Menang di bawah taruhan 45,4% dari semua hit di base.**
7. **Frekuensi Flop Time yang diselesaikan 4,7% lebih jarang** daripada angka reel.
8. **Teaser base tipis**: 7,7% ronde punya menang yang kena jejak, dan Flop terlihat di 2,2%
   ronde base.
