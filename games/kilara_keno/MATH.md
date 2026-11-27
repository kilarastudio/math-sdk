# Kilara Keno (nama sementara): desain math

Status: versi 3, dihitung pasti 2026-11-27 (enumerasi penuh, bukan simulasi). Disetujui pengguna
2026-11-27, termasuk tiga pilihan saya di bawah ("ikuti saran kamu"). Belum diunggah. Versi 2
(commit 57a870f): tanpa lucky round, High mulai 2 angka.

Nama untuk pemain, diputuskan pengguna 2026-11-27 ("ganti dengan lucky number saja"): lucky
number, lucky ball, lucky round. Nama lamanya Kilau masih dipakai di kode dan di event buku
(`kilau`, `kilauRound`, `kilauHits`). Kata "lucky" tidak ada di daftar frasa terlarang Engine.

## Ide dalam angka

Keno papan 40 angka. Pemain memilih 1 sampai 10 angka dan satu tingkat sebelum ronde. Angka yang
tidak dipilih ditandai sebagai lucky number: biasanya 1, dan pada 1 dari 5 ronde (lucky round) 3.
Angka ditarik satu per satu; kemenangan = bayaran untuk jumlah kena × pengali meter. Meter naik
lewat kena berturut-turut dan lewat lucky ball, jadi urutan tarikan ikut menentukan hasil.

Versi 3 menjawab batas 20 mode (Engine Support 2026-11-27: studio eksternal tidak boleh lebih).
Menu tidak bisa dilebarkan, jadi yang ditambah adalah isi ronde dan satu jumlah angka:

1. Lucky round: rasa mode premium (3 lucky number) muncul acak di Low, High dan Chain, tanpa
   memakai slot mode. Chain Max adalah versi yang dibeli: 3 lucky number di setiap ronde.
2. `high_2` diganti `low_1`: 1 sampai 10 angka semuanya bisa dimainkan.

Lucky number selalu ditaruh oleh game. Pilihan "pemain menaruh lucky number sendiri" sempat
dibangun di frontend dan dihapus pengguna pada hari yang sama (2026-11-27, "iya hapus"): terasa
janggal, tidak dikenal dari keno lain, dan tidak mengubah peluang.

## Aturan yang menggerakkan math

- Papan 40 angka. Low: harga 1×, 10 tarikan, 1 sampai 10 angka. High: harga 1×, 10 tarikan, 3
  sampai 10 angka. Satu dan dua angka hanya punya satu tabel (Low).
- Chain: harga 10×, 12 tarikan, 10 angka. Chain Max: harga 100×, 12 tarikan, 10 angka.
- Lucky number: angka yang tidak dipilih, ditandai sebelum tarikan. Low, High, Chain: 1 angka.
  Chain Max: 3 angka. Setiap lucky ball yang tertarik menaikkan meter satu tingkat dan tidak
  memutus rentetan.
- Lucky round: di Low, High dan Chain, 1 dari 5 ronde menandai 3 lucky number. Ronde mana yang
  menjadi lucky round adalah bagian dari hasil ronde, seperti tarikannya. Chain Max tidak punya
  lucky round.
- Tingkat meter = rentetan terbaik + jumlah lucky ball yang tertarik. Pengali: tingkat 1 ×1, 2 ×2,
  3 ×3, 4 ×5, 5 ×10, 6 ×15, 7 atau lebih ×25.
- Low/High: rentetan = kena berturut-turut; meleset memutusnya.
- Chain/Chain Max: kena menaikkan rentetan satu, meleset menurunkannya satu (tidak di bawah nol);
  puncaknya yang dipakai.
- Kemenangan tertinggi 100.000× (Chain Max). Tabel bayaran ada di `readme.txt` dan
  `game_config.py`, dicari dengan `design_tables.py`.

## Target dan hasil

Semua angka pasti (jumlah atas seluruh urutan tarikan), diukur dengan `math_audit.py` 2026-11-27.

| Mode | Harga | RTP | Std dev | Ada kemenangan | Menang ≥ harga | Max win | Peluang max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_1 | 1× | 96,056% | 1,84 | 25,0% | 25,0% | 14,5× | 1 banding 2.176 |
| low_2 | 1× | 96,569% | 2,05 | 44,2% | 44,2% | 52× | 1 banding 45.695 |
| low_3 | 1× | 96,625% | 1,99 | 58,9% | 28,5% | 117× | 1 banding 639.730 |
| low_4 | 1× | 96,553% | 2,81 | 70,0% | 25,7% | 450× | 1 banding 6.797.131 |
| low_5 | 1× | 96,682% | 4,44 | 78,3% | 36,8% | 1.250× | 1 banding 3.323.042 |
| low_6 | 1× | 96,614% | 3,02 | 47,4% | 29,4% | 750× | 1 banding 1.965.503 |
| low_7 | 1× | 96,674% | 2,49 | 57,2% | 38,2% | 750× | 1 banding 2.511.711 |
| low_8 | 1× | 96,656% | 2,54 | 65,9% | 31,5% | 500× | 1 banding 7.100.920 |
| low_9 | 1× | 96,645% | 2,56 | 73,4% | 31,6% | 500× | 1 banding 821.504 |
| low_10 | 1× | 96,566% | 3,29 | 48,5% | 37,3% | 500× | 1 banding 4.542.661 |
| high_3 | 1× | 96,662% | 7,67 | 14,9% | 14,9% | 487,5× | 1 banding 639.730 |
| high_4 | 1× | 96,644% | 6,35 | 25,6% | 13,4% | 1.000× | 1 banding 6.797.131 |
| high_5 | 1× | 96,641% | 20,24 | 36,7% | 9,1% | 6.250× | 1 banding 3.323.042 |
| high_6 | 1× | 96,560% | 23,66 | 47,4% | 11,2% | 12.500× | 1 banding 1.965.503 |
| high_7 | 1× | 96,614% | 27,81 | 22,8% | 16,9% | 25.000× | 1 banding 2.511.711 |
| high_8 | 1× | 96,669% | 36,69 | 31,2% | 9,8% | 50.000× | 1 banding 7.100.920 |
| high_9 | 1× | 96,590% | 53,54 | 39,9% | 12,5% | 37.500× | 1 banding 821.504 |
| high_10 | 1× | 96,548% | 51,91 | 19,7% | 17,9% | 50.000× | 1 banding 4.542.661 |
| chain_10 | 10× | 96,570% | 16,12 | 88,7% | 30,9% | 50.000× | 1 banding 222.685 |
| chainmax_10 | 100× | 96,694% | 4,93 | 88,7% | 26,9% | 100.000× | 1 banding 201.404 |

Setiap mode berisi 100.428 sampai 237.518 buku, semuanya dengan papan angka yang berbeda.

Yang berubah bagi pemain dibanding versi 2 (hitungan pasti):

| Angka dipilih | Meter ×2 atau lebih: ronde biasa | Lucky round | Semua ronde | Pengali tertinggi: ronde biasa | Lucky round |
| --- | --- | --- | --- | --- | --- |
| 1 | 5,8% | 13,9% | 7,4% | ×2 | ×5 |
| 2 | 11,2% | 25,4% | 14,1% | ×3 | ×10 |
| 3 | 16,6% | 34,9% | 20,2% | ×5 | ×15 |
| 4 | 21,9% | 43,0% | 26,1% | ×10 | ×25 |
| 5 | 27,2% | 49,9% | 31,7% | ×15 | ×25 |
| 6 | 32,5% | 56,0% | 37,2% | ×25 | ×25 |
| 8 | 43,4% | 66,1% | 47,9% | ×25 | ×25 |
| 10 | 54,1% | 74,4% | 58,1% | ×25 | ×25 |

Lucky ball tertarik pada 25,0% ronde biasa, 58,9% lucky round, 31,8% semua ronde. Di Low dan
High, lucky round membawa 24% sampai 26% RTP mode (ronde biasa mengembalikan 89% sampai 92%,
lucky round 114% sampai 123%).

Alasan target:
- RTP 96,5-96,7%: batas atas pita Engine (96,0-96,7%). Keputusan pengguna 2026-11-25.
  Pengecualian: `low_1` 96,056%. Satu angka hanya punya satu bayaran, dan Engine mewajibkan
  bayaran kelipatan 0,1× (uji format SDK), jadi RTP-nya bergerak dalam langkah sekitar 3,3 poin:
  2,9× memberi 96,06%, 3,0× memberi 99,4%. Masih di dalam pita Engine.
- Lucky round 1 dari 5. Dua batas menentukannya. Dengan 4 angka, max win hanya tercapai di lucky
  round (4 kena berturut-turut dan 3 lucky ball), jadi porsinya harus di atas 13,6% supaya max win
  lebih sering dari 1 banding 10 juta (pada 1 dari 10: 1 banding 13,6 juta). Dan `low_1` hanya
  masuk pita Engine pada porsi 10,5-12,5% atau 19,8-21,9%. 1 dari 5 adalah satu-satunya porsi
  bulat yang memenuhi keduanya.
- Setiap mode menang paling jarang 1 banding 6,7 (high_3; aturan Engine: tidak lebih jarang dari
  1 banding 50, dan 90% ronde kosong bisa ditolak).
- Std dev setiap mode di bawah 60 (batas kelas risiko); tertinggi high_9 53,54.
- Max win tercapai lebih sering dari 1 banding 10 juta di setiap mode. Karena itu bayaran dua
  jumlah kena teratas disamakan pada 9 dan 10 angka.
- Chain Max berhenti di 100.000× karena itu batas kelas risiko Engine untuk max win.

## Anggaran

RTP sebuah mode = Σ P(kena = h) × bayaran[h] × E[pengali | h] ÷ harga, dijumlah atas semua pola
tarikan (kena, meleset, lucky ball), dengan ronde biasa berbobot 4 dan lucky round berbobot 1. Tabel
bayaran diatur per mode sampai jumlahnya jatuh di 96,5-96,7%; tidak ada pembobotan ulang. Tabel
versi 3 berangkat dari tabel versi 2 yang ditipiskan merata sekitar 6% untuk memberi tempat bagi
lucky round, lalu dibulatkan; dipilih dari keluaran `design_tables.py --list`. Tabel Chain Max
tidak berubah.

## Mode

| Tingkat | Harga | Angka | Yang berubah bagi pemain |
| --- | --- | --- | --- |
| Low | 1× | 1-10 | Sering menang kecil, puncak 14,5-1.250× |
| High | 1× | 3-10 | Jarang, puncak 487,5-50.000× |
| Chain | 10× | 10 | 12 tarikan; meleset hanya menurunkan rentetan satu tingkat |
| Chain Max | 100× | 10 | Seperti Chain dengan 3 lucky number di setiap ronde; puncak 100.000× |

10 + 8 + 2 = 20 mode (batas Engine 20). Nama mode `<tingkat>_<angka>`: `low_1` ... `low_10`,
`high_3` ... `high_10`, `chain_10`, `chainmax_10`. `high_2` dihapus: pada 2 angka, Low dan High
punya peluang yang sama di setiap hasil dan hanya nilainya berbeda.

## Di mana varians berada

Di ekor jumlah kena dikali pengali: pada high_8, 8 kena membayar 2.000 × pengali, sampai 50.000×.
Pada 1 sampai 5 angka, pengali tertinggi hanya tercapai di lucky round, jadi puncak mode-mode itu
naik dibanding versi 2 (high_3 175× menjadi 487,5×, high_4 500× menjadi 1.000×, high_5 3.750×
menjadi 6.250×).

## Batasan Engine

- Uji kritis: semua lolos (harga termurah 1×, std ≥ 0,6, RTP dalam pita, 20 mode).
- Kelas risiko: 0 gagal. Batas taruhan dasar terbesar yang diizinkan tetap $500 (mode 100× dan
  max win 100.000×).
- Bayaran semua kelipatan 0,1× (uji format SDK: "payout values must be in increments of 10").
- Batas `math_audit.py` dibaca dari halaman math-verification 2026-11-12, dicek sama 2026-11-25.

## Verifikasi

- `verify_books.py`: buku dan tabel lookup cocok di 20 mode; angka tiap buku menunjukkan polanya
  (termasuk lucky number); kemenangan tiap buku dihitung ulang dengan aturan yang ditulis ulang;
  lucky round membawa tepat 1/5 bobot di Low, High dan Chain, dan nol di Chain Max.
- Dua hitungan pasti yang ditulis terpisah memberi RTP yang sama di 20 mode (selisih terbesar
  3 × 10⁻¹⁶): bobot pola di tabel lookup, dan peluang tarikan bola demi bola.
- Undian sungguhan (angka acak, urutan acak, lucky round acak 1 dari 5; 2-3 juta ronde per mode):
  low_1 95,80% vs 96,06% (tiga benih lain, 3 juta ronde masing-masing: 96,07%, 95,96%, 96,14%);
  low_2 96,77% vs 96,57%; low_8 96,67% vs 96,66%; high_5 95,95% vs 96,64% (galat baku 1,2);
  chain_10 96,59% vs 96,57%; chainmax_10 96,19% vs 96,69% (galat baku 0,35).
- Undian sungguhan kedua, ditulis terpisah dari kode game, 40 juta ronde per mode: low_3 96,62%
  (pasti 96,63%), low_5 96,74% (96,68%), low_10 96,58% (96,57%), high_3 96,63% (96,66%), high_4
  96,66% (96,64%), high_5 96,82% (96,64%), high_10 96,70% (96,55%), chain_10 96,72% (96,57%).
  Semua dalam 1 galat baku; lucky round muncul pada 19,98% sampai 20,01% ronde.
- Uji format SDK (`utils.rgs_verification`): lolos. Peringatan volatilitasnya untuk dua mode
  premium salah hitung (ETL tidak dibagi harga mode); angka yang benar ada di `math_audit.py`.
- `math_profile.py` terhadap `math_targets.json`: semua target terpenuhi.

## Keputusan dan pertanyaan terbuka

- Diputuskan pengguna 2026-11-25: keno dengan pengali rentetan; RTP 96,7%; dikerjakan sebelum
  Floppy Rabbit.
- Disetujui pengguna 2026-11-26 (versi 2): dua mode premium di 10 angka; lucky number di semua mode,
  3 di Chain Max, lucky ball tidak memutus rentetan; meleset di Chain menurunkan rentetan satu
  tingkat; nama `chainmax_10` / CHAIN MAX; batas taruhan dasar $500; tangga melompat ×15 ke ×25.
- Disetujui pengguna 2026-11-27: lucky round di Low dan High, `high_2` ditukar mode 1 angka.
  Pemain menaruh lucky number sendiri: disetujui lalu dihapus pada hari yang sama.
- Pilihan saya, diterima pengguna 2026-11-27 ("ikuti saran kamu"):
  1. Porsi lucky round 1 dari 5 (usul awal saya "misalnya 1 dari 10"; alasannya di atas).
  2. Chain juga punya lucky round (usul awal hanya Low dan High), supaya mode 10× tidak punya
     lebih sedikit lucky number daripada mode 1×.
  3. `low_1` di 96,06% (usul awal saya menyebut 3,14×, yang ternyata bukan kelipatan 0,1×).
     Pilihan lain: tanpa mode 1 angka (kembalikan `high_2`), atau porsi lucky round 21,5% yang
     membawa `low_1` ke 96,57% tetapi membuat `low_2` tidak lagi mengembalikan taruhan pada 1 kena.
- Belum diputuskan: nama game.
- Sisa catatan audit (sama jenisnya dengan versi 2): tangga pengali melompat dari ×15 ke ×25, jadi
  tiap mode kosong di antara 60% max win dan max win; pada low_9, high_8, high_9, high_10 dan dua
  mode premium, max win sedikit lebih sering daripada rentang setengah max win ke atas.
- Menang di bawah harga (0 < menang < harga): low_3 sekarang 30,4% ronde (versi 2: 0%), karena 1
  kena membayar 0,8× dan bukan 1×. Mode lain hampir sama dengan versi 2 (low_4 44,3%, low_5
  41,5%, chain_10 57,8%). Jangan dirayakan di frontend.
- Risiko replay (tidak bisa ditutup dari sisi math): RGS hanya memberi mode dan buku. Replay
  menampilkan papan milik buku, termasuk lucky number-nya; urutan, pengali dan kemenangan sama
  dengan ronde aslinya, tetapi angkanya bisa berbeda dari yang dipilih pemain.
