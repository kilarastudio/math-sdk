# Dragon's Glint: desain math

Status: disimulasikan 2026-11-12, 200.000 ronde per mode spin (base, ante, boost) dan 100.000 per
mode beli (bonus, super, hoard). Belum diunggah ke Studio.

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`.

## Ide dalam angka

Scatter pays 6×5 dengan tumble, kerangka yang sudah dikenal pemain. Yang khas adalah **Glint
Spots**: setiap sel papan punya multiplier sendiri yang berlipat dua tiap kali simbol di atasnya
meledak, sampai 4.096×, dan sebuah menang dikalikan spot paling terang di bawah simbolnya. Di base
game spot direset tiap ronde; di free spins spot bertahan sepanjang sesi, dan dari situlah menang
besar datang. **Glint Strike** (naga menyalakan 3–6 spot) memunculkan mekanik itu di base game.

Kelas volatilitas: tinggi, profil pemain massal (std dev base sekitar 30). Pembanding di Engine
Players, dibaca 12 Nov 2026 (laporan riset, bagian verifikasi):

| Game | Mekanik | RTP | Max win | Std dev |
| --- | --- | --- | --- | --- |
| Ganja Snail (Donut) | cluster 7×5, multiplier sel | 96,70% | 50.000× | 27,4 |
| Lazy Vampire (Paperclip) | 19 lines, wild multiplier | 96,70% | 50.000× | 36,5 |
| Candy Dash 2 (Paperclip) | cluster 7×7, multiplier sel berlipat dua | 96,00% | 50.000× | 49,3 |
| Dragon's Glint | scatter pays 6×5, multiplier sel berlipat dua | 96,70% | 25.000× | 31,4 |

Multiplier sel berlipat dua sudah ada di cluster pays; versi scatter pays masih jarang.

## Aturan yang menggerakkan math

- Papan 6×5, bayar 8+ simbol sama di mana saja; simbol menang meledak dan papan tumble.
- Paytable tiga kolom: 8–9 / 10–11 / 12+. H1 membayar 10 / 25 / 50, L4 membayar 0,3 / 0,8 / 3.
- Glint Spot: ledakan pertama menyiapkan spot, kedua menyalakannya 2×, lalu berlipat dua sampai
  4.096×. Menang simbol × spot menyala tertinggi di bawahnya (aturan "maks", bukan jumlah).
- Glint Strike: 3–6 spot acak menyala 2× / 4× / 8×. Terjadi di 10% spin base dan ante, di setiap
  spin boost, dan di awal setiap sesi free spins.
- Free spins: 4 / 5 / 6+ scatter memberi 10 / 12 / 15 spin; 3+ scatter di dalamnya menambah 5.
- Batas menang 25.000× di semua mode; mencapainya mengakhiri ronde.

## Target

Diukur dari lookup table terbitan. Sampel: 200.000 ronde (base), kecuali disebut lain.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine; 10 dari 16 game teratas | 96,698% di keenam mode |
| Hit rate base | 29–36% | Patokan scatter pays 28–43% | 32,2% |
| Free spins muncul | 1 dari 260–320 | Patokan 1 dari 200–450; angka reel sendiri | 1 dari 301,7 (reel: 1 dari 294,9) |
| Rata-rata menang free spins | 92–102× | Supaya membelinya berharga 100× | 97,0× |
| RTP base / free spins | 60–68% / 30–38% | Patokan 59/38 sampai 75/25 | 64,5% / 32,2% |
| Std dev base | 26–34 | Keputusan pengguna: sekitar 30 | 31,4 |
| Max win dan peluangnya | 25.000×, 1 dari 2–10 juta | Keputusan pengguna; pedoman Engine < 1 dari 10 juta | 25.000×, 1 dari 2.553.380 |
| Menang di bawah taruhan (dari semua hit) | ≤ 60%, dilaporkan | Tidak ada batas resmi; sampel SDK 56% | 55,5% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,358 |

Frekuensi free spins di tabel (1 dari 301,7) adalah satu-satunya angka yang diselesaikan agar RTP
tepat; ia 2,3% lebih jarang daripada yang diberikan reel tanpa paksaan (1 dari 294,9, diukur dari
4 juta spin).

## Anggaran

Semua dalam kelipatan taruhan dasar.

- Spin base yang tidak memicu free spins: menang 1 dari 3,14 spin, rata-rata 2,02× → 0,645.
- Free spins: 97,2× (termasuk papan pemicu) ÷ 301,7 → 0,322.
- Jumlah: 0,645 + 0,322 = 0,967. Max win ada di dalam porsi free spins: 25.000 ÷ 2.553.380 = 0,0098.
- Bonus: sesi alami 96,56× ÷ 0,967 = 99,9× → harga 100× (koreksi bobot θ = +0,0005).
- Super: sesi alami 334,4× ÷ 0,967 = 345,8× → harga 350× (θ = +0,0039, dalam galat sampel).
- Hoard: sesi alami 621,4× ÷ 0,967 = 642,6× → harga 640× (θ = −0,0014).
- Ante 3×: 3 × 0,967 = 2,901 = bagian base + free spins 97,2× sebanyak 1 dari 42,8 (7× lebih sering).
- Boost 1,9×: base dengan Strike tiap spin bernilai 1,505; sisanya free spins pada 1 dari 298,8,
  di samping angka reel (1 dari 295,9). Boost membeli Strike, bukan free spins lebih sering.

## Mode

| Mode | Harga | Yang berubah bagi pemain | Asal harga | RTP | Balik modal | Median | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | — | 96,698% | 14,3% | 0 | 1 dari 2.553.380 |
| ante | 3× | Free spins sekitar 7× lebih sering (1 dari 43) | 3 × RTP = base + free spins | 96,698% | 7,3% | 0 | 1 dari 362.518 |
| boost | 1,9× | Glint Strike di setiap spin | nilai alami ÷ RTP | 96,698% | 15,8% | 0 | 1 dari 2.571.808 |
| bonus | 100× | Langsung free spins | 96,56× ÷ RTP | 96,698% | 17,2% | 0,23× harga | 1 dari 9.250 |
| super | 350× | Free spins, semua spot mulai 4× | 334,4× ÷ RTP | 96,698% | 17,2% | 0,21× harga | 1 dari 1.127 |
| hoard | 640× | Free spins, semua spot mulai 8× | 621,4× ÷ RTP | 96,698% | 18,2% | 0,22× harga | 1 dari 458 |

Buku mode ante sama dengan buku mode base; yang berbeda hanya bobotnya.

## Di mana varians tinggal

Varians ada di free spins, pada spot yang terus berlipat dua. Yang dilihat pemain: spot menyala,
warnanya naik tingkat, dan angka di sel membesar sampai satu menang mendarat di atasnya.

Diukur dari buku terbitan (`analyze_books.py`, `library/book_stats.json`):

| Penghitung | base | bonus |
| --- | --- | --- |
| Menang tumble per papan | 0,50 | 0,53 |
| Spin base dengan Glint Strike | 10,1% | — |
| Spin base dengan menang yang dikalikan | 5,4% (1 dari 18,5) | — |
| Porsi RTP yang lewat multiplier | 63,6% | 99,3% |
| Spin yang dimainkan per sesi free spins | 11,0 | 11,0 |
| Sesi yang retrigger | 13,7% | 14,1% |
| Sesi tanpa satu pun menang yang dikalikan | 2,0% | 1,9% |

Multiplier tertinggi yang dipakai dalam satu sesi bonus: 8× paling sering (25,3%), 16× 20,5%,
32× 13,0%, 64× 6,8%, 128× 3,3%, 256× 1,4%, 512× 0,60%, 1.024× 0,24%, 2.048× 0,09%, 4.096× 0,06%.

Ekor distribusi mode base, tanpa celah:

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 17.431 | 4,1% |
| 1.000–2.000× | 1 dari 46.753 | 3,1% |
| 2.000–5.000× | 1 dari 86.631 | 3,6% |
| 5.000–10.000× | 1 dari 311.937 | 2,3% |
| 10.000–25.000× | 1 dari 539.603 | 3,3% |
| di antaranya tepat 25.000× | 1 dari 2.553.380 | 1,0% |

Tidak ada ronde yang dipaksa ke max win dan tidak ada reel khusus untuk mencapainya. Ronde 25.000×
adalah free spins yang memang sampai ke sana. Rentang 12.500–25.000× lebih sering daripada max win
di semua mode (base: 1 dari 1.027.709 lawan 1 dari 2.553.380).

Catatan sampel: rentang di atas 2.000× di mode spin bertumpu pada sekitar 4.100 buku per mode
(241 buku di 12.500–25.000× dan 97 buku max win di base). Bobot rentang itu adalah frekuensi
alaminya: buku ekor yang diterima ÷ ronde yang dicoba saat mengambil sampel.

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca dari halaman Studio 12 Nov 2026).

- Tes kritis: semua lolos (mode termurah 1×, std dev base 31,4, RTP 96,698% di semua mode, max win
  25.000×, harga tertinggi 640×, 6 mode, 200.000 ronde).
- Kelas risiko: **0 dari 6 gagal**. Yang paling dekat ke batas adalah mode hoard: peluang menang
  ≥ 10.000× sebesar 0,882% (batas 1%, selisih 12%), ≥ 5.000× 2,11% (batas 5%), ≥ 25.000× 0,218%
  (batas 0,5%). Std dev tertinggi 31,4 dari 60; ETL>40× tertinggi 0,576 (ante) dari 0,9.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000. Taruhan dasar terbesar
  $781,25 ($500.000 ÷ 640).
- Tes format SDK (`execute_all_tests`): hash buku dan payout cocok di keenam mode. Peringatan
  "fails 3-star volatility limits" untuk ante, bonus, super dan hoard berasal dari SDK yang tidak
  membagi dengan harga mode; angka yang berlaku adalah audit di atas.
- Belum dicek: angka Studio sendiri setelah unggah. Definisi "ETL > 10.000×" di halaman tidak
  menyebut apakah ambangnya dikalikan harga; audit membacanya sebagai 10.000× taruhan dasar.

## Keputusan dan pertanyaan terbuka

Keputusan pengguna, 2026-11-12:

- Max win 25.000× (sebelumnya 15.000×).
- Std dev base sekitar 30 (sebelumnya 20,4).
- Enam mode dengan puncak sekitar 1.000× (sebelumnya lima, puncak 250×).
- "Tutupi celah": kekurangan yang dilaporkan setelah putaran pertama ditutup. Akibatnya puncak
  tangga turun ke 640× (lihat di bawah).

Pilihan desain yang mengikuti keputusan itu:

- Batas spot 4.096×, bukan 256×. Dengan 256× sesi free spins tidak pernah melewati 7.500× dalam
  300.000 sesi, sehingga max win harus dipaksa dan ada celah di bawahnya.
- Retrigger lebih sering (4 scatter per reel di free spins) untuk kemiringan distribusi.
- Paytable tiga kolom dengan premium lebih curam. Kolom 14+ pada paytable lama tidak pernah
  membayar untuk H1 dan H2 dalam 8 juta papan.
- Bobot alami (`game_weights.py`), bukan optimizer Rust.
- **Hoard 640× (semua spot mulai 8×), bukan ~1.000×.** Versi 1.175× (semua spot mulai 16×) gagal
  kelas Tail Probability (peluang ≥ 10.000× 2,09%). Mekanik ini tidak punya bentuk mode ~1.000×
  yang lolos: dari sebelas susunan yang dicoba di model (3–30 spin, nilai awal spot 2×–256×),
  semua yang bernilai 870× ke atas memberi 1,3% atau lebih.

Risiko yang diterima atau masih terbuka:

1. **Pembelian sering kembali kecil.** 29,1% pembelian bonus mengembalikan kurang dari 10% harga
   (super 32,6%, hoard 31,4%); median bonus 0,23× harga. Penyetelan tidak mengubahnya: tujuh
   varian di model (jumlah spin, kekuatan Glint Strike, aturan spot) semuanya memberi 29–33%. Yang
   bisa menutupnya hanya aturan menang minimum terjamin (10% harga berbiaya 1,6–2% nilai sesi).
   Tidak dipasang: 10× pada pembelian 100× tetap terasa bonus gagal, dan catatan reviewer nyata
   menyebut pembelian yang kembali kecil tidak menentukan skor. Mekaniknya selalu terlihat: setiap
   sesi dibuka dengan Glint Strike dan hanya 1,9% sesi berakhir tanpa menang yang dikalikan.
2. **Ante 3×**: hanya 7,3% spin mengembalikan harga spin; 78% hit bernilai di bawah 3×. Frontend
   sekarang tidak merayakan menang yang tidak melebihi harga ronde.
3. **Menang di bawah taruhan 55,5% dari semua hit di base.** Paytable tiga kolom menaikkannya dari
   sekitar 50% karena 9 simbol rendah sekarang dibayar di kolom pertama.
4. **Tangga mode pendek di puncak**: 100× / 350× / 640×, di bawah patokan pasar 1.000–5.000×.
   Ini harga dari lolos semua kelas risiko dengan max win 25.000×.
5. **Mode hoard belum punya gambar sendiri** di frontend (memakai gambar super).
