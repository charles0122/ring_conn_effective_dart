# RingConn Dart 代码规范

这个仓库使用 [docs.page](https://docs.page/) 承载项目内的 Dart 代码规范文档。

当前第一版内容以官方 Effective Dart 的中文文档为示例，来源于：

- [cfug/dart.cn `src/content/effective-dart`](https://github.com/cfug/dart.cn/tree/main/src/content/effective-dart)

## 本地更新示例内容

执行下面的命令会重新拉取上游中文 Effective Dart 文档，并转换为适合 `docs.page` 预览的 MDX 文件：

```bash
python3 scripts/sync_effective_dart.py
```

## 本地预览

`docs.page` 官方的本地预览方式是浏览器直接读取当前目录：

1. 打开 [https://docs.page/preview](https://docs.page/preview)
2. 点击 `Select Directory`
3. 选择当前仓库根目录（需要包含 `docs.json`）
4. 修改 `docs/` 下内容并保存，页面会自动刷新预览

也可以先做一遍静态检查：

```bash
npx @docs.page/cli check
```
