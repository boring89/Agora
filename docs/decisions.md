# 決策紀錄

## 2026-10-22：第一版（使用者「照建議」）

依據：STELA e740d64 的 `docs/ports.md`、`docs/pkg.md`、`docs/setup.md`、`docs/tls.md`、`docs/linux.md`，`~/stela-ports` 2ae643c（22 個 port）。

| # | 決定 |
|---|---|
| 1 | Agora 只放配方、工具、文件；`pkg`／`pkgcore`／Setup 留在 STELA（GPL-3.0-or-later）。Agora 自己有 0BSD 的 index 與簽章工具，不複製 STELA 的 `pkgsign.py`。 |
| 2 | 配方與工具 0BSD；patch 第一行 `SPDX-License-Identifier:`，授權跟上游。 |
| 3 | 目錄維持 `ports/NAME/{port.toml,build.sh,test.sh,files/,patches/}`；`tools/portbuild.py` 暫不改名（STELA 的 Makefile 與 P14 引用它）。 |
| 4 | `~/stela-ports` → `~/Agora`，2026-10-23 12:00 之後搬；STELA 的 `PORTS_DIR` 跟著改。 |
| 5 | GitHub 名稱預設 `boring89/Agora`；不建 repo、不 push。 |
| 6 | 相容性：每個套件標最低版本 `stela`；一個 Agora release 對一個 STELA 版本（tag 同名），index 記 `built-for`，`pkg` 只比 major.minor。 |
| 7 | `port.toml` 加 `revision`，套件版本 `UPSTREAM-REVISION`。 |
| 8 | index 加 `serial`、`generated` 防重送；`format` 維持 1。 |
| 9 | `system` 項等 P14 B3 定義後照收。 |
| 10 | 鑰匙由使用者本機產生，私鑰離線備份；公鑰進 Agora `keys/` 與 STELA `tools/pkg.pub`。 |
| 11 | 套件與 System 用兩把鑰匙；System 鑰匙永不進 CI。先告訴 STELA（P14 B2／B3）。 |
| 12 | 套件由 CI 用 secret 簽（`workflow_dispatch` 與 `v*` tag、受保護的 environment）；System 本機簽。 |
| 13 | 伺服器 = GitHub Releases；`pkg.conf` 指向 release 的 download URL。 |
| 14 | index 的 `url` 相對於 index；`portbuild.py mirror`；`pkg install --from` 提給 STELA。 |
| 15 | push 只跑 lint；完整建置與 QEMU 測試只在 `workflow_dispatch` 與 tag。 |
| 16 | `STELA_VERSION` 檔釘 STELA 的 tag。 |
| 17 | Release 含所有套件、簽好的 index、`SHA256SUMS`、全部上游 tarball、`SOURCES.txt`。 |
| 18 | P14 的 E2 先寫 `build.yml`，Agora 之後以它為底。 |

12:00 之後的第一批工作：搬 repo、6 個 `copy-from` 的 port 改官方網址、patch 加 SPDX、`revision`／`stela` 進 PKGINFO 與 index、README 的表格、`lint` 子命令。

## 2026-10-23：與 P14 同步

P14 結束（STELA d7077a1，版本 0.2.0，使用者尚未審核；`~/stela-ports` 8d9c3c6）。對 Agora 的影響：

- `~/stela-ports` 多了 ripgrep、fd（`toolchain = "rust"`，crates.io 的 `.crate`，cargo 在建置時抓相依）與 wpa_supplicant（compile-only）；`portbuild.py` 解 `.crate`、測試時接 `build/system.img`。共 25 個 port。
- `build.yml` 已寫好（決定 18 的底）；secret 名稱沿用 `PKG_SIGNING_KEY`（原本寫 `AGORA_PACKAGE_KEY`，改掉）。
- 兩把鑰匙已分開（決定 11 落地）；`system` 項格式已定；`pkgsign.py verify` 要求 index 正好列出資料夾裡的 tar——相對 `url` 與它相容。
- STELA 的 `docs/release.md`：ports repo 打與 STELA 同名的 tag，STELA 的 release job 下載同名的 ports release——與決定 6、16 一致，Agora 的 release 要先做。
- STELA 的 P15 排了 `stela-requests.md` 第 4–11 項。

**待決定**：`rust` port 的相依要不要 vendor（`cargo vendor` 進 `sources/`，建置完全離線、release 的 `sources/` 才真的齊全）或維持 cargo 在 CI 抓（`--locked` 已釘版本；相依都是 MIT／Apache，沒有 GPL 的原始碼義務）。
