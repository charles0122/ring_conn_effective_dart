# RingConn Dart 代码规范

这个仓库使用 [docs.page](https://docs.page/) 承载项目内的 Dart 代码规范文档。

当前站点分成两层：

- `团队规范`：团队自己维护、当前已经采纳的规则，是权威版本
- `官方参考`：同步自 Effective Dart 中文内容，仅用于查阅和对照

官方参考来源于：

- [cfug/dart.cn `src/content/effective-dart`](https://github.com/cfug/dart.cn/tree/main/src/content/effective-dart)

## 本地更新官方参考内容

执行下面的命令会重新拉取上游中文 Effective Dart 文档，并转换为适合 `docs.page` 预览的官方参考页：

```bash
python3 scripts/sync_effective_dart.py
```

说明：

- `docs/team-guidelines/` 由团队手工维护，不会被同步脚本覆盖
- `docs/effective-dart/` 由同步脚本生成，用于官方参考

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
