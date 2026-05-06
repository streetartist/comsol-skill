# COMSOL Skill

这是一个 COMSOL Multiphysics 自动化 skill，用于端到端操作本地 COMSOL 安装。

它支持安装路径发现、COMSOL 命令启动、Java 模型编译、batch 求解、本地 Application Library 搜索、基于 JSON 的起步模型生成，以及在环境可用时通过 MATLAB LiveLink 自动化模型。

English documentation: [README.md](README.md)

## 仓库结构

```text
comsol-skill/
  README.md
  README.zh-CN.md
  .gitignore
  comsol-multiphysics/
    SKILL.md
    agents/
      openai.yaml
    assets/
      specs/
        electrostatics-square-2d.json
        heat-transfer-square-2d.json
        electrothermal-joule-heating-square-2d.json
    references/
      local-installation.md
      official-workflows.md
      thermal-electromagnetic.md
      validated-workflows.md
    scripts/
      comsol_tool.py
      comsol_project_builder.py
      comsol_examples.py
      comsol_matlab_bridge.py
```

## 功能

- 自动发现多个版本的本地 COMSOL 安装。
- 启动 COMSOL Desktop、batch 求解器、server、client、compiler 和其他命令行工具。
- 使用 `comsolcompile` 编译 Java 模型。
- 使用 `comsolbatch` 运行 `.mph` 模型或编译后的 Java `.class` 模型。
- 从 JSON spec 生成完整起步模型。
- 从支持的模板导出 `.mph`、PNG 图片和 TXT 数值表。
- 搜索并复制本地 Application Library 示例。
- 在环境可用时通过本地 MATLAB batch 执行 MATLAB LiveLink 流程。
- 默认保留运行日志，并避免覆盖输入模型。

## 多版本发现

这个 skill 不绑定某一个 COMSOL 版本。发现逻辑会检查：

1. 显式传入的 `--root`
2. `COMSOLROOT`
3. COMSOL 注册表项
4. 常见版本化安装目录，例如 `COMSOL62`、`COMSOL63`、`COMSOL64` 和未来的 `COMSOL*` 目录

可以传 COMSOL 安装根目录，也可以传平台二进制目录：

```powershell
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics"
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics\bin\win64"
```

## 快速开始

在 skill 目录下运行命令：

```powershell
cd path\to\comsol-skill\comsol-multiphysics
```

发现 COMSOL：

```powershell
python scripts\comsol_tool.py discover
```

生成起步 spec：

```powershell
python scripts\comsol_project_builder.py init-spec `
  --template heat-transfer-square-2d `
  --output .\scratch\spec.json
```

运行生成的模型：

```powershell
python scripts\comsol_project_builder.py run `
  --spec .\scratch\spec.json
```

预期输出结构：

```text
scratch/
  outputs/
    heat-transfer-square-project/
      heat-transfer-square.mph
      temperature.png
      max-temperature.txt
      run.log
```

## 已验证起步模板

- `electrostatics-square-2d`
- `heat-transfer-square-2d`
- `electrothermal-joule-heating-square-2d`

这些模板适合作为脚本化 COMSOL 自动化的稳定起点。对于其他物理问题，可以改造最接近的模板，或从本地 Application Library 中挑选相关示例作为起点。

## 常用命令

查看版本：

```powershell
python scripts\comsol_tool.py version
```

启动 Desktop：

```powershell
python scripts\comsol_tool.py desktop --detach
```

在 Desktop 中打开模型：

```powershell
python scripts\comsol_tool.py desktop path\to\model.mph --detach
```

batch 运行已有模型：

```powershell
python scripts\comsol_tool.py batch `
  --inputfile path\to\input.mph `
  --outputfile path\to\solved.mph `
  --study std1 `
  --batchlog path\to\solved.log
```

编译 Java：

```powershell
python scripts\comsol_tool.py compile path\to\MyModel.java
```

搜索本地 Application Library 示例：

```powershell
python scripts\comsol_examples.py search microwave heating --limit 10
```

复制 Application Library 模型：

```powershell
python scripts\comsol_examples.py copy `
  --source path\to\example.mph `
  --dest path\to\working-copy.mph
```

## Batch 导出安全限制

部分 COMSOL 版本会限制 Java method 和 batch-class 工作流的文件系统访问。这可能导致求解成功，但图片或表格导出失败。

`scripts/comsol_project_builder.py run` 会为生成模板的运行自动创建独立 preferences 目录：

```text
<output_dir>\comsol-batch-prefs\comsol.prefs
```

这样可以避免修改用户全局 COMSOL preferences。

## MATLAB LiveLink

这个 skill 包含 `scripts/comsol_matlab_bridge.py`，用于以 MATLAB 为中心的工作流。

只有在确认 MATLAB 和 COMSOL LiveLink 已安装且 license 可用后，才建议使用这一路线。典型任务包括：

- 将 `.mph` 模型转换为 `.m` 或 `.java`
- 对已有 COMSOL 模型运行 MATLAB 脚本
- 通过 MATLAB batch 执行保存修改后的 `.mph` 模型

## 使用准则

- 在新机器上先运行 `discover`。
- 非平凡求解使用明确的输出目录。
- 保留 batch 日志，便于复现。
- 除非明确要求，不要覆盖唯一的输入 `.mph` 文件。
- Application Library 目录只能说明示例文件存在，不代表所有相关模块 license 都可运行。
- 启动耗时求解前，先明确几何、材料、边界条件、study 设置和预期导出。

## 故障排查

### 找不到 COMSOL

传入显式根目录：

```powershell
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics"
```

或设置 `COMSOLROOT`：

```powershell
$env:COMSOLROOT = "D:\path\to\COMSOLxx\Multiphysics"
python scripts\comsol_tool.py discover
```

### 版本探测超时

如果 `version` 是 `null`，且 `version_warning` 提示超时，安装仍可能可用。先检查命令路径是否存在，再运行一个小模板仿真验证。

### 导出文件缺失

检查 batch log 是否有文件系统安全错误。如果使用 `comsol_project_builder.py run`，确认输出目录中包含：

```text
comsol-batch-prefs\comsol.prefs
```

### Application Library 模型打不开

部分本地 Application Library `.mph` 可能只是占位文件。先通过 COMSOL Desktop 的 Application Library UI 打开或下载完整示例，再重试自动化。

