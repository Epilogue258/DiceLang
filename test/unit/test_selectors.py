"""
选择器化简步骤测试

验证 h/l/k/t 选择器逐步化简时每一步的字符串输出。
使用 Lexer → Parser → Evaluator 链路。
"""

import random

import pytest

from dicelang.error import DiceLangError, TodoError
from dicelang.evaluator import Evaluator
from dicelang.lexer import Lexer
from dicelang.parser import Parser
from dicelang.result import ErrorRes, ExprRes


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
    assert steps == ["4D6", "[6, 6, 1, 1]h2", "[(6), (6), 1, 1]", "12"]


def test_selector_steps_h2k():
    """4d6h2k：投骰 → 标记 → 保留 → 求和"""
    steps = eval_steps("4d6h2k")
    _log("4d6h2k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]h2k", "[(6), (6), 1, 1]k", "[6, 6]", "12"]


def test_selector_steps_h2t():
    """4d6h2t：投骰 → 标记 → 丢弃 → 求和"""
    steps = eval_steps("4d6h2t")
    _log("4d6h2t", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]h2t", "[(6), (6), 1, 1]t", "[1, 1]", "2"]


def test_selector_steps_h3l3():
    """4d6h3l3：全选 = 全求"""
    steps = eval_steps("4d6h3l3")
    _log("4d6h3l3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]h3l3", "[(6), (6), (1), 1]l3", "[(6), (6), (1), (1)]", "14"]


def test_selector_steps_t():
    """4d6t：无标记，t 不变"""
    steps = eval_steps("4d6t")
    _log("4d6t", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]t", "[6, 6, 1, 1]", "14"]


def test_selector_steps_k():
    """4d6k：无标记，k 丢弃全部 → 0"""
    steps = eval_steps("4d6k")
    _log("4d6k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]k", "[]", "0"]


def test_selector_steps_if():
    """4d6 if>4：标记大于4的元素"""
    steps = eval_steps("4d6 if>4")
    _log("4d6 if>4", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]if > 4", "[(6), (6), 1, 1]", "12"]


def test_selector_steps_ifc():
    """4d6 ifc>4：标记 → 计数（跳过中间 [(1),(1)] 步骤）"""
    steps = eval_steps("4d6 ifc>4")
    _log("4d6 ifc>4", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]if > 4ifc", "[(6), (6), 1, 1]ifc", "2"]


def test_selector_steps_count():
    """4d6 count：无标记 → 统计全部"""
    steps = eval_steps("4d6 count")
    _log("4d6 count", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]count", "4"]


# ============================================================
# 边界情况：全选 / 全弃 / 空集
# ============================================================


def test_selector_steps_all_thrown():
    """4d6 if >=1 t：全标记 → 全丢弃 → 0"""
    steps = eval_steps("4d6 if >=1 t")
    _log("4d6 if >=1 t", steps)
    assert steps[-1] == "0"


def test_selector_steps_all_kept():
    """4d6 if >=1 k：全标记 → 全保留 → 全求和"""
    steps = eval_steps("4d6 if >=1 k")
    _log("4d6 if >=1 k", steps)
    assert steps[-1] == "14"


def test_selector_steps_none_match_t():
    """4d6 if >=7 t：无标记 → 丢弃标记 → 全保留 → 全求和"""
    steps = eval_steps("4d6 if >=7 t")
    _log("4d6 if >=7 t", steps)
    assert steps[-1] == "14"


def test_selector_steps_empty_after_k():
    """4d6 k：无标记 → 保留标记 → 全丢弃 → 0"""
    steps = eval_steps("4d6 k")
    _log("4d6 k", steps)
    assert steps[-1] == "0"


def test_selector_steps_h_overcount():
    """2d6 h5：标记数 > 骰子数 → 全标记 → 全求和"""
    steps = eval_steps("2d6 h5")
    _log("2d6 h5", steps)
    assert steps[-1] == "7"


def test_selector_steps_if_eq_mismatch():
    """1d6 if ==7 t：单骰不匹配 → 无标记 → 全保留"""
    steps = eval_steps("1d6 if ==7 t")
    _log("1d6 if ==7 t", steps)
    assert steps[-1] == "6"


# ============================================================
# 选择器参数含表达式
# ============================================================


def test_selector_dynamic_h():
    """4d6 h(1d6) → 1d6=[3] → h3 → 标记最高3 → [(6),(6),(1),1] → 13"""
    steps = eval_steps("4d6 h(1d6)")
    _log("4d6 h(1d6)", steps)
    # [6,6,1,1] → h3 → [(6),(6),(1),1] → 13
    assert steps[-1] == "13"


def test_selector_dynamic_l():
    """4d6 l(2d4+3) → 2d4+3=[3,2]+3=8 → l8 → 全标记 → 14"""
    steps = eval_steps("4d6 l(2d4+3)")
    _log("4d6 l(2d4+3)", steps)
    assert steps[-1] == "14"


def test_selector_dynamic_if():
    """4d6 if>(3d6) → 3d6=7 → if>7 → 无标记 → 14"""
    steps = eval_steps("4d6 if>(3d6)")
    _log("4d6 if>(3d6)", steps)
    assert steps[-1] == "14"


# ============================================================
# 括号 + 选择器
# ============================================================


def test_paren_dice_with_selector():
    """(3d6)h2 → 分发 → 3d6h2 → [6,1,1] → [(6),(1),1] → 7"""
    steps = eval_steps("(3d6)h2")
    _log("(3d6)h2", steps)
    assert steps == ["(3D6)h2", "([6, 1, 1]h2)", "([(6), (1), 1])", "7"]


def test_paren_expr_with_selector():
    """(1d8+1d6)h1 → 分发 → 1d8h1 + 1d6h1 → 3"""
    steps = eval_steps("(1d8+1d6)h1")
    _log("(1d8+1d6)h1", steps)
    assert steps[-1] == "3"


def test_paren_no_selector():
    """(1d8+1d6) 无选择器 → 正常求值"""
    steps = eval_steps("(1d8+1d6)")
    _log("(1d8+1d6)", steps)
    assert steps[-1] == "3"


# ============================================================
# MapMod (:N) 映射
# ============================================================


def test_mapmod_if():
    """4d6 if>4 : 5 → [6,6,1,1] 标记>4 → [(6),(6),1,1] → :5 → [5,5,1,1] → 12"""
    steps = eval_steps("4d6 if>4 : 5")
    _log("4d6 if>4 : 5", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]if > 4: 5", "[(6), (6), 1, 1]: 5", "[5, 5, 1, 1]", "12"]


def test_mapmod_if_eq():
    """4d6 if ==1 : 2 → [6,6,1,1] 标记==1 → [6,6,(1),(1)] → :2 → [6,6,2,2] → 16"""
    steps = eval_steps("4d6 if ==1 : 2")
    _log("4d6 if ==1 : 2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]if == 1: 2", "[6, 6, (1), (1)]: 2", "[6, 6, 2, 2]", "16"]


def test_mapmod_h():
    """4d6 h2 : 3 → [6,6,1,1] 标记最高2 → [(6),(6),1,1] → :3 → [3,3,1,1] → 8"""
    steps = eval_steps("4d6 h2 : 3")
    _log("4d6 h2 : 3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]h2: 3", "[(6), (6), 1, 1]: 3", "[3, 3, 1, 1]", "8"]


def test_mapmod_empty_match():
    """4d6 if>7 : 2 → [6,6,1,1] 无标记 → :2 空操作 → 14"""
    steps = eval_steps("4d6 if>7 : 2")
    _log("4d6 if>7 : 2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]if > 7: 2", "[6, 6, 1, 1]: 2", "[6, 6, 1, 1]", "14"]


# ============================================================
# 爆炸骰 (Explode)
# ============================================================


def test_explode_basic():
    """4d6e → 满值爆 → 6 爆出 3 和 2 → 19"""
    steps = eval_steps("4d6e")
    _log("4d6e", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!", "[6, D6!3, 6, D6!2, 1, 1]", "19"]


def test_explode_bang():
    """4d6! ≡ 4d6e"""
    steps = eval_steps("4d6!")
    _log("4d6!", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!", "[6, D6!3, 6, D6!2, 1, 1]", "19"]


def test_explode_with_count():
    """4d6e3 → per-die 至多 3 次爆"""
    steps = eval_steps("4d6e3")
    _log("4d6e3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!", "[6, D6!3, 6, D6!2, 1, 1]", "19"]


def test_explode_condition():
    """4d6e>=5 → >=5 才爆"""
    steps = eval_steps("4d6e>=5")
    _log("4d6e>=5", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!", "[6, D6!3, 6, D6!2, 1, 1]", "19"]


def test_explode_condition_with_count():
    """4d6e3>=5 → per-die 至多 3 次 >=5 爆"""
    steps = eval_steps("4d6e3>=5")
    _log("4d6e3>=5", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!", "[6, D6!3, 6, D6!2, 1, 1]", "19"]


def test_explode_then_h():
    """4d6!h2 → 爆完再选最高2个"""
    steps = eval_steps("4d6!h2")
    _log("4d6!h2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!h2", "[6, D6!3, 6, D6!2, 1, 1]h2", "[(6), (D6!3), 6, D6!2, 1, 1]", "9"]


def test_explode_then_keep():
    """4d6! k → 爆完无标记 → k 保留空集"""
    steps = eval_steps("4d6! k")
    _log("4d6! k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!k", "[6, D6!3, 6, D6!2, 1, 1]k", "[]", "0"]


def test_explode_then_count():
    """4d6! count → 爆完统计总数"""
    steps = eval_steps("4d6! count")
    _log("4d6! count", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]!count", "[6, D6!3, 6, D6!2, 1, 1]count", "6"]


# ============================================================
# 重掷 (Reroll)
# ============================================================


def test_reroll_basic():
    """4d6re → 无条件重掷一次"""
    steps = eval_steps("4d6re")
    _log("4d6re", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]re", "[6|3, 6|2, 1|2, 1|2]", "9"]


def test_reroll_with_count():
    """4d6re2 → 每颗至多重掷2次"""
    steps = eval_steps("4d6re2")
    _log("4d6re2", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]re2", "[6|3|2, 6|2|2, 1|6|1, 1|6|6]", "11"]


def test_reroll_condition():
    """4d6re<3 → 只重掷 <3 的骰子"""
    steps = eval_steps("4d6re<3")
    _log("4d6re<3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]re<3", "[6, 6, 1|3, 1|2|2|2|6]", "21"]


def test_reroll_condition_with_count():
    """4d6re2<3 → 每颗 <3 的至多重掷2次"""
    steps = eval_steps("4d6re2<3")
    _log("4d6re2<3", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]re2<3", "[6, 6, 1|3, 1|2|2]", "17"]


def test_reroll_then_keep():
    """4d6re>5 k → 只重掷>5的 → k 保留标记(无标记→空集)"""
    steps = eval_steps("4d6re>5 k")
    _log("4d6re>5 k", steps)
    assert steps == ["4D6", "[6, 6, 1, 1]re>5k", "[6|3, 6|2, 1, 1]k", "[]", "0"]


# ============================================================
# 复合：爆炸 + 重掷 + 选择器
# ============================================================


def test_explode_reroll_then_h():
    """4d6! re h2 → 爆 → 重掷 → 选高2"""
    steps = eval_steps("4d6! re h2")
    _log("4d6! re h2", steps)
    assert steps == [
        "4D6", "[6, 6, 1, 1]!reh2",
        "[6, D6!3, 6, D6!2, 1, 1]reh2",
        "[6|2, 3|2, 6|6, 2|1, 1|6, 1|6]h2", "[(6|2), (3|2), 6|6, 2|1, 1|6, 1|6]", "4",
    ]


def test_explode_if_map():
    """4d6e3 if>4:2 → 爆 → 标记>4 → 映射为2"""
    steps = eval_steps("4d6e3 if>4:2")
    _log("4d6e3 if>4:2", steps)
    assert steps == [
        "4D6", "[6, 6, 1, 1]!if > 4: 2",
        "[6, D6!3, 6, D6!2, 1, 1]if > 4: 2",
        "[(6), D6!3, (6), D6!2, 1, 1]: 2",
        "[2, D6!3, 2, D6!2, 1, 1]", "11",
    ]
