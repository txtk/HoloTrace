import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Union

# --- Component 1: draw a histogram in the specified area ---
def draw_histogram(data: Union[List[float], np.ndarray], 
                   ax: plt.Axes = None, 
                   bins: int = 50, 
                   title: str = '数据分布直方图', 
                   xlabel: str = '数值', 
                   ylabel: str = '频数'):
    """
    Draw a histogram on the specified Matplotlib Axes object.
    If ax is not provided, create a new figure for plotting.
    """
    create = False
    if ax is None:
        # If called standalone, create the figure and subplot locally
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

# --- Component 2: draw a KDE plot in the specified area ---
def draw_kde(data: Union[List[float], np.ndarray], 
             ax: plt.Axes = None,
             title: str = '数据核密度估计图', 
             xlabel: str = '数值', 
             ylabel: str = '密度'):
    """
    Draw a KDE plot on the specified Matplotlib Axes object.
    If ax is not provided, create a new figure for plotting.
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
