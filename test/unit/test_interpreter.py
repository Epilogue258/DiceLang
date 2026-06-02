"""
Interpreter 单元测试

覆盖 compile → interpret → __iter__ 全链路，
着重测试 ErrorRes / ExprRes 的分发与分离。
VarDef / MacroDef 预留空接口，待实现后填入。
"""

import random

import pytest

from DiceLang.error import DiceLangError, TodoError
from DiceLang.interpreter import Interpreter
from DiceLang.result import ErrorRes, ExprRes, MacroDefRes, Result, VarDefRes

RNG = random.Random(42)


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def results(text: str) -> list[Result]:
    """便捷入口：编译并求值，返回 Result 列表。
    每次调用创建新的 Interpreter 并使用独立 RNG 保证可复现。"""
    interp = Interpreter(text, rng=random.Random(42))
    return list(interp)


def _log(source: str, result: Result) -> None:
    is_err = isinstance(result, ErrorRes)
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result.value}{_Color.RESET}" if is_err else str(result)
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={source!r}  [{tag}]\n  {indented}")


# ============================================================
# ErrorRes / ExprRes 分发
# ============================================================


def test_expr_res_basic():
    """正常表达式应返回 ExprRes"""
    [res] = results("2+3")
    _log("2+3", res)
    assert isinstance(res, ExprRes)
    assert res.value == 5


def test_error_res_compile():
    """compile 阶段错误应返回 ErrorRes（非法字符）"""
    [res] = results("1 @ 2")
    _log("1 @ 2", res)
    assert isinstance(res, ErrorRes)
    assert isinstance(res.value, DiceLangError)


def test_error_res_eval():
    """eval 阶段错误应返回 ErrorRes（除零）"""
    [res] = results("1/0")
    _log("1/0", res)
    assert isinstance(res, ErrorRes)
    assert isinstance(res.value, DiceLangError)


def test_mixed_valid_and_error():
    """多条语句中，ErrorRes 与 ExprRes 正确分离，互不影响。
    先打印全部结果再断言，确保失败时能看到完整输出。"""
    rs = results("1+2; 1/0; 3*4")
    for i, r in enumerate(rs):
        _log(f"stmt {i}: ", r)
    assert len(rs) == 3
    assert isinstance(rs[0], ExprRes) and rs[0].value == 3
    assert isinstance(rs[1], ErrorRes)
    assert isinstance(rs[2], ExprRes) and rs[2].value == 12


# ============================================================
# 分号分隔
# ============================================================


def test_single_statement():
    """单条语句返回一个 Result"""
    assert len(results("42")) == 1


def test_multiple_statements():
    """分号分隔多条语句，各自独立求值"""
    rs = results("1; 2; 3")
    assert len(rs) == 3
    for i, r in enumerate(rs):
        assert isinstance(r, ExprRes)
        assert r.value == i + 1


def test_trailing_semicolon():
    """尾随分号不产生多余空语句"""
    rs = results("1+1; ")
    assert len(rs) == 1
    assert isinstance(rs[0], ExprRes)
    assert rs[0].value == 2


def test_consecutive_semicolons():
    """连续分号不产生多余空语句"""
    rs = results("1+1;;;2+2")
    assert len(rs) == 2


# ============================================================
# ExprRes 步骤遍历
# ============================================================


def test_steps_iteration():
    """ExprRes 应支持 for 循环遍历化简步骤"""
    [res] = results("3d6+5")
    assert isinstance(res, ExprRes)
    steps = list(res)
    assert len(steps) >= 2  # 至少原式 + 最终结果
    assert "3D6 + 5" in steps[0]
    assert str(res.value) == steps[-1]


def test_steps_str():
    """ExprRes.__str__ 输出调试格式（Step n: ...）"""
    [res] = results("1+2")
    s = str(res)
    assert "Step 0" in s
    assert "Step 1" in s
    assert "3" in s


# ============================================================
# 骰子表达式
# ============================================================


def test_dice_simple():
    """单骰表达式"""
    [res] = results("1d6")
    assert isinstance(res, ExprRes)
    assert 1 <= res.value <= 6


def test_dice_deterministic():
    """固定种子下骰子结果确定"""
    [res1] = results("2d6")
    [res2] = results("2d6")
    assert isinstance(res1, ExprRes)
    assert isinstance(res2, ExprRes)
    assert res1.value == res2.value


# ============================================================
# VarDef / MacroDef 预留空接口
# ============================================================


@pytest.mark.xfail(reason="VarDef 尚未实现", strict=True, raises=TodoError)
def test_vardef_unimplemented():
    """变量定义语句（预留，待实现）"""
    [res] = results("x = 5")
    assert isinstance(res, VarDefRes)


@pytest.mark.xfail(reason="Parser 尚未实现宏定义，& 被当作语法错误", strict=True)
def test_macrodef_unimplemented():
    """宏定义语句（预留，待 Parser 实现后填入）"""
    [res] = results("&foo = 2d6")
    assert isinstance(res, MacroDefRes)


# ============================================================
# 空输入边界
# ============================================================


def test_empty_input():
    """空输入不应产生 Result"""
    rs = results("")
    assert len(rs) == 0
