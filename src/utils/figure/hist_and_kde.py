import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Union

# --- 组件 1: 可以在指定区域绘制直方图 ---
def draw_histogram(data: Union[List[float], np.ndarray], 
                   ax: plt.Axes = None, 
                   bins: int = 50, 
                   title: str = '数据分布直方图', 
                   xlabel: str = '数值', 
                   ylabel: str = '频数'):
    """
    在指定的 Matplotlib Axes 对象上绘制直方图。
    如果未提供 ax，则会创建一个新的图窗来绘制。
    """
    create = False
    if ax is None:
        # 如果是独立调用，自己创建画布和子图
        fig, ax = plt.subplots(figsize=(10, 6))
        create = True
        
    ax.hist(data, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    if create:
        return fig, ax
    return None, ax

# --- 组件 2: 可以在指定区域绘制KDE图 ---
def draw_kde(data: Union[List[float], np.ndarray], 
             ax: plt.Axes = None,
             title: str = '数据核密度估计图', 
             xlabel: str = '数值', 
             ylabel: str = '密度'):
    """
    在指定的 Matplotlib Axes 对象上绘制KDE图。
    如果未提供 ax，则会创建一个新的图窗来绘制。
    """
    create = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        create = True
        
    sns.kdeplot(data, ax=ax, fill=True, color='coral', lw=3)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    if create:
        return fig, ax
    return None, ax
