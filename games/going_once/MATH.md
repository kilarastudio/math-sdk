# Going Once: desain math

Status: disimulasikan 2026-11-25, 300.000 ronde per mode spin dan 100.000 per mode beli. Belum dilihat pengguna, belum diunggah ke
Studio. Semua pilihan di bawah adalah pilihan lead selama pengguna tidur.

Aturan lengkap ada di `readme.txt`. Target yang dibaca mesin ada di `math_targets.json`.

## Ide dalam angka

Video slot lines 5×3, 20 line, dengan bonus hold & win bertema rumah lelang. Lelang berjalan
sendiri dari awal sampai palu diketuk: **tidak ada pilihan pemain**. Pedoman Engine melarang
continuation dan early cashout, dan RGS tidak punya jalan untuk pilihan yang mengubah hasil
(roadmap, revisi 24 Nov 2026).

- **Lot** membawa nilai 1–50× taruhan. 6 Lot atau lebih di papan base membuka lelang.
- Lelang: Lot lengket, 3 respin, apa pun yang mendarat mengisi ulang respin ("going once, going
  twice, sold").
- **Buyer** menjadi Lot senilai semua Lot lain di reelnya.
- **Gavel** menggandakan semua Lot di papan.
- **Last Bid**: saat palu diketuk, penawaran terakhir mengalikan total ×1 sampai ×100
  (ditentukan buku).
- **Full House**: 15 Lot menggandakan total.
- Teaser base: Gavel di reel 3 menggandakan menang line spin itu.

Menang besar datang dari Gavel yang jatuh di papan yang sudah penuh Lot, dan dari Last Bid tinggi.
Last Bid membawa ekor tanpa menambah aturan di dalam lelang.

Kelas volatilitas: tinggi. Pembanding hold & win di Engine (laporan ide 16 Nov 2026): Odins Vault
(nomor 2, 500.000×), Bank Basher 2 Vegas (20.000×), Deal with the Devil (66.666×).

## Aturan yang menggerakkan math

- Papan 5×3, 20 line, 3/4/5 sejenis dari kiri. Wild di reel 2–4, Gavel base di reel 3.
- Paytable per line: H1 3 / 12 / 45 sampai L4 0,3 / 0,8 / 3 (kelipatan 0,1).
- Reel base 101 stop; Lot 12 atau 13 per reel (reel 2 dan 4 punya 13), boleh bertumpuk sampai tiga.
- Respin: setiap sel kosong menarik Lot 6,0%, Gavel 1,2%, Buyer 0,8%, kosong 92,0%.
- Nilai Lot (bobot): 1× 41,7%, 2× 26,0%, 3× 15,6%, 5× 10,4%, 10× 5,2%, 25× 1,3%, 50× 0,3%.
- Last Bid (bobot): ×1 70,0%, ×2 18,0%, ×3 6,0%, ×5 3,5%, ×10 1,5%, ×25 0,6%, ×50 0,3%, ×100 0,1%.
- Batas menang 25.000× di semua mode.

## Target dan terukur

Diukur dari lookup table terbitan, 2026-11-25. Sampel: 300.000 ronde (base, ante) dan 100.000 per
mode beli, ditambah sampel ekor. Semua target di `math_targets.json` terpenuhi.

| Angka | Target | Alasan / sumber | Terukur |
| --- | --- | --- | --- |
| RTP (semua mode) | 96,70% | Batas atas Engine | 96,698% di kelima mode |
| Hit rate base | 24–30% | Angka reel tanpa paksaan: 26,7% | 27,3% |
| Lelang muncul | 1 dari 170–205 | Angka reel: 1 dari 188,9 (10 juta spin) | 1 dari 186,6 |
| Rata-rata menang lelang | 100–122× | Lelang tanpa paksaan | 111,7× |
| RTP base / lelang | 33–40% / 58–66% porsi | Hold & win: fitur membawa sebagian besar | 36,8% / 59,9% (porsi 61,9%) |
| Std dev base | 20–58 | Volatil tinggi, di bawah batas Engine 60 | 32,5 |
| Max win dan peluangnya | 25.000×, 1 dari 1–10 juta | Pedoman Engine | 25.000×, 1 dari 4.182.795 |
| Menang di bawah taruhan (dari semua hit) | ≤ 60%, dilaporkan | Tidak ada batas resmi | 55,3% |
| ETL > 40×, base | < 0,9 | Batas risiko Engine | 0,545 |
| Beli bonus: balik modal / median / di bawah 10% harga | ≥ 17% / ≥ 0,35× / ≤ 5% | Lelang tanpa paksaan | 19,2% / 0,40× / 2,0% |
| Beli gavel: sama | ≥ 17% / ≥ 0,35× / ≤ 3% | sama | 18,8% / 0,39× / 1,4% |
| Beli private: sama | ≥ 18% / ≥ 0,42× / ≤ 1% | sama | 19,7% / 0,46× / 0,0% |

Frekuensi lelang adalah satu-satunya angka yang diselesaikan agar RTP tepat: 1 dari 186,6, 1,2%
lebih sering daripada angka reel.

## Anggaran

- Spin base tanpa lelang: menang 1 dari 3,74, rata-rata 1,37× → 0,368.
- Lelang: 111,7× ÷ 186,6 → 0,599. Jumlah: 0,368 + 0,599 = 0,967.
- Pemicu alami: 6 Lot 85,7%, 7 Lot 12,8%, 8 Lot 1,3%, 9+ 0,07% (10 juta spin, 52.951 pemicu).
- Bonus (tepat 6 Lot): 110,8× ÷ 0,967 = 114,6× → harga 110× (−2,2% pada rata-rata).
- Gavel (6 Lot + satu ketukan): 187,3× ÷ 0,967 = 193,7× → harga 190× (−1,1%).
- Private (9 Lot + dua ketukan): 326,7× ÷ 0,967 = 337,9× → harga 340× (+0,4%).
- Ante 1,5×: lelang 1 dari 103,2 (1,8× lebih sering).

## Mode

| Mode | Harga | Yang berubah bagi pemain | RTP | Balik modal | Median | Di bawah 10% harga | Max win |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 1× | Permainan normal | 96,698% | 12,2% | 0 | — | 1 dari 4.182.795 |
| ante | 1,5× | Lelang sekitar 1,8× lebih sering | 96,698% | 8,9% | 0 | — | 1 dari 2.312.511 |
| bonus | 110× | Langsung lelang dengan 6 Lot | 96,698% | 19,2% | 0,40× harga | 2,0% | 1 dari 23.264 |
| gavel | 190× | 6 Lot dan satu ketukan Gavel di awal | 96,698% | 18,8% | 0,39× harga | 1,4% | 1 dari 6.367 |
| private | 340× | 9 Lot dan dua ketukan Gavel di awal | 96,698% | 19,7% | 0,46× harga | 0,0% | 1 dari 3.325 |

## Di mana varians tinggal

Di Gavel dan Last Bid. Lelang rata-rata memainkan 8,5 respin, mengisi 10 dari 15 sel, dan
melihat 0,64 Gavel dan 0,42 Buyer (lelang tanpa paksaan, 300.000 sesi). Tanpa Last Bid lelang
rata-rata hanya 38× dan tidak pernah mencapai 25.000×; Last Bid (rata-rata ×1,64) membawa ekor
tanpa menambah keputusan atau aturan di dalam lelang. Full House 1 dari 81 lelang.

Ekor mode base, tanpa celah:

| Rentang menang | Peluang | Porsi RTP |
| --- | --- | --- |
| 500–1.000× | 1 dari 10.195 | 7,0% |
| 1.000–2.000× | 1 dari 27.063 | 5,2% |
| 2.000–5.000× | 1 dari 54.457 | 5,7% |
| 5.000–10.000× | 1 dari 241.315 | 2,9% |
| 10.000–25.000× | 1 dari 559.482 | 3,0% |
| di antaranya tepat 25.000× | 1 dari 4.182.795 | 0,6% |

Tidak ada ronde yang dipaksa ke max win; buku ekor dari sampel `freegame_tail` (≥ 1.500× di base
dan bonus, ≥ 3.000× di gavel, ≥ 5.000× di private) dengan bobot = diterima ÷ dicoba.

## Batasan Engine

Diukur dengan `math_audit.py` (batas dibaca 12 Nov 2026).

- Tes kritis: semua lolos (mode termurah 1×, std dev base 32,5, RTP 96,698% di semua mode, max win
  25.000×, harga tertinggi 340×, 5 mode).
- Kelas risiko: **0 dari 6 gagal**. ETL > 40× tertinggi 0,600 (ante); peluang ≥ 10.000×
  tertinggi 0,19% (private) dari 1%; ≥ 25.000× 0,03% dari 0,5%.
- Batas setelah penalti: eksposur $50 juta, biaya taruhan $500.000; taruhan dasar terbesar $1.470,
  jadi template $1.000 terpakai penuh.
- Tes format SDK: hash buku dan payout cocok di kelima mode.
- Aturan diputar ulang terpisah dari kode game (`verify_books.py`): 599.976 buku base, bonus,
  gavel dan private, semuanya mengikuti `readme.txt` (menang line dihitung ulang, Gavel base,
  Lot awal, reset respin, Buyer, Gavel, Last Bid, Full House, total sama dengan lookup table).

## Keputusan dan pertanyaan terbuka

Belum ada keputusan pengguna untuk math ini. Pilihan lead (2026-11-25, pengguna tidur):

1. **Tanpa The Offer**, sesuai revisi roadmap 24 Nov (pedoman Engine).
2. **Last Bid ditambahkan** sebagai pembawa ekor, ditentukan buku. Tanpa itu lelang rata-rata 38×
   tanpa ekor.
3. **Full House menggandakan total, bukan hadiah tetap 5.000×**, dan tidak dinamai Grand/Jackpot
   (Engine melarang jackpot).
4. **20 line, bukan 10.** Dengan 10 line base hanya mengembalikan 0,11; hit rate 16%.
5. **Gavel di respin meninggalkan sel kosong** (tidak menjadi Lot); Buyer menjadi Lot.
6. **Mode**: ante 1,5×, bonus 110×, gavel 190×, private 340×. Private 1.000× dari ide awal
   menjadi 340×, karena 9 Lot dengan satu ketukan bernilai lebih rendah dari mode gavel; dua ketukan
   memperbaiki tangganya.
7. Bobot alami, bukan optimizer Rust. Reel dari jumlah stop pasti dan seed tetap.

Risiko yang diterima atau masih terbuka:

1. **Last Bid ×100 adalah satu angka besar yang jatuh di akhir.** Frontend harus membangunnya
   sebagai momen (palu, angka penawaran), bukan kejutan diam.
2. **Menang di bawah taruhan 55,3% dari semua hit di base.**
3. **Tangga mode berhenti di 340×**, di bawah patokan pasar 1.000–5.000×.
4. Belum diunggah ke Studio; belum di-commit.
