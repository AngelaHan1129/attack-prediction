## Label Studio 影片伺服器

在 Windows 下，請先切到 `STGCN\data\raw`，再啟動影片靜態伺服器：

```powershell
cd "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\raw"
npx http-server --cors -p 8081
```

這個指令會把 `data/raw` 底下的影片公開成瀏覽器可讀的網址，例如：

```text
http://127.0.0.1:8081/rwf2000/train/Fight/-1l5631l3fg_0.mp4
```

請保持這個伺服器持續運作，否則 Label Studio 無法載入影片。Label Studio 的影片元件是透過瀏覽器重新抓取影片資源，因此來源必須可被瀏覽器存取，且跨來源請求需能正常處理。 [web:551][web:682][web:431]

---

## `tasks.json` 產生方式

切回 `STGCN` 根目錄後執行：

```powershell
cd "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN"
python .\generate_labelstudio_tasks.py --root-dir "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\raw\rwf2000" --base-url "http://127.0.0.1:8081/rwf2000" --output ".\tasks.json"
```

產生出的 `tasks.json` 會包含：

- `video`：Label Studio 要讀取的影片 URL。
- `file_name`：檔名。
- `relative_path`：相對路徑。
- `split`：`train` 或 `val`。
- `gt_class`：`Fight` 或 `NonFight`。

---

## Label Studio 匯入注意事項

你的 Label Studio 專案需使用 video 標籤，例如：

```xml
<View>
  <Video name="video" value="$video" />
</View>
```

因此每筆任務都必須有 `data.video`，而且這個 URL 必須是 Label Studio 所在瀏覽器能直接讀取的地址。 [web:551][web:606]

---

## 常見問題

### `unable to play`
如果瀏覽器可以直接打開影片，但 Label Studio 顯示 `unable to play`，通常不是檔案不存在，而是影片來源沒有正確提供給 Label Studio，或瀏覽器端跨來源資源載入失敗。 [web:431][web:682]

### `404 Not Found`
如果網址開不起來，先確認：

- `http-server` 是否真的在 `data/raw` 啟動。
- 影片檔是否存在於 `rwf2000/...` 路徑下。
- Label Studio 匯入時的 `video` 路徑是否和靜態伺服器路徑一致。

---

## 建議的最小流程

```powershell
cd "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\raw"
npx http-server --cors -p 8081
```

另開一個視窗：

```powershell
cd "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN"
python .\generate_labelstudio_tasks.py --root-dir "C:\Users\User\Desktop\nutc\YS_LAB\研究\attack-prediction\STGCN\data\raw\rwf2000" --base-url "http://127.0.0.1:8081/rwf2000" --output ".\tasks.json"
```
