# Pratala: desain math

Status: disimulasikan 2026-11-16, 200.000 ronde per mode spin (base, ante, boost) dan 100.000 per
mode beli (bonus, super, hoard). Diunggah ke Studio 2026-11-16 sebagai Math Version 1: Submission Ready.

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`; target
itu ditulis dari model desain sebelum simulasi penuh dibaca.

## Ide dalam angka

Scatter pays 6×5 dengan tumble, kerangka yang sudah dikenal pemain. Yang khas adalah lantai dan
mata naga:

- **Glint Spots.** Setiap sel papan punya multiplier sendiri. Ledakan memanaskannya: belum
  menyala → siap → 2× → 4× → 8×, dan berhenti di 8×.
- **Dragon's Gaze.** Di free spins, setiap scatter (mata naga) yang mendarat menatap ke bawah
  reel-nya: kelima spot di reel itu berlipat dua, sampai 4.096×. Hanya tatapan naga yang membawa
  spot melewati 8×. Scatter tidak lagi simbol mati di dalam free spins: setiap mata yang jatuh
  mengubah papan.
- **Enam mata.** Free spins yang dipicu 6 scatter atau lebih dimulai dengan seluruh lantai
  menyala 128×. Ini pemicu puncak game: 0,24% dari sesi free spins (1 dari 418), rata-rata
  sekitar 5.900×.
- **Glint Strike** (naga menyalakan 3–6 spot) memunculkan mekanik itu di base game, 1 dari 10 spin.

Menang besar datang dari free spins: tatapan yang berulang di reel yang sama, dan sesi enam mata.

Kelas volatilitas: tinggi, profil pemain massal (std dev base 26,6). Pembanding di Engine Players,
dibaca 12 Nov 2026 (laporan riset, bagian verifikasi):

| Game | Mekanik | RTP | Max win | Std dev |
| --- | --- | --- | --- | --- |
| Ganja Snail (Donut) | cluster 7×5, multiplier sel | 96,70% | 50.000× | 27,4 |
| Lazy Vampire (Paperclip) | 19 lines, wild multiplier | 96,70% | 50.000× | 36,5 |
| Candy Dash 2 (Paperclip) | cluster 7×7, multiplier sel berlipat dua | 96,00% | 50.000× | 49,3 |
| Pratala | scatter pays 6×5, spot sel + tatapan scatter per reel | 96,70% | 25.000× | 26,6 |

Multiplier sel yang berlipat dua sudah ada di Engine (cluster pays, dan satu game scatter pays).
Yang tidak ada di game-game itu: dua sumber pertumbuhan yang berbeda (ledakan sampai 8×, tatapan
scatter untuk seluruh reel sampai 4.096×) dan pemicu enam mata.

## Aturan yang menggerakkan math

- Papan 6×5, bayar 8+ simbol sama di mana saja; simbol menang meledak dan papan tumble.
- Paytable tiga kolom: 8–9 / 10–11 / 12+. H1 membayar 10 / 25 / 50, L4 membayar 0,3 / 0,8 / 3.
- Glint Spot: ledakan pertama menyiapkan spot, kedua menyalakannya 2×, lalu berlipat dua sampai
  8×. Menang simbol × spot menyala tertinggi di bawahnya.
- Glint Strike: spot acak menyala 2× / 4× / 8×. 3–6 spot di 10% spin base dan ante dan di setiap
  spin boost; 8–15 spot di awal setiap sesi free spins.
- Dragon's Gaze (free spins): scatter yang mendarat, saat papan dibuka atau lewat tumble,
  melipatgandakan kelima spot di reel-nya (spot yang belum menyala menjadi 2×), sampai 4.096×,
  sebelum papan dievaluasi.
- Free spins: 4 / 5 / 6+ scatter memberi 10 / 12 / 15 spin; dengan 6+ scatter semua spot mulai
  128×; 3+ scatter di dalamnya menambah 5.
- Batas menang 25.000× di semua mode; mencapainya mengakhiri ronde.

## Target

Diukur dari lookup table terbitan. Sampel: 200.000 ronde (base), kecuali disebut lain.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine; 10 dari 16 game teratas | 96,698% di keenam mode |
| Hit rate base | 29–36% | Patokan scatter pays 28–43% | 32,2% |
| Free spins muncul | 1 dari 280–310 | Angka reel sendiri: 1 dari 294,8 | 1 dari 291,0 |
| Rata-rata menang free spins | 92–100× | Supaya membelinya berharga 100× | 97,0× |
| RTP base / free spins | 60–68% / 30–38% | Patokan 59/38 sampai 75/25 | 63,4% / 33,3% |
| Std dev base | 26–34 | Keputusan pengguna: sekitar 30 | 26,6 |
| Max win dan peluangnya | 25.000×, 1 dari 2–8 juta | Keputusan pengguna; pedoman Engine < 1 dari 10 juta | 25.000×, 1 dari 2.758.409 |
| Menang di bawah taruhan (dari semua hit) | ≤ 60%, dilaporkan | Tidak ada batas resmi; sampel SDK 56% | 55,3% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,356 |
| Beli bonus: balik modal / median / di bawah 10% harga | ≥ 22% / ≥ 0,38× / ≤ 17% | Model desain; paket sebelumnya 17% / 0,23× / 29% | 22,5% / 0,42× / 13,5% |
| Beli super: sama | ≥ 23% / ≥ 0,42× / ≤ 13% | Model desain (pembelian yang stabil) | 24,0% / 0,47× / 9,6% |
| Beli hoard: sama | ≥ 17% / ≥ 0,28× / ≤ 21% | Model desain (pembelian yang liar) | 18,3% / 0,33× / 17,6% |

Semua 49 target di `math_targets.json` tercapai (`math_profile.py`).

Frekuensi free spins adalah satu-satunya angka yang diselesaikan agar RTP tepat. Di base ia 1,1%
lebih sering daripada yang diberikan reel tanpa paksaan (1 dari 291,0 lawan 1 dari 294,1 pada
4 juta spin SDK; 1 dari 294,8 pada 130 juta spin model).

## Anggaran

Semua dalam kelipatan taruhan dasar.

- Spin base yang tidak memicu free spins: menang 1 dari 3,14 spin, rata-rata 1,99× → 0,634.
- Free spins: 97,2× (termasuk papan pemicu) ÷ 291,0 → 0,333.
- Jumlah: 0,634 + 0,333 = 0,967. Max win ada di dalam porsi free spins: 25.000 ÷ 2.758.409 = 0,0091.
- Sesi enam mata: 0,214% dari sesi free spins, 4,4 poin RTP mode base.
- Bonus: sesi alami 97,23× ÷ 0,967 = 100,5× → harga 100× (koreksi bobot θ = −0,0026).
- Super: sesi alami 198,89× ÷ 0,967 = 205,7× → harga 205× (θ = −0,0020).
- Hoard: sesi alami 419,03× ÷ 0,967 = 433,3× → harga 435× (θ = +0,0016).
- Ante 3×: 3 × 0,967 = 2,901 = bagian base + free spins 97,2× sebanyak 1 dari 42,6 (6,8× lebih
  sering).
- Boost 1,85×: base dengan Strike tiap spin bernilai 1,445; sisanya free spins 96,0× pada 1 dari
  278,0 (reel: 1 dari 290,4, selisih 4,3%). Boost membeli Strike, bukan free spins lebih sering.

## Mode

| Mode | Harga | Yang berubah bagi pemain | Asal harga | RTP | Balik modal | Median | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | — | 96,698% | 14,4% | 0 | 1 dari 2.758.409 |
| ante | 3× | Free spins sekitar 7× lebih sering (1 dari 43) | 3 × RTP = base + free spins | 96,698% | 7,5% | 0 | 1 dari 403.903 |
| boost | 1,85× | Glint Strike di setiap spin | nilai alami ÷ RTP | 96,698% | 16,2% | 0 | 1 dari 2.587.691 |
| bonus | 100× | Langsung free spins | 97,23× ÷ RTP | 96,698% | 22,5% | 0,42× harga | 1 dari 9.505 |
| super | 205× | Free spins, semua spot mulai 8×: pembelian yang stabil | 198,89× ÷ RTP | 96,698% | 24,0% | 0,47× harga | 1 dari 8.397 |
| hoard | 435× | Free spins, semua spot mulai 4× dan tatapan naga menyapu satu reel sebelum tiap spin: pembelian yang liar | 419,03× ÷ RTP | 96,698% | 18,3% | 0,33× harga | 1 dari 840 |

Setiap mode menawarkan hal yang berbeda jenisnya: lebih sering free spins (ante), mekanik di tiap
spin (boost), fitur (bonus), fitur dengan awal yang sudah panas (super), fitur dengan tatapan di
tiap spin (hoard). Super dan hoard berbeda sifat, bukan hanya angka awal: super mengembalikan
harganya paling sering, hoard paling sering mencapai max win.

Buku mode ante sama dengan buku mode base (aturan dan seed sama); disimulasikan sekali dan
disalin. Yang berbeda hanya bobotnya.

Pembelian menarik 4, 5 atau 6 scatter dalam proporsi yang diberikan reel base setelah tumble
selesai: 93,52% / 6,24% / 0,239% (130 juta spin tanpa paksaan). SDK memaksa jumlah scatter saat
papan dibuka, lalu tumble bisa menambah mata, jadi bobot paksaan diselesaikan dari 4 juta papan
paksaan per jumlah: 954.759 / 44.133 / 1.108. Terukur di buku hoard: 93,48% / 6,29% / 0,232%.

## Di mana varians tinggal

Varians ada di free spins, di dua tempat: reel yang ditatap berulang kali, dan sesi enam mata.
Ledakan sendiri hanya sampai 8×, sehingga badan distribusi rapat; ekornya dibawa oleh tatapan.
Yang dilihat pemain: mata naga mendarat, satu reel penuh naik tingkat warnanya (biru sampai 8×,
ungu 16–64×, jingga 128–512×, merah 1.024×+).

Diukur dari buku terbitan (`analyze_books.py`, `library/book_stats.json`):

| Penghitung | base | bonus | super | hoard |
| --- | --- | --- | --- | --- |
| Menang tumble per papan | 0,50 | 0,53 | 0,53 | 0,53 |
| Spin base dengan Glint Strike | 10,0% | — | — | — |
| Spin base dengan menang yang dikalikan | 5,5% (1 dari 18) | — | — | — |
| Porsi RTP yang lewat multiplier | 63,9% | 99,8% | 99,9% | 100% |
| Spin yang dimainkan per sesi free spins | 10,9 | 10,9 | 10,9 | 10,9 |
| Tatapan naga per sesi | 6,0 | 6,0 | 6,0 | 16,9 |
| Sesi tanpa satu pun tatapan | 0,3% | 0,3% | 0,3% | 0% |
| Sesi yang retrigger | 14,0% | 13,8% | 13,8% | 13,8% |
| Sesi tanpa satu pun menang yang dikalikan | 0,3% | 0,3% | 0,3% | 0,3% |
| Sesi enam mata: porsi sesi / poin RTP | 0,214% / 4,4 | 0,236% / 13,9 | 0,228% / 6,5 | 0,234% / 7,2 |

Multiplier tertinggi yang dipakai dalam satu sesi bonus: 16× paling sering (40,0%), 8× 28,0%,
32× 17,8%, 64× 5,5%, 128× 1,6%, 256× 0,44%, 512× 0,20%, 1.024× 0,10%, 2.048× 0,04%, 4.096× 0,02%.
Di hoard: 64× paling sering (32,1%), 32× 28,3%, 128× 16,1%, 4.096× 0,47%.

Ekor distribusi mode base, tanpa celah (peluang turun terus dari pita ke pita):

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 25.088 | 2,8% |
| 1.000–2.000× | 1 dari 73.676 | 1,9% |
| 2.000–5.000× | 1 dari 158.818 | 2,0% |
| 5.000–10.000× | 1 dari 464.832 | 1,5% |
| 10.000–25.000× | 1 dari 738.166 | 2,4% |
| di antaranya tepat 25.000× | 1 dari 2.758.409 | 0,9% |

Tidak ada ronde yang dipaksa ke max win dan tidak ada reel khusus untuk mencapainya. Ronde 25.000×
adalah free spins yang memang sampai ke sana. Rentang 12.500–25.000× lebih sering daripada max win
di semua mode (base: 1 dari 1.564.471 lawan 1 dari 2.758.409; hoard: 1 dari 449 lawan 1 dari 840).

Catatan sampel: rentang di atas 2.000× di mode base bertumpu pada 2.055 buku (134 buku di
12.500–25.000× dan 76 buku max win); bonus 2.264, super 2.686, hoard 2.973 buku. Bobot rentang itu
adalah frekuensi alaminya: buku ekor yang diterima ÷ ronde yang dicoba saat mengambil sampel
(base: 2.000 buku dari 700.430 sesi).

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca dari halaman Studio 12 Nov 2026); keluaran lengkap di
`library/math_audit.txt`.

- Tes kritis: semua lolos (mode termurah 1×, std dev base 26,6, RTP 96,698% di semua mode, max win
  25.000×, harga tertinggi 435×, 6 mode, 200.000 ronde).
- Kelas risiko: **0 dari 6 gagal**. Yang paling dekat ke batas, semuanya di mode hoard: peluang
  menang ≥ 10.000× sebesar 0,479% (batas 1%), CVaR absolut 25.000 (batas 50.000), peluang
  ≥ 25.000× 0,119% (batas 0,5%), ≥ 5.000× 1,04% (batas 5%). Std dev tertinggi 26,6 dari 60;
  ETL > 40× tertinggi 0,502 (ante) dari 0,9. Tidak ada nilai dalam 5% dari batasnya.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000. Taruhan dasar terbesar yang
  diizinkan $1.149, jadi template $1.000 terpakai penuh ($500.000 ÷ 435).
- Tes format SDK (`execute_all_tests`): hash buku dan payout cocok di keenam mode. Peringatan
  `etl40b` dan `etl10k` untuk ante, bonus, super dan hoard berasal dari SDK yang tidak membagi
  dengan harga mode; angka yang berlaku adalah audit di atas.
- Aturan diputar ulang terpisah dari kode game (`verify_books.py`): 900.000 buku, semuanya
  mengikuti `readme.txt` (bayaran, multiplier, pertumbuhan spot, tatapan, lantai awal, sapuan
  hoard, retrigger, total sama dengan lookup table).
- Studio, 2026-11-16 (Math Version 1): Submission Ready, risk checks 6 dari 6 lolos (big win
  frequency 5 dari 5, tail liability 4 dari 4, worst 0,1% 2 dari 2), template `1kmax_1cent`
  (taruhan dasar $1.000), RTP 96,70% dan std dev sama dengan audit di keenam mode. Base diberi
  label volatilitas "Extreme". Template ini memberi ruang sampai max win 50.000× dan harga 500×.

## Keputusan dan pertanyaan terbuka

Keputusan pengguna:

- 2026-11-12: max win 25.000×; std dev base sekitar 30; enam mode; "tutupi celah".
- 2026-11-16: bawa skor math review ke 9/9. Review 2026-11-15 memberi 7/9 karena lima hal:
  taruhan dasar maksimum $781 (di bawah template $1.000), pembelian yang jarang balik modal
  (17–18%, median 0,22× harga), super dan hoard yang mirip, kerangka mekanik yang sudah ada di
  Engine, dan teks yang tertinggal. Perubahan di bawah menjawab kelimanya.

Pilihan desain yang mengikuti keputusan itu:

- **Ledakan berhenti di 8×, tatapan scatter membawa sisanya.** Pada aturan lama (ledakan
  berlipat dua sampai 4.096×) median pembelian 0,23× harga, dan tidak ada penyetelan yang
  mengubahnya: nilai rata-rata dibawa segelintir sesi yang spot-nya berlipat berkali-kali. Model
  menunjukkan median ditentukan oleh panjang ruang lipat-ganda yang dijangkau sesi biasa. Memotong
  ruang itu untuk ledakan dan memberikannya ke peristiwa yang lebih jarang (scatter mendarat)
  menaikkan median ke 0,42× dan balik modal ke 22,5% tanpa menghilangkan ekor.
- **Enam mata = lantai 128×.** Tanpa pembawa ekor yang jarang, max win 25.000× di model tercapai
  lebih jarang dari 1 dari 20 juta spin base. Sesi enam mata membawanya ke 1 dari 2,76 juta. Harganya: 14% RTP
  pembelian bonus berada di sesi yang muncul 1 dari 418 pembelian.
- **Max win tetap 25.000×, bukan 50.000×.** 50.000× diuji di model: dengan aturan ini ia tercapai
  alami lebih jarang dari 1 dari 15 juta spin base (pedoman Engine: lebih sering dari 1 dari 10
  juta). Mencapainya butuh ekor yang lebih berat, yang mengembalikan pembelian ke median 0,2–0,3×.
- **Hoard 435×, bukan ~1.000×.** Dua alasan: di atas 500× template taruhan $1.000 tidak terpakai
  penuh, dan tatapan di tiap spin dengan lantai 8× (1.051×) memberi peluang ≥ 10.000× sebesar
  1,6% (gagal kelas Tail Probability).
- **Glint Strike pembuka lebih lebar (8–15 spot)** supaya hampir setiap menang di free spins
  dikalikan sejak spin pertama, dan Strike base sedikit lebih besar (rata-rata 4,4 spot) supaya
  frekuensi free spins yang diselesaikan sama dengan yang diberikan reel.
- Bobot alami (`game_weights.py`), bukan optimizer Rust.

Risiko yang diterima atau masih terbuka:

1. **Hoard tetap pembelian yang liar.** 18,3% balik modal, median 0,33× harga, 17,6% kembali di
   bawah 10% harga. Tatapan di tiap spin membangun multiplier di akhir sesi, jadi menang awal
   kecil. Ini sifat yang dijual mode itu (max win 1 dari 840), dan teks mode menyebut apa yang
   dibeli. Bila dianggap terlalu keras, pilihannya menaikkan lantai awal hoard (harga ikut naik).
2. **Headline 25.000×** di bawah median 50.000× game teratas Engine (lihat pilihan desain).
3. **Tangga mode berhenti di 435×**, di bawah patokan pasar 1.000–5.000×. Ditukar dengan template
   taruhan penuh dan lolos semua kelas risiko.
4. **Ante 3×**: 7,5% spin mengembalikan harga spin; 78% hit bernilai di bawah 3×. Frontend tidak
   merayakan menang yang tidak melebihi harga ronde.
5. **Menang di bawah taruhan 55,3% dari semua hit di base.**
6. **Std dev base 26,6**, di tepi bawah "sekitar 30". Ekor yang lebih ringan adalah yang
   menaikkan pengembalian pembelian.
7. **Boost**: free spins 4,3% lebih sering daripada angka reel pada harga 1,85×; harga 1,83×
   akan menyamakannya.
8. **Presentasi tatapan di frontend masih memakai gerak Glint Strike** (mata menyipit, spot
   menyala dari dalam). Berfungsi dan sudah dicek di game lokal; gerak khusus per reel belum ada.
