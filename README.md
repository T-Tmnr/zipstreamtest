
## 目的
複数のファイルをZIPにまとめつつ、ストリーミング配信する検証。

### 前提
- crc-32 を事前に計算できない
- 対象のファイルサイズは不明

## 方針
general purpose bit flag の bit 3 を ON にすることで、 local header に記録しなければならない、 size, crc-32 を
ファイルデータの直後に追加する data descriptor で示すことができる。
この方法を利用することで、事前に ファイルサイズ、 crc-32 がわからない場合でも local header を作成することができる。

## 課題

### data descriptor
7zip が general purpose bit flag の bit 3 が ON の時の data descriptor に対応していない？
展開時に local header の size, crc32 を優先して参照してしまっている。
仮に size のみ設定しても、 CRC32 が一致せずに展開できない。

### ファイル名のエンコード
Unicode のサポートが入ったのが仕様書のバージョン 6.3.0。
しかし、現行バージョンとして表明されているのが 6.2.0。
それゆえに、Unicodeファイル名に対応できていないアプリも多い。

## 参考資料
https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT