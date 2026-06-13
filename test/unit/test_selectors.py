"""
选择器化简步骤测试

验证 h/l/k/t 选择器逐步化简时每一步的字符串输出。
使用 Lexer → Parser → Evaluator 链路。
"""

import random

import pytest

from DiceLang.error import DiceLangError
from DiceLang.evaluator import Evaluator
from DiceLang.lexer import Lexer
from DiceLang.parser import Parser
from DiceLang.result import ErrorRes, ExprRes


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def _log(source: str, result) -> None:
    is_err = isinstance(result, (DiceLangError, ErrorRes))
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result.value}{_Color.RESET}" if isinstance(result, ErrorRes) else (
        f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    )
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={source!r}  [{tag}]\n  {indented}")


def eval_steps(expr: str) -> list[str]:
    """求值并返回化简步骤字符串列表。"""
    tokens = Lexer.tokenize(expr)
    stmt = Parser(tokens).parse()
    result = Evaluator(rng=random.Random(42)).eval(stmt)  # 每次新建 RNG，保证可复现
    assert isinstance(result, ExprRes), f"期望 ExprRes, 得到 {type(result).__name__}: {result}"
    return list(result)


# ============================================================


def test_selector_steps_h2():
    """4d6h2：投骰 → 标记最高2个 → 求和"""
    steps = eval_steps("4d6h2")
    _log("4d6h2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "12"]


def test_selector_steps_h2k():
    """4d6h2k：投骰 → 标记 → 保留 → 求和"""
    steps = eval_steps("4d6h2k")
    _log("4d6h2k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "[6, 6]", "12"]


def test_selector_steps_h2t():
    """4d6h2t：投骰 → 标记 → 丢弃 → 求和"""
    steps = eval_steps("4d6h2t")
    _log("4d6h2t", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "[1, 1]", "2"]


def test_selector_steps_h3l3():
    """4d6h3l3：全选 = 全求"""
    steps = eval_steps("4d6h3l3")
    _log("4d6h3l3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), (1), 1]", "[(6), (6), (1), (1)]", "14"]


def test_selector_steps_t():
    """4d6t：无标记，t 不变"""
    steps = eval_steps("4d6t")
    _log("4d6t", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[6, 6, 1, 1]", "14"]


def test_selector_steps_k():
    """4d6k：无标记，k 丢弃全部 → 0"""
    steps = eval_steps("4d6k")
    _log("4d6k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[]", "0"]


def test_selector_steps_if():
    """4d6 if>4：标记大于4的元素"""
    steps = eval_steps("4d6 if>4")
    _log("4d6 if>4", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "12"]


def test_selector_steps_ifc():
    """4d6 ifc>4：标记 → 计数（跳过中间 [(1),(1)] 步骤）"""
    steps = eval_steps("4d6 ifc>4")
    _log("4d6 ifc>4", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "2"]


def test_selector_steps_count():
    """4d6 count：无标记 → 统计全部"""
    steps = eval_steps("4d6 count")
    _log("4d6 count", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "4"]


# ============================================================
# 选择器参数含表达式
# ============================================================


@pytest.mark.xfail(reason="selector 参数含表达式尚未支持", strict=True, raises=AttributeError)
def test_selector_dynamic_h():
    """4d6 h(1d6) → 1d6=3 → h3 → 标记最高3 → 13"""
    steps = eval_steps("4d6 h(1d6)")
    _log("4d6 h(1d6)", steps)
    # [6,6,1,1] → h3 → [(6),(6),(1),1] → 13
    assert steps[-1] == "13"


@pytest.mark.xfail(reason="selector 参数含表达式尚未支持", strict=True, raises=AttributeError)
def test_selector_dynamic_l():
    """4d6 l(2d4+3) → 2d4+3=5 → l5 → 全标记 → 14"""
    steps = eval_steps("4d6 l(2d4+3)")
    _log("4d6 l(2d4+3)", steps)
    assert steps[-1] == "14"


@pytest.mark.xfail(reason="selector 参数含表达式尚未支持", strict=True, raises=AttributeError)
def test_selector_dynamic_if():
    """4d6 if>(3d6) → 3d6=5 → if>5 → 标记>5 → 12"""
    steps = eval_steps("4d6 if>(3d6)")
    _log("4d6 if>(3d6)", steps)
    assert steps[-1] == "12"


# ============================================================
# MapMod (:N) 映射
# ============================================================


def test_mapmod_if():
    """4d6 if>4 : 5 → [6,6,1,1] 标记>4 → [(6),(6),1,1] → :5 → [5,5,1,1] → 12"""
    steps = eval_steps("4d6 if>4 : 5")
    _log("4d6 if>4 : 5", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "[5, 5, 1, 1]", "12"]


def test_mapmod_if_eq():
    """4d6 if ==1 : 2 → [6,6,1,1] 标记==1 → [6,6,(1),(1)] → :2 → [6,6,2,2] → 16"""
    steps = eval_steps("4d6 if ==1 : 2")
    _log("4d6 if ==1 : 2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[6, 6, (1), (1)]", "[6, 6, 2, 2]", "16"]


def test_mapmod_h():
    """4d6 h2 : 3 → [6,6,1,1] 标记最高2 → [(6),(6),1,1] → :3 → [3,3,1,1] → 8"""
    steps = eval_steps("4d6 h2 : 3")
    _log("4d6 h2 : 3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[(6), (6), 1, 1]", "[3, 3, 1, 1]", "8"]


def test_mapmod_empty_match():
    """4d6 if>7 : 2 → [6,6,1,1] 无标记 → :2 空操作 → 14"""
    steps = eval_steps("4d6 if>7 : 2")
    _log("4d6 if>7 : 2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]", "[6, 6, 1, 1]", "[6, 6, 1, 1]", "14"]
