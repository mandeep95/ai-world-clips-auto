# Videos — upload manifest

The video files live in this folder in the repo (the repo is public, so
Threads can fetch them from `raw.githubusercontent.com`).

The connector used to create this repo cannot push binary files, so the
videos were NOT uploaded with the code. Upload them once, using
`scripts/upload_videos.sh` or the GitHub web UI (see `docs/SETUP.md` —
each file is under GitHub's 100 MB per-file limit).

Verify after upload with `sha256sum` — the hashes must match.

| File in this folder | Original file name | Size | SHA-256 |
|---|---|---|---|
| 08-motu-patlu-rain-noida.mp4 | browser-download-20261105T120355.907417103Z-7-kling_20260828_VIDEO_Motu_aur_p_5281_0.mp4 | 4,447,386 | a9c2e2557d814e86afd92b8c82f4f0d0b9e14674d653cad5adecd10e31289692 |
| 09-lion-hyena-heads.mp4 | browser-download-20261105T115838.980951328Z-2-kling_20261022_VIDEO__Start_Fra_1234_0.mp4 | 12,076,016 | ce8b50287c12e8c94a45948d808ba121c29af4042b0ca66c9e85faa4a62e59db |
| 10-village-children-soccer.mp4 | browser-download-20261105T121126.621793456Z-11-kling_20260914_Image_to_Video_Create_a_1_1379_0.mp4 | 35,440,428 | 4d56cb877562d15b368ae4ba0ec1093c6521660c558cf2ecbdb71959a828df77 |
| 11-vegetable-pool-party.mp4 | browser-download-20261105T121246.753336397Z-12-kling_20261015_VIDEO_See_in_Hin_264_0.mp4 | 10,552,966 | ae1bf60add36b50265a86b30d97f2327d936fc0388f4b5afa48f647d27d3c1eb |
| 12-sun-wukong-vs-taotie.mp4 | browser-download-20261105T121339.879684946Z-13-kling_20260802_VIDEO_Ultra_real_3107_0.mp4 | 18,852,075 | 0b85c0aa8bcfbde7c08880b8944ef582cb25e7f2896020bfd91714a0c6223192 |
| 13-bear-sheep-village.mp4 | browser-download-20261105T120150.577249501Z-5-kling_20261024_Image_to_Video_A_highly_r_5933_0.mp4 | 12,878,397 | 070380596e9d7db14021d1523101b5fd213f15fadcac0c46a35ce232f3129b6b |
| 14-sugarcane-vendor.mp4 | browser-download-20261105T121946.936563740Z-16-kling_20260903_VIDEO_voice_in_H_5069_0.mp4 | 2,893,426 | 155d73a5225b67a7ffd8841bc8310d89a8c58663b892b1763026aac5931ca520 |
| 15-urdu-pronunciation.mp4 | browser-download-20261105T122019.114204986Z-17-kling_20261028_VIDEO__Kuchuu_Po_3105_0.mp4 | 7,702,699 | f6e94adc59977e8ba2270581d355054cf4f8eadbfe4fc122842ffd4f31778f06 |
| held-08-chicken-mimics-woman.mp4 | browser-download-20261105T120429.924572928Z-8-kling_20261025_VIDEO____________1603_0.mp4 | 38,148,369 | bbff4e12cfe64a63964ef83dd010e6fa6add5ec341cfbd5b7ad7dc20844858c1 |
| held-15-khalnayak.mp4 | browser-download-20261105T121542.304010012Z-15-kling_20260909_Motion_Control_Copy_the_E_3099_0.mp4 | 61,512,748 | c1974a4d342205385b9367123dc56460fce164c7a4121e976ec5b2e80b7b8ba9 |

NOT in this repo (do not add):
- Index 6, Telugu children (#3) — HELD for copyright reasons. Never upload it.
- Index 14 — not in the posting queue (unreviewed content).
