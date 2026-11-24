# Prototype-first UI

[English](README.md)

面向通用 AI Agent 的设计技能。它让 Agent 像资深产品设计师兼严谨的工程师一样工作：
先定方向再动像素，基于项目内的设计系统构建，渲染并评审真实产出，
未经审阅的设计不进入生产。覆盖 Web 应用、网站、数据看板、iOS / Android / 桌面应用、
浏览器扩展、CLI/TUI、邮件、幻灯片、打印文档、图解和设计系统。

一个 `SKILL.md` 按需求只加载少量相关参考文档。工具都是可选的、仅依赖标准库的 Python；
任何能读写文件的 Agent 不用工具也能按技能执行。

## Agent 能得到什么

- **一个工作循环**：定位、分流、定方向、构建、渲染与评审、交付，
  并用固定格式区分"已验证"和"未验证"。
- **一套质量标准**：方向设定、层级、字体、色彩与对比度、状态、动效、无障碍、国际化、
  "AI 默认风格"反模式清单，以及可打分的评审量表。
- **平台规范**：Web、iOS/iPadOS、Android、macOS、Windows、Linux、浏览器扩展、
  CLI/TUI、邮件、打印、幻灯片、电视、手表和空间计算。
- **起步设计系统**：203 个 DTCG 令牌（亮色/暗色双模式），声明了 58 组对比度配对
  （共 116 项检查）全部通过；组件放在 cascade layer 中，附带实时预览页；
  另有应用、网站、幻灯片和文档脚手架。
- **工具**（`scripts/pfui.py`）：环境诊断、进度状态、脚手架、本地审阅台、一键检查、
  46 条设计 lint 规则，以及从同一份令牌生成 CSS、iOS、Android、Flutter 的管线。
- **治理机制**：内容防火墙（需求说明永远不会变成界面文案）、生产 UI 的显式审批门禁、
  不可信媒体策略、脱敏示例数据，以及可选历史重置所需的已验证恢复快照。

## 快速开始

在目标项目中安装技能后（见下文）：

```sh
S=.agents/skills/prototype-first-ui/scripts
python $S/pfui.py doctor                                   # 这台机器能验证什么？
python $S/pfui.py init system --name "Harbor"              # 令牌、组件、预览页
python $S/pfui.py init app --name "Orders" --platform ios  # 带状态视图的原型骨架
python $S/pfui.py serve designs                            # http://127.0.0.1:8765/__pfui/review.html
python $S/pfui.py check                                    # 记录、令牌、对比度、lint
```

然后这样对 Agent 说：

```text
$prototype-first-ui critique
在移动端和桌面宽度、亮色和暗色下评审我们的设置页，按质量量表打分并附截图证据，
按影响排序给出改进项。
```

## 模式

| 模式 | 产出 |
|---|---|
| `system` | 令牌、主题、组件、预览页和使用说明 |
| `critique` | 以证据支撑、按量表打分的质量评审 |
| `prototype` / `explore` | 页面、流程和备选结构，每个状态都有独立链接 |
| `compose` | 幻灯片、文档、海报、社交图片、图解、邮件 |
| `visualize` | 指标定义清晰、数据经过核对的图表和看板 |
| `audit`、`approve`、`implement`、`verify`、`sync` | 生产 UI 生命周期 |
| `bootstrap` | 可选的仓库清理与本地历史重置，包含恢复快照 |

生产 UI 保留门禁：审计、原型、审阅、显式批准、纯设计提交、实现门禁、
实现一个切片、验证。独立产物按其媒介验证，不虚构路由或审批提交。

## 命令

| 命令 | 用途 |
|---|---|
| `pfui.py doctor` | Git、浏览器、自动化、导出器、技术栈、令牌来源 |
| `pfui.py status` | 交付物、审阅状态和下一步 |
| `pfui.py init system\|app\|site\|deck\|doc` | 起步系统或脚手架；文案以 `{{slot}}` 留作待决内容 |
| `pfui.py serve` | 本地预览和审阅台：状态、主题、平台、宽度、总览视图 |
| `pfui.py check [--final]` | 审阅记录、UI 契约、来源、文案清单、令牌对比度、lint |
| `pfui.py tokens check\|build\|ramp\|contrast` | DTCG 令牌转 CSS、iOS 资源目录与 Swift、Android 资源、Flutter |
| `pfui.py lint` | 可访问名称、焦点、对比度、触控尺寸、字体与色彩纪律、动效、占位符、资源、邮件 |
| `pfui.py content`、`pfui.py gate` | 渲染文案清单和生产 UI 门禁 |

完整说明见[工具参考](references/tooling.md)。

## 依赖

- 支持文件读写的 AI Agent；执行检查需要命令行。
- 可选：Python 3.9+（只用标准库）运行工具；Git 用于生产 UI 提交门禁；
  浏览器、模拟器用于渲染审阅；需要特定格式时再用图片生成和导出工具
  （LibreOffice、python-pptx、pandoc 等）。`pfui.py doctor` 会列出现有能力。

## 安装

只在项目级安装，不要全局安装。在目标项目目录运行，选择项目级作用域和所用 Agent：

```sh
npx skills add DejavuMoe/prototype-first-ui --skill prototype-first-ui --copy
```

也可以从 [GitHub Releases](https://github.com/DejavuMoe/prototype-first-ui/releases)
下载技能包，解压到 `<项目>/.agents/skills/prototype-first-ui/`
或宿主的项目级技能目录（例如 `.claude/skills/`）。不支持自动发现的 Agent，
可在 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 或其规则文件中指向安装后的 `SKILL.md`。
安装器需要 Node.js，手动解压不需要。

本仓库是技能的分发源码，不是产品工作区。

## 示例

```text
$prototype-first-ui system
以我们的青绿色重塑起步系统，亮色和暗色下所有对比度配对保持通过，
并从同一份令牌文件生成 CSS、iOS、Android 和 Flutter 输出。

$prototype-first-ui prototype
为文件管理器制作批量重命名原型：预览、冲突、进度、取消和错误。附上状态链接供审阅。

$prototype-first-ui compose
用已确认的文案制作六页介绍幻灯片，并说明当前环境缺少哪些导出格式。
```

审阅通过后，用 `$prototype-first-ui implement` 并给出已批准的文件和设计提交。
更多示例：[中文](references/prompts.zh-CN.md) · [English](references/prompts.en.md)。

[技能指令](SKILL.md) · [设计质量](references/design-quality.md) ·
[平台规范](references/platforms.md) · [工作流](references/workflow.md) ·
[发布指南](RELEASING.md) · [更新日志](CHANGELOG.md)

## 从 2.x 升级

审批记录只认项目自有的 `design-review.json`；实现门禁会核对所有已登记的原型依赖，
包括二进制资产。按[升级说明](references/design-review.md#upgrading-a-2x-project)处理，
旧的状态标记不会自动变成新批准。原有 UI、文案和来源契约仍可使用，
也不需要另外安装任何技能或编辑器。

## 许可证

[MIT](LICENSE)
