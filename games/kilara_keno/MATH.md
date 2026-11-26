# Kilara Keno (nama sementara): desain math

Status: versi 2, dihitung pasti 2026-11-26 (enumerasi penuh, bukan simulasi), disetujui pengguna
2026-11-26. Belum diunggah. Versi 1 (16 mode, tanpa angka Kilau) tersimpan di `../kilara_keno_v1_src.tar.gz`.

## Ide dalam angka

Keno papan 40 angka. Pemain memilih 2 sampai 10 angka dan satu tingkat sebelum ronde. Satu angka
yang tidak dipilih ditandai sebagai angka Kilau. Angka ditarik satu per satu; kemenangan = bayaran
untuk jumlah kena × pengali meter. Meter naik lewat kena berturut-turut dan lewat bola Kilau, jadi
urutan tarikan ikut menentukan hasil.

Versi 2 dibuat untuk menutup tiga jarak terhadap Keno Xtreme (Degen Lab; RTP 96,0%, sampai
100.000×, 5 tingkat risiko, mode 10× dan 100×; Engine Insights 2026-11-15) di dalam batas 20 mode:
pilihan jumlah angka (dulu 4, sekarang 9), tingkat premium 100× dengan 100.000×, dan pengali yang
terlihat pada pilihan kecil. Dasarnya ada di `reports/Depth gameplay keno.md`.

## Aturan yang menggerakkan math

- Papan 40 angka. Low dan High: harga 1×, 10 tarikan, 2 sampai 10 angka.
- Chain: harga 10×, 12 tarikan, 10 angka. Chain Max: harga 100×, 12 tarikan, 10 angka.
- Angka Kilau: angka yang tidak dipilih, ditandai sebelum tarikan. Low, High, Chain: 1 angka.
  Chain Max: 3 angka. Setiap bola Kilau yang tertarik menaikkan meter satu tingkat dan tidak
  memutus rentetan.
- Tingkat meter = rentetan terbaik + jumlah bola Kilau yang tertarik. Pengali: tingkat 1 ×1, 2 ×2,
  3 ×3, 4 ×5, 5 ×10, 6 ×15, 7 atau lebih ×25.
- Low/High: rentetan = kena berturut-turut; meleset memutusnya.
- Chain/Chain Max: kena menaikkan rentetan satu, meleset menurunkannya satu (tidak di bawah nol);
  puncaknya yang dipakai.
- Kemenangan tertinggi 100.000× (Chain Max). Tabel bayaran ada di `readme.txt` dan
  `game_config.py`, dicari dengan `design_tables.py`.

## Target dan hasil

Semua angka pasti (jumlah atas seluruh urutan tarikan), diukur dengan `math_audit.py` 2026-11-26.

| Mode | Harga | RTP | Std dev | Ada kemenangan | Menang ≥ harga | Max win | Peluang max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_2 | 1× | 96,559% | 2,14 | 44,2% | 44,2% | 18× | 1 banding 370,5 |
| low_3 | 1× | 96,582% | 1,92 | 58,9% | 58,9% | 42× | 1 banding 5.222,3 |
| low_4 | 1× | 96,621% | 2,44 | 70,0% | 25,6% | 150× | 1 banding 54.834,0 |
| low_5 | 1× | 96,637% | 4,33 | 78,3% | 36,7% | 750× | 1 banding 460.605,6 |
| low_6 | 1× | 96,620% | 2,86 | 47,4% | 27,7% | 1.000× | 1 banding 3.262.623,0 |
| low_7 | 1× | 96,687% | 2,67 | 57,2% | 36,4% | 1.000× | 1 banding 2.929.702,3 |
| low_8 | 1× | 96,572% | 2,51 | 65,9% | 23,1% | 500× | 1 banding 7.457.424,0 |
| low_9 | 1× | 96,552% | 2,85 | 73,4% | 30,4% | 500× | 1 banding 863.198,1 |
| low_10 | 1× | 96,542% | 3,34 | 48,5% | 36,2% | 500× | 1 banding 4.581.948,8 |
| high_2 | 1× | 96,592% | 3,37 | 44,2% | 5,8% | 28× | 1 banding 370,5 |
| high_3 | 1× | 96,682% | 7,62 | 14,9% | 14,9% | 175× | 1 banding 5.222,3 |
| high_4 | 1× | 96,653% | 6,98 | 25,6% | 12,3% | 500× | 1 banding 54.834,0 |
| high_5 | 1× | 96,632% | 18,77 | 36,7% | 10,3% | 3.750× | 1 banding 460.605,6 |
| high_6 | 1× | 96,543% | 22,61 | 47,4% | 15,3% | 12.500× | 1 banding 3.262.623,0 |
| high_7 | 1× | 96,590% | 26,73 | 22,8% | 16,3% | 25.000× | 1 banding 2.929.702,3 |
| high_8 | 1× | 96,559% | 35,83 | 31,2% | 9,3% | 50.000× | 1 banding 7.457.424,0 |
| high_9 | 1× | 96,620% | 51,96 | 39,9% | 12,8% | 37.500× | 1 banding 863.198,1 |
| high_10 | 1× | 96,686% | 51,75 | 19,7% | 17,7% | 50.000× | 1 banding 4.581.948,8 |
| chain_10 | 10× | 96,556% | 15,80 | 88,7% | 29,6% | 50.000× | 1 banding 228.726,5 |
| chainmax_10 | 100× | 96,694% | 4,93 | 88,7% | 26,9% | 100.000× | 1 banding 201.403,9 |

Setiap mode berisi 100.104 sampai 208.871 buku, semuanya dengan papan angka yang berbeda.

Seberapa sering meter terlihat (ronde dengan minimal satu kena dan pengali ×2 atau lebih; simulasi
400.000 ronde per jumlah angka, 10 tarikan): 2 angka 11,3% (tanpa Kilau 1,2%), 3 angka 16,6%
(3,4%), 5 angka 27,2% (10,6%), 8 angka 43,5% (26,6%), 10 angka 54,0% (38,7%).

Alasan target:
- RTP 96,5-96,7%: batas atas pita Engine (96,0-96,7%). Keputusan pengguna 2026-11-25.
- Setiap mode menang paling jarang 1 banding 6,7 (high_3; aturan Engine: tidak lebih jarang dari
  1 banding 50, dan 90% ronde kosong bisa ditolak).
- Std dev setiap mode di bawah 60 (batas kelas risiko). high_9 membayar 1.500 untuk 8 dan 9 kena,
  bukan 2.000: dengan 2.000 std dev-nya 68.
- Max win tercapai lebih sering dari 1 banding 10 juta di setiap mode. Karena itu bayaran dua
  jumlah kena teratas disamakan pada 9 dan 10 angka.
- Chain Max berhenti di 100.000× karena itu batas kelas risiko Engine untuk max win.

## Anggaran

RTP sebuah mode = Σ P(kena = h) × bayaran[h] × E[pengali | h] ÷ harga, dijumlah atas semua pola
tarikan (kena, meleset, Kilau). Tabel bayaran diatur per mode sampai jumlahnya jatuh di
96,5-96,7%; tidak ada pembobotan ulang. Harga 10× dan 100× tepat karena tabelnya disusun untuk
nilai rata-rata 9,66× dan 96,69×, bukan bobotnya yang digeser.

## Mode

| Tingkat | Harga | Angka | Yang berubah bagi pemain |
| --- | --- | --- | --- |
| Low | 1× | 2-10 | Sering menang kecil, puncak 18-1.000× |
| High | 1× | 2-10 | Jarang, puncak 28-50.000× |
| Chain | 10× | 10 | 12 tarikan; meleset hanya menurunkan rentetan satu tingkat |
| Chain Max | 100× | 10 | Seperti Chain dengan 3 angka Kilau; puncak 100.000× |

9 × 2 + 2 = 20 mode (batas Engine 20). Nama mode `<tingkat>_<angka>`: `low_2` ... `high_10`,
`chain_10`, `chainmax_10`. Tingkat Mid dan Chain untuk 3, 5, 8 angka dihapus untuk memberi tempat.

## Di mana varians berada

Di ekor jumlah kena dikali pengali: pada high_8, 8 kena membayar 2.000 × pengali, sampai 50.000×.
Bola Kilau menaikkan pengali satu tingkat, sehingga tingkat 7 (×25) tercapai dengan rentetan 6.

## Batasan Engine

- Uji kritis: semua lolos (harga termurah 1×, std ≥ 0,6, RTP dalam pita, 20 mode).
- Kelas risiko: 0 gagal. Batas taruhan dasar terbesar yang diizinkan turun dari $1.000 ke $500,
  karena mode 100× dan max win 100.000×.
- Batas `math_audit.py` dibaca dari halaman math-verification 2026-11-12, dicek sama 2026-11-25.

## Verifikasi

- `verify_books.py`: buku dan tabel lookup cocok di 20 mode; angka tiap buku menunjukkan polanya
  (termasuk angka Kilau); kemenangan tiap buku dihitung ulang dengan aturan yang ditulis ulang.
- Undian sungguhan (angka acak, urutan acak, 2 juta ronde per mode): low_2 96,48% vs 96,56%;
  high_5 97,48% vs 96,63% (galat baku 1,33); chain_10 95,78% vs 96,56% (galat baku 1,1);
  chainmax_10 97,11% vs 96,69% (galat baku 0,35); low_8 97,07% vs 96,57% pada satu benih, dan
  96,43%, 96,64%, 96,61% pada tiga benih lain (3 juta ronde masing-masing, galat baku 0,14).

## Keputusan dan pertanyaan terbuka

- Diputuskan pengguna 2026-11-25: keno dengan pengali rentetan; RTP 96,7%; dikerjakan sebelum
  Floppy Rabbit.
- Disetujui pengguna 2026-11-26: 9 jumlah angka × 2 tingkat dengan dua mode premium di 10 angka;
  angka Kilau di semua mode, 3 di Chain Max, dan bola Kilau tidak memutus rentetan; meleset di
  Chain menurunkan rentetan satu tingkat (kalimat lama, "meleset tidak menurunkan pengali",
  membuat Chain hanya bergantung pada jumlah kena; pengali yang sudah tercapai tetap tidak pernah
  turun, dan meter menampilkannya begitu); nama `chainmax_10` / CHAIN MAX.
- Diterima pengguna 2026-11-26: batas taruhan dasar $500, high_9 berpuncak 37.500×, dan tangga
  pengali tetap melompat dari ×15 ke ×25 (menambah ×20 membuat max win lebih jarang).
- Belum diputuskan: nama game.
- Celah chain_10 antara 7.500× dan 30.000× ditutup: 8 kena sekarang membayar 500 × pengali
  (sampai 12.500×).
- Sisa catatan audit: tangga pengali melompat dari ×15 ke ×25, jadi tiap mode kosong di antara
  60% max win dan max win; pada low_9 dan high_8 max win sedikit lebih sering daripada rentang
  setengah max win ke atas; high_5 kosong di 100-200×.
- Risiko replay (tidak bisa ditutup dari sisi math): RGS hanya memberi mode dan buku. Replay
  menampilkan papan milik buku, termasuk angka Kilau-nya; urutan, pengali dan kemenangan sama
  dengan ronde aslinya, tetapi angkanya bisa berbeda dari yang dipilih pemain.
- Belum diketahui: cara Keno Xtreme memuat 10 jumlah angka × 5 tingkat dalam 20 mode.
