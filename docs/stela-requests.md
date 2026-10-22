# 給 STELA 的需求（Agora 這邊提出）

Agora 不直接改 STELA；這份清單是 Agora 需要 STELA 那邊做的事，依急迫程度排。每一項說明為什麼、改哪裡（依 STELA e740d64 的程式碼）、Agora 這邊對應的文件。

## 狀態（2026-10-22 22:30，STELA 的 session 回覆）

- 第 1 項已套用：P14 的 B2／B3 改用 `tools/system.pub` → `Initrd:/certs/system.pub`，`pkg.pub` 與 `pkgcore` 不動（P14 當時在 K0，B 還沒開始；若執行中的 session 沒重讀到，審核時補改）。
- 第 2 項：`system` 項定好後寫進 STELA 的 `docs/system.md`。第 3 項：E2 照原計畫。
- 第 4–11 項已記進 STELA 的待辦，排 **P15**。
- 2026-10-23 12:00 之後 STELA 不再動 `~/stela-ports`，也不動 `~/Agora`。

## 急：P14 進行中就該知道（B2／B3 的設計）

1. **System 映像與套件用不同的鑰匙。** P14 的 B2 打算用 pkg 的鑰匙（`tools/pkg.pub`）簽 System 映像。Agora 的決定（2026-10-22）：套件鑰匙會放進 GitHub Actions 的 secret 讓 CI 簽 index；System 鑰匙永遠只在使用者手上。CI 的 secret 外洩不該能簽出 loader 會自動開機的系統映像。需要：`Initrd:/certs/system.pub`（`tools/system.pub`）與 `pkg.pub` 分開；`stela-update` 與 kernel 驗 System 時用 `system.pub`；`pkgcore` 不動。P14 之內兩把都可以先是測試鍵（`pkgsign.py keygen` 加一個不同句子的種子）。（`docs/signing.md`）
2. **`index.json` 的 `system` 項**：B3 定好格式後請寫進 `docs/system.md`，Agora 的 index 工具照抄（`docs/index.md`）。
3. **E2 的 ports workflow**：照計畫寫在 `~/stela-ports/.github/workflows/build.yml` 即可，Agora 會以它為底改（`docs/release.md`）；不必顧 Agora 的欄位。

## P14 之後（pkg／pkgcore 的小改動）

4. `Makefile` 的 `PORTS_DIR` 預設 `~/stela-ports` → `~/Agora`。
5. `pkgcore::parse_index`：讀 `built-for`、`serial`、`packages[].stela`、`revision`（都是新增欄位，`format` 維持 1，缺了就當沒有）；`pkg update` 拒絕 `serial` 比 `Data:/.pkg/index.json` 的小、拒絕 `built-for` 的 major.minor 比系統新；`pkg install` 拒絕 `stela` 比系統新的套件。系統版本從 `env!("CARGO_PKG_VERSION")`（kernel 已這樣印）經 `SysInfo` 或 libstela 給使用者程式。
6. `packages[].url` 相對於 index 的位置：`ops::install` 下載時用 `http::join(base, url)`（絕對的照舊）。
7. `Initrd:/certs/pkg.pub` 一行一把鑰匙，任何一把驗過就算（換鑰匙時兩把並存一個版本）。
8. `pkg install --from 卷宗:/資料夾 名稱`：讀那裡的 `index.json` 與 `.sig`、驗簽、依賴也從那裡拿（離線安裝）。
9. `PKGINFO` 多 `revision = `、`stela = `；`pkg list` 顯示 `5.4.7-1`。
10. `tools/pkg.pub` 換成正式的套件公鑰；`make test-pkg` 的測試鍵只放進測試映像，不進正式的 initrd（或 `pkg.pub` 多行時一行是測試鍵、release 時拿掉——擇一）。
11. Setup 的套件頁與 `pkg` 的訊息把來源叫 Agora；新格式化的 Data 寫入預設的 `pkg.conf`（指向 STELA 該版本對應的 Agora release）。

## 不急（之後再談）

- `tools/portbuild.py` 改名時 `Makefile` 的 `test-ports` 一起改。
- `pkg remove` 的「誰依賴我」、交易式安裝（STELA `docs/pkg.md` §6 的限制），Agora 沒有依賴它們。
