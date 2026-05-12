# DiceLang

骰子表达式解析与求值的领域特定语言（DSL），面向桌游 RPG 场景。

## 约定

该文件的作用是记录 agent 在本项目中可能会遇到的常见错误和易混淆之处。
如果你在项目中遇到任何让你感到意外的情况，请及时告知与你协作的开发者，并在该文件中注明这一情况，以避免今后的 agent 重复踩坑。

## 工作流程

每次修改代码前，**必须**按以下流程操作：

1. **改前检查版本控制** - 动手前先检查 `jj log`，决定是否需要创建新变更
   ```bash
   jj log                        # 查看当前变更
   jj new                        # 如有现有变更，创建新变更
   # 或使用 branch 管理复杂改动
   ```

2. **改代码**

3. **运行测试** - 根据改动范围选择合适的测试
   ```bash
   uv run pytest test/unit/test_parser.py     # 只改了 parser
   uv run pytest test/unit/                   # 改了多个核心组件
   uv run pytest test/                        # 改动影响全局
   ```

4. **添加/更新变更描述** - 确保 `jj log` 的变更描述清晰准确
   ```bash
   jj describe -m "描述内容"     # 更新变更描述
   ```

项目使用 `uv` 管理依赖，Python 3.13.5，测试框架 pytest。

## 版本控制

项目使用 **JujuStu（jj）** 进行版本控制，而非传统 Git。

**重要约定**：有代码改动时，必须确认 `jj log` 的变更内容是否合理：

- 合理：描述清晰、改动范围正确
- 不合理：使用 `jj new` 或 `jj commit` 手动推进变更后再调整

**多功能改动**：如果改动同时涉及多项功能，可以手动添加描述，对新添加的修改进行 `squash` 或 `split`。

**历史变更**：已有的修改（非本次对话新增），就算不合理也放过，不做处理。

## 编码约定

- 注释和文档使用中文
- 错误类型继承自 `DiceLangError`，按组件分 `LexerError` / `ParserError` / `EvaluatorError`。未完成的功能使用`TodoError`
