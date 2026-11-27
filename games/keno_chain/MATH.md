# Keno Chain: desain math

Status: **math v2**, tag git `keno-chain-math-v2`. Dihitung pasti 2026-11-27 (enumerasi penuh,
bukan simulasi) dan diunggah ke Studio oleh pengguna 2026-11-27: 20 mode lolos, setiap angka di
Studio sama dengan lembar ini.

Math v1 (tag `keno-chain-math-v1`, commit 3debc9a, diunggah ke Studio 2026-11-27, digantikan v2):
dua tingkat, Low dengan 1-10 angka dan High dengan 3-10 angka. Rancangan sebelum v1 tidak pernah
diunggah.

Nama untuk pemain, diputuskan pengguna 2026-11-27 ("ganti dengan lucky number saja"): lucky
number, lucky ball, lucky round. Nama lamanya Kilau masih dipakai di kode dan di event buku
(`kilau`, `kilauRound`, `kilauHits`). Kata "lucky" tidak ada di daftar frasa terlarang Engine.

## Ide dalam angka

Keno papan 40 angka. Pemain memilih 3, 4, 5, 6, 8 atau 10 angka dan satu tingkat sebelum ronde.
Angka yang tidak dipilih ditandai sebagai lucky number: biasanya 1, dan pada 1 dari 5 ronde (lucky
round) 3. Angka ditarik satu per satu; kemenangan = bayaran untuk jumlah kena × pengali meter.
Meter naik lewat kena berturut-turut dan lewat lucky ball, jadi urutan tarikan ikut menentukan
hasil.

Batas 20 mode (Engine Support 2026-11-27: studio eksternal tidak boleh lebih) berarti 18 pilihan
seharga 1× ditambah 2 mode berbayar. 18 pilihan itu dibagi menjadi 3 tingkat × 6 jumlah angka:

1. Calm, Bold, Wild adalah tiga tingkat volatilitas untuk tarikan yang sama: peluang tiap jumlah
   kena sama di ketiganya, hanya tabel bayarannya berbeda. Di setiap tingkat volatilitas dan
   puncak kemenangan naik per jumlah angka, dan pada setiap jumlah angka Calm < Bold < Wild.
2. Jumlah angka yang tidak dimainkan: 1 dan 2 (terlalu sedikit hasil untuk tiga tabel), 7 dan 9
   (terasa seperti 8 dan 10). Di v1, Low 7 sampai 10 nyaris kembar (puncak 500-750×, std 2,5-3,3)
   dan pada 8 angka tidak ada pilihan di antara std 2,5 dan 36,7.
3. Lucky round: rasa mode premium (3 lucky number) muncul acak di Calm, Bold, Wild dan Chain,
   tanpa memakai slot mode. Chain Max adalah versi yang dibeli.

Lucky number selalu ditaruh oleh game.

## Aturan yang menggerakkan math

- Papan 40 angka. Calm, Bold, Wild: harga 1×, 10 tarikan, 3, 4, 5, 6, 8 atau 10 angka.
- Chain: harga 10×, 12 tarikan, 10 angka. Chain Max: harga 100×, 12 tarikan, 10 angka.
- Lucky number: angka yang tidak dipilih, ditandai sebelum tarikan. Calm, Bold, Wild, Chain: 1 angka.
  Chain Max: 3 angka. Setiap lucky ball yang tertarik menaikkan meter satu tingkat dan tidak
  memutus rentetan.
- Lucky round: di Calm, Bold, Wild dan Chain, 1 dari 5 ronde menandai 3 lucky number. Ronde mana yang
  menjadi lucky round adalah bagian dari hasil ronde, seperti tarikannya. Chain Max tidak punya
  lucky round.
- Tingkat meter = rentetan terbaik + jumlah lucky ball yang tertarik. Pengali: tingkat 1 ×1, 2 ×2,
  3 ×3, 4 ×5, 5 ×10, 6 ×15, 7 atau lebih ×25.
- Calm/Bold/Wild: rentetan = kena berturut-turut; meleset memutusnya.
- Chain/Chain Max: kena menaikkan rentetan satu, meleset menurunkannya satu (tidak di bawah nol);
  puncaknya yang dipakai.
- Kemenangan tertinggi 100.000× (Chain Max). Tabel bayaran ada di `readme.txt` dan
  `game_config.py`, dicari dengan `design_tables.py`.

## Target dan hasil

Semua angka pasti (jumlah atas seluruh urutan tarikan), diukur dengan `math_audit.py` 2026-11-27.

| Mode | Harga | RTP | Std dev | Ada kemenangan | Menang ≥ harga | Max win | Peluang max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| calm_3 | 1× | 96,625% | 1,99 | 58,9% | 28,5% | 117× | 1 banding 639.730 |
| calm_4 | 1× | 96,553% | 2,81 | 70,0% | 25,7% | 450× | 1 banding 6.797.131 |
| calm_5 | 1× | 96,664% | 3,03 | 78,3% | 36,8% | 750× | 1 banding 3.323.042 |
| calm_6 | 1× | 96,605% | 3,48 | 47,4% | 29,4% | 1.250× | 1 banding 1.965.503 |
| calm_8 | 1× | 96,607% | 3,85 | 65,9% | 31,5% | 1.500× | 1 banding 7.100.920 |
| calm_10 | 1× | 96,568% | 4,24 | 48,5% | 37,3% | 2.500× | 1 banding 4.542.661 |
| bold_3 | 1× | 96,618% | 4,17 | 14,9% | 14,9% | 247,5× | 1 banding 639.730 |
| bold_4 | 1× | 96,610% | 5,74 | 25,6% | 25,6% | 950× | 1 banding 6.797.131 |
| bold_5 | 1× | 96,645% | 7,23 | 36,7% | 21,0% | 2.000× | 1 banding 3.323.042 |
| bold_6 | 1× | 96,683% | 8,45 | 47,4% | 29,4% | 4.000× | 1 banding 1.965.503 |
| bold_8 | 1× | 96,627% | 9,35 | 31,2% | 23,7% | 7.500× | 1 banding 7.100.920 |
| bold_10 | 1× | 96,550% | 12,23 | 19,7% | 19,7% | 10.000× | 1 banding 4.542.661 |
| wild_3 | 1× | 96,662% | 7,67 | 14,9% | 14,9% | 487,5× | 1 banding 639.730 |
| wild_4 | 1× | 96,620% | 13,86 | 25,6% | 13,4% | 2.500× | 1 banding 6.797.131 |
| wild_5 | 1× | 96,641% | 20,24 | 36,7% | 9,1% | 6.250× | 1 banding 3.323.042 |
| wild_6 | 1× | 96,560% | 23,66 | 47,4% | 11,2% | 12.500× | 1 banding 1.965.503 |
| wild_8 | 1× | 96,669% | 36,69 | 31,2% | 9,8% | 50.000× | 1 banding 7.100.920 |
| wild_10 | 1× | 96,548% | 51,91 | 19,7% | 17,9% | 50.000× | 1 banding 4.542.661 |
| chain_10 | 10× | 96,570% | 16,12 | 88,7% | 30,9% | 50.000× | 1 banding 222.685 |
| chainmax_10 | 100× | 96,603% | 7,07 | 64,5% | 26,8% | 100.000× | 1 banding 201.404 |

Setiap mode berisi 100.428 sampai 237.518 buku, semuanya dengan papan angka yang berbeda.

Tiga tingkat berdampingan (std, puncak):

| Angka | Calm | Bold | Wild |
| --- | --- | --- | --- |
| 3 | 2,0 · 117× | 4,2 · 247,5× | 7,7 · 487,5× |
| 4 | 2,8 · 450× | 5,7 · 950× | 13,9 · 2.500× |
| 5 | 3,0 · 750× | 7,2 · 2.000× | 20,2 · 6.250× |
| 6 | 3,5 · 1.250× | 8,5 · 4.000× | 23,7 · 12.500× |
| 8 | 3,9 · 1.500× | 9,4 · 7.500× | 36,7 · 50.000× |
| 10 | 4,2 · 2.500× | 12,2 · 10.000× | 51,9 · 50.000× |

Ke bawah (lebih banyak angka) dan ke kanan (tingkat lebih berani) std selalu naik. Puncak juga,
kecuali Wild 8 dan 10 angka yang sama-sama 50.000×. Sasaran yang disetujui pengguna: Calm 2 · 2,5 ·
3 · 3,5 · 4 · 4,5; Bold 4 · 5,5 · 7 · 8,5 · 10 · 12; Wild 8 · 12 · 20 · 24 · 37 · 52. Tabel
dengan angka bulat meleset paling jauh 1,9 (wild_4) dari sasaran itu.

Bold membayar mulai jumlah kena yang sama dengan Wild (jadi sama seringnya menang), dengan
bayaran yang lebih rata dan puncak di antara Calm dan Wild. Pada 3, 4 dan 10 angka Bold tidak
punya kemenangan di bawah taruhan. Pada 3 angka ketiga tingkat berdekatan (std 2 sampai 7,7):
hasil yang mungkin terlalu sedikit untuk jarak yang lebar.

Meter per jumlah angka (hitungan pasti; sama di Calm, Bold dan Wild):

| Angka dipilih | Meter ×2 atau lebih: ronde biasa | Lucky round | Semua ronde | Pengali tertinggi: ronde biasa | Lucky round |
| --- | --- | --- | --- | --- | --- |
| 3 | 16,6% | 34,9% | 20,2% | ×5 | ×15 |
| 4 | 21,9% | 43,0% | 26,1% | ×10 | ×25 |
| 5 | 27,2% | 49,9% | 31,7% | ×15 | ×25 |
| 6 | 32,5% | 56,0% | 37,2% | ×25 | ×25 |
| 8 | 43,4% | 66,1% | 47,9% | ×25 | ×25 |
| 10 | 54,1% | 74,4% | 58,1% | ×25 | ×25 |

Lucky ball tertarik pada 25,0% ronde biasa, 58,9% lucky round, 31,8% semua ronde. Di Calm
dan Wild, lucky round membawa 24% sampai 26% RTP mode (ronde biasa mengembalikan 89% sampai 92%,
lucky round 114% sampai 123%).

Alasan target:
- RTP 96,5-96,7%: batas atas pita Engine (96,0-96,7%). Keputusan pengguna 2026-11-25.
- Lucky round 1 dari 5. Dengan 4 angka, max win hanya tercapai di lucky round (4 kena
  berturut-turut dan 3 lucky ball), jadi porsinya harus di atas 13,6% supaya max win lebih sering
  dari 1 banding 10 juta (pada 1 dari 10: 1 banding 13,6 juta).
- Setiap mode menang paling jarang 1 banding 6,7 (bold_3 dan wild_3; aturan Engine: tidak lebih jarang dari
  1 banding 50, dan 90% ronde kosong bisa ditolak).
- Std dev setiap mode di bawah 60 (batas kelas risiko); tertinggi wild_10 51,91.
- Max win tercapai lebih sering dari 1 banding 10 juta di setiap mode. Karena itu bayaran 9 dan
  10 kena disamakan pada 10 angka.
- Chain Max berhenti di 100.000× karena itu batas kelas risiko Engine untuk max win.

## Anggaran

RTP sebuah mode = Σ P(kena = h) × bayaran[h] × E[pengali | h] ÷ harga, dijumlah atas semua pola
tarikan (kena, meleset, lucky ball), dengan ronde biasa berbobot 4 dan lucky round berbobot 1. Tabel
bayaran diatur per mode sampai jumlahnya jatuh di 96,5-96,7%; tidak ada pembobotan ulang.
Tabel dicari dengan `design_tables.py`: angka bulat di dalam jendela RTP yang std-nya paling dekat
ke sasaran. Delapan tabel sama dengan v1 (calm_3, calm_4, wild_3, wild_5, wild_6, wild_8, wild_10,
chain_10); dua belas baru.
`design_tables.py --check` mencetak ke-20 tabel dengan angkanya.

## Mode

| Tingkat | Harga | Angka | Yang berubah bagi pemain |
| --- | --- | --- | --- |
| Calm | 1× | 3, 4, 5, 6, 8, 10 | Sering menang kecil, puncak 117-2.500× |
| Bold | 1× | 3, 4, 5, 6, 8, 10 | Di antara keduanya, puncak 247,5-10.000× |
| Wild | 1× | 3, 4, 5, 6, 8, 10 | Jarang, puncak 487,5-50.000× |
| Chain | 10× | 10 | 12 tarikan; meleset hanya menurunkan rentetan satu tingkat |
| Chain Max | 100× | 10 | Seperti Chain dengan 3 lucky number di setiap ronde; puncak 100.000× |

6 + 6 + 6 + 2 = 20 mode (batas Engine 20). Nama mode `<tingkat>_<angka>`: `calm_3` ... `calm_10`,
`bold_3` ... `bold_10`, `wild_3` ... `wild_10`, `chain_10`, `chainmax_10`. Setiap jumlah angka
punya ketiga tingkat, jadi tidak ada aturan "tingkat ini hanya untuk angka sekian". Yang tersisa:
7 dan 9 angka terpilih tidak memulai ronde (pemain menambah satu angka atau menghapus satu).

## Di mana varians berada

Di ekor jumlah kena dikali pengali: pada wild_8, 8 kena membayar 2.000 × pengali, sampai 50.000×.
Pada 3 sampai 5 angka, pengali tertinggi hanya tercapai di lucky round. Tingkat yang dipilih
menentukan seberapa besar ekor itu: pada 8 angka, 8 kena membayar 60× (Calm), 300× (Bold) atau
2.000× (Wild) sebelum pengali.

## Batasan Engine

- Uji kritis: semua lolos (harga termurah 1×, std ≥ 0,6, RTP dalam pita, 20 mode).
- Kelas risiko: 0 gagal. Batas taruhan dasar terbesar yang diizinkan tetap $500 (mode 100× dan
  max win 100.000×).
- Bayaran semua kelipatan 0,1× (uji format SDK: "payout values must be in increments of 10").
- Batas `math_audit.py` dibaca dari halaman math-verification 2026-11-12, dicek sama 2026-11-25.

## Verifikasi

- `verify_books.py`: buku dan tabel lookup cocok di 20 mode; angka tiap buku menunjukkan polanya
  (termasuk lucky number); kemenangan tiap buku dihitung ulang dengan aturan yang ditulis ulang;
  lucky round membawa tepat 1/5 bobot di Calm, Bold, Wild dan Chain, dan nol di Chain Max.
- Dua hitungan pasti yang ditulis terpisah memberi RTP yang sama di 20 mode (selisih terbesar
  3 × 10⁻¹⁶): bobot pola di tabel lookup, dan peluang tarikan bola demi bola.
- Undian sungguhan (angka acak, urutan acak, lucky round acak 1 dari 5; 2-3 juta ronde per mode):
  calm_3 96,47% vs 96,63% (galat baku 0,14); bold_4 96,22% vs 96,61% (0,41); bold_8 96,12% vs
  96,63% (0,54); bold_10 96,35% vs 96,55% (0,71); wild_5 93,84% vs 96,64% (1,17; 2,4 galat baku,
  tabelnya sama dengan high_5 di v1, yang pada 40 juta ronde memberi 96,82%); chain_10 96,93%
  vs 96,57%; chainmax_10 97,07% vs 96,60% (0,50).
- Undian sungguhan kedua, ditulis terpisah dari kode game, 40 juta ronde per mode, dijalankan di
  v1 untuk tabel yang masih dipakai: calm_3 96,62% (pasti 96,63%), wild_3 96,63% (96,66%), wild_5
  96,82% (96,64%), wild_10 96,70% (96,55%), chain_10 96,72% (96,57%). Semua dalam 1 galat baku.
  Belum diulang untuk dua belas tabel baru.
- Server game lokal, 2026-11-27: 40 ronde per mode (800 ronde) lewat `wallet/play`; mode, jumlah
  angka, bayaran tabel dan pengali kemenangan setiap ronde cocok dengan tabel v2.
- Uji format SDK (`utils.rgs_verification`): lolos. Peringatan volatilitasnya untuk dua mode
  premium salah hitung (ETL tidak dibagi harga mode); angka yang benar ada di `math_audit.py`.
- `math_profile.py` terhadap `math_targets.json`: semua target terpenuhi.

## Keputusan dan pertanyaan terbuka

Keputusan pengguna yang berlaku di v2:
- 2026-11-25: keno dengan pengali rentetan; RTP di batas atas pita Engine; dikerjakan sebelum
  Floppy Rabbit.
- 2026-11-26: dua mode premium di 10 angka; lucky number di semua mode, 3 di Chain Max, lucky ball
  tidak memutus rentetan; meleset di Chain menurunkan rentetan satu tingkat; id `chainmax_10`;
  batas taruhan dasar $500; tangga melompat ×15 ke ×25.
- 2026-11-27: lucky round, 1 dari 5 ronde, juga di Chain; nama pemain lucky number, lucky ball,
  lucky round; lucky number selalu ditaruh game; nama game Keno Chain, id math dan folder
  `keno_chain` (sebelumnya `kilara_keno`).
- 2026-11-27: tiga tingkat volatilitas dengan mengorbankan jumlah angka (6 jumlah angka × 3
  tingkat); nama CALM, BOLD, WILD (usul "easy, normal, crazy" tidak dipakai: itu tiga nama pertama
  Keno Xtreme); volatilitas naik per jumlah angka di setiap tingkat.
- 2026-11-27: Chain Max tidak membayar untuk 2 kena, dan bayarannya dipindah ke atas (std 4,93
  menjadi 7,07, ronde menang 88,7% menjadi 64,5%, menang ≥ harga tetap 26,8%). Ia tetap di bawah
  Chain (16,12): puncaknya terkunci di 100.000× taruhan dasar, yaitu 1.000× harganya, jadi "lebih
  mahal = lebih berani" tidak bisa dicapai tanpa menurunkan Chain.

Terbuka dan catatan:
- Template taruhan $500 karena puncak Chain Max 100.000×; $1.000 butuh puncak 50.000×. Saran saya
  tetap $500.
- Label volatilitas Studio (v2): Calm semuanya Low; Bold 3-8 angka Low, 10 angka Medium; Wild 3
  angka Low, 4 angka Medium, 5-6 angka High, 8-10 angka Extreme. Nama tingkat kita relatif di
  dalam game.
- Catatan audit: tangga pengali melompat dari ×15 ke ×25, jadi tiap mode kosong di antara 60% max
  win dan max win; pada calm_10, bold_8, bold_10, wild_8, wild_10 dan chain_10, max win sedikit
  lebih sering daripada rentang setengah max win ke atas (wild_8, wild_10 dan chain_10 sama dengan
  v1, yang lolos pemeriksaan Studio).
- Menang di bawah harga (0 < menang < harga): calm_3 30,4%, calm_4 44,3%, calm_5 41,5%, calm_8
  34,4%, wild_5 27,6%, wild_6 36,2%, chain_10 57,8%, chainmax_10 37,7% ronde. Bold: 0% pada 3, 4
  dan 10 angka, paling banyak 18,0% (bold_6). Jangan dirayakan di frontend.
- Risiko replay (tidak bisa ditutup dari sisi math): RGS hanya memberi mode dan buku. Replay
  menampilkan papan milik buku, termasuk lucky number-nya; urutan, pengali dan kemenangan sama
  dengan ronde aslinya, tetapi angkanya bisa berbeda dari yang dipilih pemain.
