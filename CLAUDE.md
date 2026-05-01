# DiceLang

骰子表达式解析与求值的领域特定语言（DSL），面向桌游 RPG 场景。

## 构建 & 测试

```bash
uv run pytest test/          # 运行全部测试
uv run pytest test/unit/     # 仅单元测试
uv run pytest -x             # 遇到失败即停
```

项目使用 `uv` 管理依赖，Python 3.13.5，测试框架 pytest。

## 架构

经典三阶段管线：**Lexer → Parser → Evaluator**

```
源代码字符串 → Lexer(lexer.py) → Token流 → Parser(parser.py) → AST → Evaluator(evaluator.py) → 结果
```

### 源码结构

- `tokens.py` — Token & TokenType 定义（21 种 token）
- `lexer.py` — 词法分析器，支持最长匹配、大小写无关关键字、`**`/`^` 归一化
- `astnode.py` — AST 节点定义（frozen dataclass），含 `DiceResult` 求值结果类型
- `parser.py` — Pratt parser，前缀/中缀绑定力表驱动
- `evaluator.py` — 求值器（当前为骨架，仅 raise TodoError）
- `error.py` — 错误层级：`DiceLangError → LexerError / ParserError / TodoError`

### AST 节点

| 节点 | 用途 |
|------|------|
| `NumberNode(value: int)` | 整数字面量 |
| `BinaryOpNode(op, left, right)` | 二元运算 |
| `UnaryOpNode(op, operand)` | 一元前缀运算 |
| `DiceNode(count, sides, selectors)` | 掷骰表达式 |
| `SelectorNode(selector, count)` | 后缀选择器（h/l/k/t） |
| `GroupNode(group: list[AstNode])` | 括号分组 / 参数列表 |
| `FuncCallNode(args: GroupNode)` | 函数调用 |
| `DiceResult(rolls: list[tuple[int, bool]])` | 掷骰结果（值, 是否被标记） |

### Parser 优先级（绑定力，越高越紧密）

| 运算 | 前缀 BP | 中缀 (左, 右) | 结合性 |
|------|---------|--------------|--------|
| `+` `-` | 50 | (10, 11) | 左 |
| `*` `/` `%` | — | (20, 21) | 左 |
| `^` | — | (31, 30) | 右 |
| `d` | 60 | (60, 61) | 左 |

## 当前实现状态

- **Lexer**: 完成
- **Parser**: ~60-70%。算术/unary/括号/基础掷骰可用。缺少：DICE prefix handler、选择器解析、比较运算符、if 条件表达式、变量赋值
- **Evaluator**: 未实现（骨架状态）

## 核心语义：后缀选择器链

骰子后缀选择器采用管道式设计，按源码顺序对掷骰结果集合做标记/删除变换：

| 关键字 | 全称 | 作用 |
|--------|------|------|
| `h` | highest | 标记最高 N 个 |
| `l` | lowest | 标记最低 N 个 |
| `k` | keep | 删除未标记元素，保留已标记，然后清空所有标记 |
| `t` | throw | 删除已标记元素，保留未标记，然后清空所有标记 |

**三阶段流程**：掷骰生成集合 → 顺序执行选择器链 → 对标记元素求和（无标记则对全部求和）

`k`/`t` 执行后会清空剩余元素标记，保证后续 `h`/`l` 从干净状态开始。N 超出数量时标记全部，不报错。

## 语法特征要点

- 骰子表达式：`NdS`（如 `4d6`）、裸骰 `d6`（隐式 count=1）
- 选择器链：`4d6h2`、`4d6h1l1t`、`2d6kh1`
- 爆炸骰：`3d8e`、`3d8e>5:4`、`2d6e3`（e 或 ! 均可）
- 条件映射：`3d8 if >4`、`2d8 if ==1:2`
- 成功计数：`3d10e ifc >8`（ifc = if + count 语法糖）
- 函数调用：`reroll(1d20,<,15,1)`、`max(2d6+5, 2d6+5)`
- 嵌套骰子：`(3d4)d6h1`

## 编码约定

- 数据类一律 `@dataclass(frozen=True, slots=True)`，Token 和 AST 节点不可变
- 注释和文档使用中文
- 错误类型继承自 `DiceLangError`，按组件分 `LexerError` / `ParserError`
