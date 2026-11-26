# Dwanda: desain math

Status: disimulasikan 2026-11-25, 200.000 ronde per mode spin dan 100.000 per mode beli, ditambah
sampel ekor. Belum dilihat pengguna, belum diunggah ke Studio. Nama Dwanda dan tema Phoenix vs
Dragon adalah usulan 17 Nov yang belum dikonfirmasi; papan 7×7 cluster dengan tumble adalah
pilihan pengguna 17 Nov. Semua pilihan math di bawah adalah pilihan lead selama pengguna tidur.

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`.

## Ide dalam angka

Cluster pays 7×7 dengan tumble. Simbol terbagi dua sisi: phoenix (P1–P4, hangat) dan naga
(D1–D4, dingin), membayar sama per peringkat. Yang khas adalah **wilayah**:

- Cluster yang menang menandai selnya untuk sisinya.
- Sel yang sudah ditandai sisi lawan menjadi **sel Clash** ×2. Sel Clash yang dimenangkan lagi
  (sisi mana pun) berlipat dua, sampai ×1.024.
- Cluster dibayar × **jumlah** sel Clash di bawahnya.
- **The Duel** (free spins): wilayah bertahan sepanjang fitur, dan tanda cluster yang menang juga
  menjalar ke sel di sebelahnya. Di sinilah dua sisi benar-benar bertemu.

Multiplier tumbuh di garis depan tempat dua sisi bertemu, bukan di sel acak. Pembanding keluarga
multiplier sel (Engine Players dan Engine Insights, dibaca 16 Nov 2026): Ganja Snail (std dev
27,4, 50.000×), Candy Dash 2 (sel berlipat sampai 4.096×, 49,3), Stoned Pandas (18,3, 20.000×),
dan Floppy Rabbit sendiri (22,8, 25.000×).

## Aturan yang menggerakkan math

- Papan 7×7, cluster 5+ simbol sama bersentuhan sisi, tumble sampai papan berhenti membayar.
- Paytable 5 / 6–8 / 9–12 / 13+: peringkat 1 membayar 5 / 13 / 32 / 80, peringkat 4 membayar
  0,4 / 1 / 3,2 / 8.
- 3/4/5 scatter → 10/12/15 spin; 3+ scatter di The Duel menambah 5.
- Reel base 198 stop (14/20/28/36 stop per peringkat per sisi, scatter 2-2-1-1-1-1-1); reel The
  Duel 199 stop dengan simbol lebih bertumpuk (`clump` 2,0 lawan 1,35) dan scatter 3-3-3-3-2-2-2.
- Batas menang 25.000× di semua mode.

## Target dan terukur

Diukur dari lookup table terbitan, 2026-11-25. Semua target di `math_targets.json` terpenuhi.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine | 96,698% di kelima mode |
| Hit rate base | 29–34% | Angka reel tanpa paksaan: 31,0% | 31,3% |
| The Duel muncul | 1 dari 295–345 | Angka reel: 1 dari 322,9 (6 juta spin) | 1 dari 313,0 |
| Rata-rata menang The Duel | 150–195× | Campuran 3/4/5 scatter | 167,5× |
| RTP base / The Duel | 40–46% / 52–59% porsi | Patokan 59/38 sampai 75/25; fitur di sini lebih berat | 43,2% / 53,5% (porsi 55,3%) |
| Std dev base | 20–58 | Volatil tinggi, di bawah batas Engine 60 | 33,0 |
| Max win dan peluangnya | 25.000×, 1 dari 1–10 juta | Pedoman Engine | 25.000×, 1 dari 3.921.211 |
| Menang di bawah taruhan (dari semua hit) | ≤ 50%, dilaporkan | Tidak ada batas resmi | 45,4% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,514 |
| Beli bonus: balik modal / median / di bawah 10% harga | ≥ 20% / ≥ 0,31× / ≤ 24% | Sesi tanpa paksaan | 22,3% / 0,35× / 21,5% |
| Beli blaze: sama | ≥ 20% / ≥ 0,36× / ≤ 17% | sama | 22,7% / 0,40× / 14,3% |
| Beli eclipse: sama | ≥ 21% / ≥ 0,40× / ≤ 12% | sama | 23,5% / 0,45× / 9,6% |

Frekuensi The Duel adalah satu-satunya angka yang diselesaikan agar RTP tepat: 1 dari 313,0, 3,1%
lebih sering daripada angka reel.

## Anggaran

- Spin base tanpa The Duel: menang 1 dari 3,22, rata-rata 1,39× → 0,432.
- The Duel: 167,5× ÷ 313,0 → 0,535. Jumlah: 0,432 + 0,535 = 0,967.
- Pemicu alami: 95,5% tiga scatter, 4,4% empat, 0,11% lima (6 juta spin, 18.584 pemicu).
  Tumble kadang menjatuhkan scatter tambahan sebelum pemicu dihitung (0,64% papan yang dibuka
  dengan 3 berakhir dengan 4; 360.000 papan paksaan), jadi bobot scatter saat papan pemicu
  dibuka diselesaikan menjadi 96.113 / 3.792 / 95 agar jumlah akhirnya sama dengan permainan
  tanpa paksaan.
- Bonus: 159,8× ÷ 0,967 = 165,2× → harga 160× (−1,5% pada rata-rata).
- Blaze (5 sel Clash ×4): 240,6× ÷ 0,967 = 248,8× → harga 250× (+0,5%).
- Eclipse (9 sel Clash ×8): 481,6× ÷ 0,967 = 498,0× → harga 500× (+0,4%).
- Ante 3×: The Duel 1 dari 67,8 (4,6× lebih sering).

## Mode

| Mode | Harga | Yang berubah bagi pemain | RTP | Balik modal | Median | Di bawah 10% harga | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | 96,698% | 17,1% | 0 | — | 1 dari 3.921.211 |
| ante | 3× | The Duel sekitar 4,6× lebih sering | 96,698% | 4,3% | 0 | — | 1 dari 849.038 |
| bonus | 160× | Langsung The Duel, 10 spin | 96,698% | 22,3% | 0,35× harga | 21,5% | 1 dari 15.627 |
| blaze | 250× | The Duel dengan 5 sel Clash ×4 | 96,698% | 22,7% | 0,40× harga | 14,3% | 1 dari 9.829 |
| eclipse | 500× | The Duel dengan 9 sel Clash ×8 | 96,698% | 23,5% | 0,45× harga | 9,6% | 1 dari 3.192 |

Buku mode ante sama dengan buku mode base; yang berbeda hanya bobotnya.

## Di mana varians tinggal

Di garis depan wilayah selama The Duel. Sesi bonus rata-rata memainkan 11,5 spin dengan 8,2
cascade menang, dan membuat 27 sel Clash (sesi tanpa paksaan, 36.000 sesi). Sel Clash terbesar
di akhir sesi bonus: ×8 26,7%, ×16 22,1%, ×32 13,1%, ×64 6,4%, ×128 2,9%, ×256 1,1%, ×512 0,5%,
×1.024 0,4%. Karena cluster dibayar × jumlah sel Clash di bawahnya, cluster besar yang menutup
garis depan membawa ekor.

Di base, 9,7% kemenangan sempat membuat sel Clash (teaser): dua sisi bertemu di cascade yang sama.

Ekor mode base, tanpa celah:

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 8.326 | 8,4% |
| 1.000–2.000× | 1 dari 20.524 | 6,9% |
| 2.000–5.000× | 1 dari 55.364 | 5,5% |
| 5.000–10.000× | 1 dari 265.258 | 2,6% |
| 10.000–25.000× | 1 dari 518.321 | 3,1% |
| di antaranya tepat 25.000× | 1 dari 3.921.211 | 0,6% |

Tidak ada ronde yang dipaksa ke max win; buku ekor dari sampel `freegame_tail` (≥ 2.000× di base
dan bonus, ≥ 4.000× di blaze, ≥ 6.000× di eclipse) dengan bobot = diterima ÷ dicoba.

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca 12 Nov 2026).

- Tes kritis: semua lolos (mode termurah 1×, std dev base 33,0, RTP 96,698% di semua mode, max win
  25.000×, harga tertinggi 500×, 5 mode).
- Kelas risiko: **0 dari 6 gagal**. ETL > 40× tertinggi 0,688 (ante) dari 0,9; peluang ≥ 10.000×
  tertinggi 0,24% (eclipse) dari 1%; ≥ 25.000× 0,03% dari 0,5%.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000; taruhan dasar terbesar $1.000,
  jadi template $1.000 terpakai penuh.
- Tes format SDK: hash buku dan payout cocok di kelima mode.
- Aturan diputar ulang terpisah dari kode game (`verify_books.py`, pencarian cluster sendiri,
  wilayah diputar ulang menang demi menang). Pemeriksa diuji dengan dua aturan yang sengaja
  disalahkan (tanpa jalaran di The Duel; sel Clash baru ×3) dan menangkap keduanya. Pemeriksaan
  penuh: 699.972 buku di kelima mode, semuanya mengikuti `readme.txt`.

## Keputusan dan pertanyaan terbuka

Keputusan pengguna: 17 Nov 2026, cluster pays 7×7 dengan tumble dan wilayah dua sisi. Pilihan lead
(2026-11-25, pengguna tidur):

1. **Multiplier = jumlah sel Clash di bawah cluster**, bukan "total phoenix × total naga" dari
   konsep 17 Nov. Perkalian dua meter tumbuh kuadrat dan sulit dibaca di layar; sel Clash membuat
   pertemuan dua sisi terlihat di sel tempat ia terjadi.
2. **Satu jenis free spins (The Duel)**, bukan tiga (Phoenix, Dragon, Clash Spins). Dua sisi
   membayar sama, jadi Phoenix Spins dan Dragon Spins akan sama persis secara math; tangga mode
   beli (blaze, eclipse) mengambil peran "Clash Spins".
3. **Jalaran di The Duel.** Tanpa itu sesi bonus hanya bernilai 5,5× (wilayah jarang bertemu,
   0,35 cascade menang per spin); dengan jalaran dan reel The Duel yang lebih bertumpuk, 160×.
4. **Papan tetap 7×7** (pilihan pengguna), walau Floppy Rabbit juga 7×7. Usulan 6×6 atau 8×8
   menunggu pengguna.
5. **Harga mengikuti nilai**: bonus 160×, blaze 250×, eclipse 500×; ante 3×.
6. Bobot alami, bukan optimizer Rust. Reel dari tumpukan simbol berjumlah pasti dan seed tetap
   (`reels/make_reels.py`, cara Floppy Rabbit).

Risiko yang diterima atau masih terbuka:

1. **Bonus 160×**, di atas 100× yang lazim. Menurunkannya berarti The Duel yang lebih lemah dan base
   yang lebih berat, atau spin yang lebih sedikit.
2. **Pembelian bonus: 21,5% kembali di bawah sepersepuluh harga.**
3. **Dua game cluster 7×7 berurutan** (Floppy Rabbit, Dwanda) bisa terasa berulang di lobby.
4. **Nama dan tema belum dikonfirmasi** dan belum dicek di Engine.
5. Belum diunggah ke Studio; belum di-commit.
