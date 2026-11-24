# 使用示例

`$prototype-first-ui <模式>` 代表你的 Agent 支持的任何调用方式；
直接描述需求也可以，技能会按意图分流。

## 开始或继续

```text
$prototype-first-ui
运行 doctor 和 status，告诉我这个仓库能验证哪些内容，然后继续等待处理的交付物。
```

## 设计系统

```text
$prototype-first-ui system
基于现有品牌与组件建立项目设计系统：带亮色和暗色模式的语义令牌并在两种模式下
检查对比度、组件状态和组件预览页。只保存在当前项目，不安装或配置全局技能。
```

```text
$prototype-first-ui system
以我们的青绿色（#0f766e）重塑起步设计系统：生成色阶、重新指向强调色角色、
保持所有声明的对比度配对通过，并从同一个令牌文件生成 CSS、iOS、Android 和 Flutter 输出。
```

## 设计评审

```text
$prototype-first-ui critique
我们的设置页看起来过时了。请在移动端和桌面宽度、亮色和暗色下评审，
按质量量表打分并以截图为证据，按影响排序给出改进项。暂时不要改生产代码。
```

## 制作原型

```text
$prototype-first-ui prototype
在 designs/rename/ 中为文件管理器制作批量重命名原型：变更预览、文件名冲突、
进度、取消和错误。完成后附上各状态的链接供审阅。
```

```text
$prototype-first-ui prototype
为 iOS 和 Android 设计同一个引导流程。共享我们的设计令牌，但导航、控件和返回
行为遵循各自平台规范，并列出 HTML 原型无法验证的部分。
```

## 方向探索

```text
$prototype-first-ui explore
基于现有能力和设计系统，为 <产品> 探索三个导航与工作区结构。
```

## 视觉传播

```text
$prototype-first-ui compose
使用项目设计系统和 docs/launch-copy.md 中已确认的文案，制作六页介绍幻灯片和一页讲义。
保留可编辑源文件，检查两者的渲染结果，并说明当前环境缺少哪些导出格式。
```

```text
$prototype-first-ui compose
用 content/october.json 制作月度状态邮件：单栏、表格布局、兼容暗色模式、
关闭图片也能阅读，并按邮件媒介做 lint 检查。
```

## 数据可视化

```text
$prototype-first-ui visualize
基于这份 CSV 制作看板。定义每个指标及其对比基准，用原始行核对汇总和筛选，
并设计加载、空数据和数据过期状态。
```

## 其他平台

```text
$prototype-first-ui prototype
设计我们 CLI 的 `deploy` 命令输出：进度、成功、失败和 --json 模式。
无颜色和 80 列终端下也必须清晰可读。
```

## 生产 UI 生命周期

```text
$prototype-first-ui audit
审计当前产品的页面、操作、状态和接口，记录到 docs/ui/capabilities.md。
```

```text
$prototype-first-ui approve
我批准当前的 designs/<project>/index.html，登记批准状态并创建纯设计提交。
```

```text
$prototype-first-ui implement
实现设计提交 <SHA> 中已批准的 designs/<project>/index.html，本次范围为 <功能>。
```

```text
$prototype-first-ui sync
对比生产环境中的 <界面> 与已批准原型，修复实现偏差。
```

```text
$prototype-first-ui verify
对照已批准原型验证 <功能>：交互、文案、响应式布局、主题和键盘可访问性。
```

## 仓库初始化

```text
$prototype-first-ui bootstrap
清理此仓库，在创建并验证外部恢复快照后，将本地 Git 历史重建到 <分支名>。
保留应用功能，不改动远程仓库。
```
