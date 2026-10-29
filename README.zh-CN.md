# 免费实战教程：给 Markdown 稿件加一道本地质检

**版本 1.0｜2026-10-29｜原创合成示例｜免费教程与源码｜已通过独立技术和文档复核**

你将完成三个小实验：找出元数据类型错误、验证修正结果、识别重复 slug。教程和工具一并提供，不需要购买其他包、不需要账号、API 密钥或上传稿件。使用开源 PyYAML；不是 PyYAML 官方教程。

## 1. 先知道它检查什么

Markdown 正文前的 YAML front matter 就像稿件的标签卡：

```yaml
---
title: 把会议记录整理成行动项
author: 示例编辑
slug: meeting-action-list
tags: [写作, 协作]
draft: false
date: 2026-10-29
---
```

本工具采用一套**演示用固定约定**：title/author 是非空字符串，slug 只能含小写英文、数字和中间短横线，tags 是非空字符串列表，draft 是布尔值，date 是有效 YYYY-MM-DD 日期，正文不能为空。你的网站可能有不同规则；本教程不代表任何 CMS 的通用规范。

## 2. 准备环境

需要 Python 3.10+ 和基本终端操作。解压后进入本目录；下文的相对路径都以该目录为起点。

```bash
python --version
python -m venv .venv
```

激活方式（二选一）：

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

若 Windows 策略禁止激活，不必更改安全策略，可用 `.venv\Scripts\python.exe` 替换后续所有 `python`。如果系统只有 `python3`，用它创建虚拟环境，激活后再运行以下命令。

```bash
python -m pip install -r requirements.txt
python -m unittest -v
```

依赖锁定 PyYAML 6.0.3。首次安装通常要联网；包中没有 Python 或 PyYAML 安装文件。安装完成后的检查过程不联网。仅在证据注明的 Linux / Python 环境实际复测；Windows/macOS 命令是操作指引，未原生验收。这里不承诺新电脑安装必然成功。

## 3. 实验一：看见错误，不要急着「修复程序」

打开 `examples/before/article.md`。其中故意使用了：

```yaml
tags: 写作
draft: "false"
```

第一项是字符串而不是列表；第二项是字符串而不是布尔值。运行：

```bash
python content_check.py examples/before --output lesson-before
```

预期输出：`files` 为 1、`failed` 为 1；退出码 **1** 是找到了问题，不是程序崩溃。打开 `lesson-before/report.html`，应看到 tags 与 draft 两个错误。`failed` 按失败文件数计数，不按错误条目计数。

## 4. 实验二：修改类型，再用报告验收

为了便于对照，修正稿已经放在独立的 `examples/after/article.md`；检查器不会替你改原稿。你也可把 before 稿复制到自己的练习目录，再手动改为：

```yaml
tags: [写作, 协作]
draft: false
```

运行修正稿：

```bash
python content_check.py examples/after --output lesson-after
```

预期 `files: 1`、`failed: 0`，退出码 **0**。查看两个 JSON 中的 sha256：稿件内容有修改时哈希不同，证明这是不同版本的文件，而不是证明稿件质量更好。

`draft: true` 也会通过，因为工具检查类型，而不是替编辑批准上线。报告通过不代表正文事实正确、日期不是未来、版权合规或网站一定能发布。

## 5. 实验三：单稿都合法，为什么一起检查失败？

`examples/duplicate/a.md` 与 `b.md` 各自字段合法，但故意用了相同 slug。

```bash
python content_check.py examples/duplicate --output lesson-duplicate
```

预期 `files: 2`、`failed: 2`，退出码 **1**；两稿都应收到冲突提示。把 b 的 slug 改成不同值并在一个新输出目录复跑，就能自行验证解决方式。不要改动包内示例后再将其当作原始测试证据。

注意：检查只比较**同一次输入目录内**的稿件，不知道你线上已有的 URL，也不会联网查重。

## 6. 自动复现实验

```bash
python verify_tutorial.py
```

这个脚本在临时目录运行三个实验，验证预期文件数、异常数、错误条目、退出码、报告存在以及源样稿 SHA-256 不变；还验证相同输出目录被拒绝、空目录不会被误报成功。临时结果随后自动清理，终端输出机器可读摘要。需要持久报告请使用上面的手动命令。

## 7. 常见问题

- **第二次运行提示目录已存在？** 这是防覆盖设计。改用新的输出目录，如 `lesson-after-02`，不要盲目删除已有报告。
- **退出码怎么查？** bash 用 `echo $?`，PowerShell 用 `$LASTEXITCODE`，紧跟在运行命令后执行。
- **0、1、2 怎么区分？** 0=有稿且全部通过；1=有异常或没找到稿；2=输入/输出或运行错误。空目录也生成报告，但返回1。
- **找不到 yaml 模块？** 在实际运行脚本的同一个 Python 环境执行 `python -m pip install -r requirements.txt`。
- **为什么 `.MD` 没检查？** 本版只扫描小写 `.md`，不自动转换文件名。
- **为什么 YAML 解析失败？** 检查缩进、重复键、键类型；本版不支持锚点/别名、Python 对象标签。某些错误合并为一条提示，并非精确定位编辑器。
- **为什么合法 CMS 稿件也报错？** 规则是教程约定，不会推断站点的字段映射。先核对规则，勿为了通过检查破坏真实站点配置。

## 隐私与安全边界

所有演示资料均为原创虚构内容，不包含真实客户或个人信息。检查器只读稿件，在指定目录写报告，不联网、不执行稿件代码、不自动发布。报告保存相对文件名、SHA-256 和错误（冲突提示可能引用另一文件名）；**文件名也可能敏感，哈希也不是匿名化保证**。不要直接公开真实稿件报告，先用合成样例复现。

本版拒绝 YAML 别名/锚点，限制单文件 2 MB、front matter 16 KiB，跳过符号链接文件；这些措施不是完整沙箱，也没有目录总量、CPU 或内存硬限额。不要把它直接暴露为接收陌生上传文件的网络服务。只处理你有权读取的本地文件。

## 免费分享、许可和边界

原创代码、文档、样稿及证据采用根目录 MIT 许可，可免费使用、修改、商用和分享，保留版权及许可文本。PyYAML 独立采用 MIT，副本在 `licenses/`；本包不包含其源代码或二进制。无额外人工支持、更新或响应时限承诺；适用法律的强制性权利不受本说明影响。

没有销量、节省时间百分比、收入或兼容性保证。教程不需要付费功能，未包含支付或注册入口。本次交付已通过独立技术与文档复核，但不代表所有操作系统、实际站点或未知输入都已验证。

来源与核验：上游 https://github.com/yaml/pyyaml ，版本锁定见 requirements.txt；本地发行包许可已核验。这里使用 SafeLoader 子类解析，并额外拒绝重复键和别名。测试环境及结果见 `evidence/`，未验证全新设备联网安装及原生 Windows/macOS。
