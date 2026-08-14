"""Treeview 列宽自适应管理（融入自 V1.1.1 分支，恢复自 Git 历史 a13a4be）

提供按权重分配列宽 + 监听窗口尺寸变化自动重分配 + 用户拖拽后停止自动调整的智能行为。
设计:
  - 每列配置一个 weight (权重, 默认 1.0)
  - 初次显示时, 按 weight 比例分配可用宽度
  - 用户手动拖拽列分隔线后, 该列被标记为 "locked", 不再参与自动分配
  - 提供 reset_column_widths() 方法重置所有列为自动模式
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional


class ColumnResizer:
    """Treeview 列宽自适应管理器"""

    def __init__(self, tree: ttk.Treeview, weights: Optional[Dict[str, float]] = None,
                 min_width: int = 60, max_width: int = 600):
        self.tree = tree
        self.weights: Dict[str, float] = dict(weights) if weights else {}
        self.min_width = int(min_width)
        self.max_width = int(max_width)
        # 用户已手动调整过的列(不再参与自动分配)
        self._locked: set = set()
        self._last_total_width: int = 0
        self._resize_after_id: Optional[str] = None
        # 列出所有列
        self._all_columns: list = list(tree["columns"])

        # 为未指定 weight 的列设置默认值 1.0
        for col in self._all_columns:
            if col not in self.weights:
                self.weights[col] = 1.0

        # 监听列分隔线拖拽(标记为 locked)
        self._bind_heading_drag_detection()

        # 监听 Treeview 尺寸变化
        self.tree.bind("<Configure>", self._on_configure, add="+")

    def _bind_heading_drag_detection(self):
        """监听 heading 区域的鼠标按下/拖动事件, 用于检测用户调整列宽"""
        # ttk.Treeview 的 heading 拖动通过 ButtonPress-1 在 heading 区域触发
        # 我们监听列宽变化: 如果某列宽度变化且非程序触发, 则标记为 locked
        self._prev_widths: Dict[str, int] = {}
        self.tree.bind("<ButtonPress-1>", self._on_button_press, add="+")
        self.tree.bind("<ButtonRelease-1>", self._on_button_release, add="+")
        self._dragging = False

    def _on_button_press(self, event):
        # 检测是否点击在 heading 区域的列分隔线附近
        if self.tree.identify_region(event.x, event.y) == "heading":
            self._dragging = True
            self._prev_widths = {col: int(self.tree.column(col, "width"))
                                 for col in self._all_columns}

    def _on_button_release(self, event):
        if not self._dragging:
            return
        self._dragging = False

        # 比较前后列宽, 找出哪列被用户调整过
        for col in self._all_columns:
            cur_w = int(self.tree.column(col, "width"))
            prev_w = self._prev_widths.get(col, cur_w)
            if abs(cur_w - prev_w) > 2:
                self._locked.add(col)

    def _on_configure(self, event):
        """Treeview 尺寸变化时, 按权重重新分配列宽 (locked 列保持不变)"""
        try:
            if not self.tree.winfo_exists():
                return
        except tk.TclError:
            return
        # 防抖: 多次 Configure 事件合并为一次重分配
        if self._resize_after_id is not None:
            try:
                self.tree.after_cancel(self._resize_after_id)
            except Exception:
                pass
        try:
            self._resize_after_id = self.tree.after(50, self._do_resize)
        except tk.TclError:
            self._resize_after_id = None

    def _do_resize(self):
        self._resize_after_id = None
        try:
            if not self.tree.winfo_exists():
                return
            tree_width = int(self.tree.winfo_width())
        except tk.TclError:
            return
        except Exception:
            return
        if tree_width <= 1:
            return  # 还未布局完成

        # 取出需要分配的列(非 locked)
        auto_cols = [c for c in self._all_columns if c not in self._locked]
        if not auto_cols:
            return  # 所有列都被锁定, 不再自动分配

        # 计算可用宽度 = 总宽 - locked 列已占宽度
        locked_width = sum(int(self.tree.column(c, "width")) for c in self._locked)
        # 减去滚动条宽度估计(20px)和边距
        avail = max(self.min_width * len(auto_cols), tree_width - locked_width - 24)

        # 按权重分配
        total_weight = sum(self.weights.get(c, 1.0) for c in auto_cols)
        if total_weight <= 0:
            total_weight = float(len(auto_cols))

        for col in auto_cols:
            w = self.weights.get(col, 1.0) / total_weight * avail
            w = max(self.min_width, min(self.max_width, int(w)))
            self.tree.column(col, width=w, stretch=True)

    def shutdown(self):
        """取消所有 pending 的 after 回调（窗口显式关闭前调用，防退出噪声）"""
        if self._resize_after_id is not None:
            try:
                self.tree.after_cancel(self._resize_after_id)
            except Exception:
                pass
            self._resize_after_id = None

    def reset_column_widths(self):
        """重置所有列为自动模式, 立即按权重重新分配"""
        self._locked.clear()
        self._do_resize()

    def set_weights(self, weights: Dict[str, float]):
        """更新权重并立即重新分配"""
        self.weights.update(weights)
        for col in self._all_columns:
            if col not in self.weights:
                self.weights[col] = 1.0
        self._locked.clear()
        self._do_resize()

    def get_column_state(self) -> Dict[str, int]:
        """获取当前列宽状态 (用于持久化)"""
        return {col: int(self.tree.column(col, "width")) for col in self._all_columns}

    def restore_column_state(self, state: Dict[str, int]):
        """恢复列宽状态 (从持久化数据)"""
        for col, w in state.items():
            if col in self._all_columns:
                self.tree.column(col, width=int(w))
                self._locked.add(col)
