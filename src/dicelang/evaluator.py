import random
from collections.abc import Callable, Generator
from operator import eq, ge, gt, le, lt, ne
from typing import Any

import dicelang.astnode as ast

from .astnode import AstNode, MacroRefNode, NumberNode, Roll, VarNode
from .error import EvaluatorError
from .result import ErrorRes, ExprRes, MacroDefRes, Result, VarDefRes, VarInfo
from .statement import ErrorStmt, ExprStmt, MacroDefStmt, Statement, VarDefStmt
from .tokens import TokenType

# TokenType 条件运算符 → operator 比较函数
_COND_OPS = {
    TokenType.GT: gt,
    TokenType.LT: lt,
    TokenType.GTE: ge,
    TokenType.LTE: le,
    TokenType.EQ: eq,
    TokenType.NEQ: ne,
}
_EXPLODE_LIMIT = 9
_REROLL_LIMIT = 9


class Evaluator:
    """
    求值器：输入 Statement，输出 Result（包含中间化简过程）。

    唯一入口为eval方法。
    """

    def __init__(
        self, rng: random.Random | None = None, vars: dict[str, int] | None = None, macros: dict[str, AstNode] | None = None
    ):
        self.rng = rng or random.Random()
        self.context = vars if vars is not None else {}
        self.macros = macros if macros is not None else {}

    def same_family(self, father: AstNode, children: list[AstNode]) -> bool:
        """判断一组节点是否均属于同一运算家族（例如都是加法、或者都是乘法）。"""
        res_family = father.family
        for child in children:
            res_family &= child.family
        return bool(res_family)

    def fold(self, node: AstNode, children: list[Any]) -> AstNode:
        """
        在所有子节点都抵达终点的前提下，根据父节点类型进行计算，返回一个新的结果。
        """
        match node:
            case ast.BinaryOpNode():
                match node.op:
                    case TokenType.PLUS:
                        return NumberNode(value=children[0].value + children[1].value)
                    case TokenType.MINUS:
                        return NumberNode(value=children[0].value - children[1].value)
                    case TokenType.MULTIPLY:
                        return NumberNode(value=children[0].value * children[1].value)
                    case TokenType.DIVIDE:
                        if children[1].value != 0:
                            return NumberNode(value=children[0].value // children[1].value)
                        else:
                            raise EvaluatorError("除数不能为零", ast_tree=node)
                    case TokenType.POW:
                        return NumberNode(value=children[0].value ** children[1].value)
                    case TokenType.MOD:
                        return NumberNode(value=children[0].value % children[1].value)
                    case _:  # pragma: no cover
                        raise EvaluatorError(f"不支持的二元运算符: {node.op}", ast_tree=node)
            case ast.UnaryOpNode():
                match node.op:
                    case TokenType.PLUS:
                        return NumberNode(value=children[0].value)
                    case TokenType.MINUS:
                        return NumberNode(value=-children[0].value)
                    case _:  # pragma: no cover
                        raise EvaluatorError(f"不支持的一元运算符: {node.op}", ast_tree=node)
            case ast.GroupNode(selectors=selectors):
                if not selectors:
                    return children[0]
                # 递归将 selectors 分发给内部所有 DiceNode，返回空选择器的 GroupNode
                new_group = [self._distribute_selectors(c, selectors) for c in node.group]
                return ast.GroupNode(group=new_group, selectors=(), pos=node.pos, length=node.length)

            case ast.FuncCallNode():
                values = [c.value for c in children]
                match node.func:
                    case "max":
                        return NumberNode(value=max(values))
                    case "min":
                        return NumberNode(value=min(values))
                    case _:  # pragma: no cover
                        raise EvaluatorError(f"未知函数: {node.func}", ast_tree=node)
            case ast.DiceNode():
                count = children[0].value
                sides = children[1].value
                rolls = tuple(Roll(value=self.rng.randint(1, sides), sides=sides) for _ in range(count))
                # 按值降序排列
                rolls = tuple(sorted(rolls, key=lambda r: r.value, reverse=True))
                return ast.DiceResNode(rolls=rolls, selectors=tuple(node.selectors))
            case ast.DiceResNode():
                if not node.selectors:
                    return NumberNode(value=node.sum())
                return self._apply_modifier(node)
            case ast.ModifierNode():
                attrs = [self.simplify(attr) for attr in node]
                return node.reconstruct(node, attrs)
            case _:  # pragma: no cover
                raise EvaluatorError(f"无法折叠的节点: {node}", ast_tree=node)

    def _distribute_selectors(self, node: AstNode, selectors: tuple[ast.ModifierNode, ...]) -> AstNode:
        """递归将 selectors 附加到子树中所有 DiceNode 上。"""
        if isinstance(node, ast.DiceNode):
            new_sel = tuple(node.selectors) + selectors
            return ast.DiceNode(
                count=node.count,
                sides=node.sides,
                selectors=new_sel,
                pos=node.pos,
                length=node.length,
            )
        if isinstance(node, ast.NumberNode):
            return node  # 常数无选择器
        # 其他节点递归处理子节点（保留非 AstNode 值原样透传）
        new_attrs = [self._distribute_selectors(c, selectors) if isinstance(c, AstNode) else c for c in node]
        return type(node).reconstruct(node, new_attrs)

    def _mod_value(self, child: AstNode) -> int | None:
        """从 modifier 子节点提取 int 值，非 NumberNode/DiceResNode(no sel) 返回 None。"""
        if isinstance(child, ast.NumberNode):
            return child.value
        if isinstance(child, ast.DiceResNode) and not child.selectors:
            return child.value
        return None

    def _apply_modifier(self, node: ast.DiceResNode) -> AstNode:
        """对 DiceResNode 施加当前选择器（selectors[0]），返回化简后的节点。"""
        # 所有 modifier 各推进一步，子表达式可能简化
        new_mods = tuple(map(self.simplify, node.selectors))
        mod = new_mods[0]
        remaining_selectors = new_mods[1:]
        match mod:
            case ast.HighestMod(count=count_node) | ast.LowestMod(count=count_node):
                if (v := self._mod_value(count_node)) is None:
                    return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                mark_count = v
                reverse = isinstance(mod, ast.LowestMod)
                source = reversed(node.rolls) if reverse else node.rolls
                marked = 0
                result = []
                for roll in source:
                    if not roll.marked and marked < mark_count:
                        result.append(roll._replace(marked=True))
                        marked += 1
                    else:
                        result.append(roll)
                rolls = tuple(reversed(result)) if reverse else tuple(result)
                return ast.DiceResNode(rolls=rolls, selectors=remaining_selectors)
            case ast.ConditionMod(condition=condition, threshold=threshold_node):
                if (v := self._mod_value(threshold_node)) is None:
                    return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                threshold = v
                cmp = _COND_OPS[condition]
                rolls = tuple(r._replace(marked=cmp(r.value, threshold)) if not r.marked else r for r in node.rolls)
                return ast.DiceResNode(rolls=rolls, selectors=remaining_selectors)
            case ast.KeepMod():
                return ast.DiceResNode(
                    rolls=tuple(r._replace(marked=False) for r in node.rolls if r.marked),
                    selectors=remaining_selectors,
                )
            case ast.ThrowMod():
                return ast.DiceResNode(
                    rolls=tuple(r._replace(marked=False) for r in node.rolls if not r.marked),
                    selectors=remaining_selectors,
                )
            case ast.CountMod(is_ifc=is_ifc):
                name = "ifc" if is_ifc else "count"
                if remaining_selectors:
                    # ast_tree=node 提供错误上下文（哪个骰子表达式），
                    # pos/length 提供精确高亮位置（标红关键字而非整个骰子表达式）
                    raise EvaluatorError(
                        f"{name} 必须是最后一个选择器",
                        ast_tree=node,
                        pos=mod.pos,
                        length=mod.length,
                    )
                marked_count = sum(1 for r in node.rolls if r.marked)
                return NumberNode(value=marked_count if marked_count else sum(1 for _ in node.rolls))
            case ast.MapMod(map_to=map_to_node):
                if (v := self._mod_value(map_to_node)) is None:
                    return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                mapped_value = v
                new_rolls = tuple(r._replace(value=mapped_value, marked=False) if r.marked else r for r in node.rolls)
                return ast.DiceResNode(rolls=new_rolls, selectors=remaining_selectors)
            case ast.ExplodeMod(count=count_node, condition=condition, threshold=threshold_node):
                if count_node is not None:
                    if (v := self._mod_value(count_node)) is None:
                        return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                    max_per_die = min(v, _EXPLODE_LIMIT)
                else:
                    max_per_die = _EXPLODE_LIMIT
                # 爆面判定
                cmp: Callable | None = _COND_OPS.get(condition)
                if threshold_node is not None:
                    if (v := self._mod_value(threshold_node)) is None:
                        return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                    threshold = v
                else:
                    threshold = None

                def should_explode(roll) -> bool:
                    if cmp is not None:
                        return cmp(roll.value, threshold)
                    return eq(roll.value, roll.sides)

                rolls = []
                for roll in node.rolls:
                    remaining = max_per_die
                    rolls.append(roll)
                    while remaining > 0 and should_explode(roll):
                        roll = Roll(value=self.rng.randint(1, roll.sides), sides=roll.sides, marked=False, exploded=True)
                        rolls.append(roll)
                        remaining -= 1

                return ast.DiceResNode(rolls=tuple(rolls), selectors=remaining_selectors)
            case ast.RerollMod(count=count_node, condition=condition, threshold=threshold_node):
                if count_node is not None:
                    if (v := self._mod_value(count_node)) is None:
                        return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                    max_per_die = min(v, _REROLL_LIMIT)
                elif condition is None:
                    max_per_die = 1
                else:
                    max_per_die = _REROLL_LIMIT
                cmp: Callable | None = _COND_OPS.get(condition)
                if threshold_node is not None:
                    if (v := self._mod_value(threshold_node)) is None:
                        return ast.DiceResNode(rolls=node.rolls, selectors=new_mods)
                    threshold = v
                else:
                    threshold = None

                def should_reroll(roll) -> bool:
                    if cmp is not None:
                        return cmp(roll.value, threshold)
                    return True

                rolls: list[Roll] = []
                for roll in node.rolls:
                    remaining = max_per_die
                    chain = [roll.value]
                    while remaining > 0 and should_reroll(roll):
                        roll = roll._replace(value=self.rng.randint(1, roll.sides), marked=False)
                        chain.append(roll.value)
                        remaining -= 1
                    rolls.append(roll._replace(reroll_chain=tuple(chain)))

                return ast.DiceResNode(rolls=tuple(rolls), selectors=remaining_selectors)
            case _:  # pragma: no cover
                raise EvaluatorError(f"未处理的选择器类型: {type(mod).__name__}", ast_tree=node)

    def simplify(self, node: Any) -> AstNode:
        """递归化简 AST 节点：解析变量、展开宏、折叠常量、重建非可折叠节点。"""
        if not isinstance(node, AstNode):
            # 非 AstNode 的属性（如 selector 的 int 参数）直接返回，无需化简
            return node

        if isinstance(node, VarNode):
            if node.name in self.context:
                return NumberNode(value=self.context[node.name])
            raise EvaluatorError(f"未定义的变量: {node.name}", ast_tree=node)

        if isinstance(node, MacroRefNode):
            if node.name not in self.macros:
                raise EvaluatorError(f"未定义的宏: &{node.name}", ast_tree=node)
            return self.macros[node.name]

        if isinstance(node, NumberNode):
            return node

        # GroupNode 带选择器：先将选择器分发到内部 DiceNode，再走正常路径
        if isinstance(node, ast.GroupNode) and node.selectors:
            raw = [self._distribute_selectors(c, node.selectors) for c in node.group]
            node = ast.GroupNode(group=raw, selectors=(), pos=node.pos, length=node.length)

        # 不是 AstNode 的原子元素直接返回——simplify 可能递归化简子元素，
        # 但非 AstNode 的叶子节点（如 selector 的 int 参数）无需处理
        simplified_attr: list[AstNode | object] = [self.simplify(child) for child in node]
        simplified_child: list[AstNode] = [child for child in simplified_attr if isinstance(child, AstNode)]
        # 其实我想用filter的, 但是filter无法收窄类型检查, 刚好列表推导式看着也更好懂。
        if (
            all(child.family == ast.Family.ALL for child in simplified_child)  # all([]) == True
            and self.same_family(node, node.children)  # no child时显然也算同一族, 毕竟底层是father & child for loop
        ):
            return self.fold(node, simplified_child)
        return type(node).reconstruct(node, simplified_attr)

    def to_str(self, node: AstNode) -> Generator[str]:
        """
        输入 AST，输出一个生成器，依次产出每一步化简的结果字符串。

        index 0 是原式，最后一个是最终结果。
        index n刚好是第n步化简的结果。
        """
        yield str(node)
        while not isinstance(node, NumberNode):
            node = self.simplify(node)
            yield str(node)

    def eval_stmt(self, stmt: Statement) -> Result:
        """根据语句类型分发求值，返回对应的 Result。"""
        node: AstNode
        match stmt:
            case ExprStmt(value=ast):
                steps: list[str] = []
                node = ast
                while True:
                    steps.append(str(node))
                    if isinstance(node, NumberNode):
                        break
                    node = self.simplify(node)
                return ExprRes(value=node.value, steps=tuple(steps))
            case VarDefStmt(names=names, expr=expr, op=op):
                node = expr
                while True:
                    if isinstance(node, NumberNode):
                        break
                    node = self.simplify(node)
                rhs = node.value
                var_infos = []
                for name in names:
                    old = self.context.get(name)
                    match op:
                        case TokenType.ASSIGN:
                            new = rhs
                        case _ if old is None:
                            raise EvaluatorError(
                                f"复合赋值前变量未定义: {name}",
                                ast_tree=expr,
                            )
                        case TokenType.PLUS_ASSIGN:
                            new = old + rhs
                        case TokenType.MINUS_ASSIGN:
                            new = old - rhs
                        case TokenType.MULTIPLY_ASSIGN:
                            new = old * rhs
                        case TokenType.DIVIDE_ASSIGN:
                            if rhs == 0:
                                raise EvaluatorError("除数不能为零", ast_tree=expr)
                            new = old // rhs
                        case TokenType.MOD_ASSIGN:
                            if rhs == 0:
                                raise EvaluatorError("除数不能为零", ast_tree=expr)
                            new = old % rhs
                        case TokenType.POW_ASSIGN:
                            new = old**rhs
                        case _:  # pragma: no cover
                            raise EvaluatorError(f"不支持的赋值操作: {op}", ast_tree=expr)
                    self.context[name] = new
                    var_infos.append(VarInfo(name=name, old=old, value=new))
                return VarDefRes(vars=tuple(var_infos))
            case MacroDefStmt(names=names, expr=macro_expr):
                for name in names:
                    self.macros[name] = macro_expr
                return MacroDefRes(names=names, expr_str=str(macro_expr))
            case ErrorStmt(value=err):
                return ErrorRes(value=err)
            case _:  # pragma: no cover
                raise EvaluatorError(f"不支持的语句类型: {type(stmt).__name__}", ast_tree=stmt)

    def eval(self, stmt: Statement) -> Result:
        """
        求值器的唯一公共入口：输入 Statement，总是返回 Result（永不抛异常）。
        内部调用 eval_stmt() 分发求值，捕获 EvaluatorError 并包装为 ErrorRes。
        """
        try:
            return self.eval_stmt(stmt)
        except EvaluatorError as e:
            return ErrorRes(value=e)


if __name__ == "__main__":  # pragma: no cover
    # 简单测试
    from .lexer import Lexer
    from .parser import Parser

    RNG = random.Random(42)  # 固定随机种子, 以便复现

    source = "2**2**2 % 2 + 5d(3d4 + 2)"
    tokens = Lexer.tokenize(source)
    print(f"Tokens: {Lexer.format_tokens(tokens)}")
    stmt = Parser(tokens).parse()
    if isinstance(stmt, ExprStmt):
        asttree = stmt.value
    else:
        raise EvaluatorError("此示例仅支持表达式语句")
    print(f"AST: {asttree}")
    evaluator = Evaluator(rng=RNG)
    index = 0
    print("========== Evaluation Steps =========")
    for index, step in enumerate(evaluator.to_str(asttree)):
        print(f"Step {index}: {step}")
        if index >= 10:
            print("过多步骤, 可能进入死循环, 测试终止。")
            break
