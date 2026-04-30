import os

import matplotlib.pyplot as plt
from loguru import logger
from matplotlib import font_manager
from matplotlib.figure import Figure

from utils.file.file_utils import FileUtils

FONT_PATH = "./data/simhei.ttf"

# 2. Check whether the font file exists and load it if present
if os.path.exists(FONT_PATH):
    # Add the font file to matplotlib's font manager
    font_manager.fontManager.addfont(FONT_PATH)

    # Get the internal name of the font, usually 'SimHei'
    prop = font_manager.FontProperties(fname=FONT_PATH)
    font_name = prop.get_name()

    # Set the global default font
    plt.rcParams["font.family"] = "sans-serif"  # Use the sans-serif font family by default
    plt.rcParams["font.sans-serif"] = [font_name]  # Prefer this font for that family

    # Fix minus-sign rendering
    plt.rcParams["axes.unicode_minus"] = False

    print(f"✅ 成功加载中文字体: {font_name}")
else:
    print(f"❌ 警告: 未找到字体文件 {FONT_PATH}，中文将无法显示！")
    print("   请从 Windows (C:\\Windows\\Fonts\\simhei.ttf) 上传该文件到服务器。")


def get_fig(title, row, col, figsize=None):
    if figsize is None:
        figsize = (16, 6 * row)
    fig, axes = plt.subplots(row, col, figsize=figsize)
    fig.suptitle(title, fontsize=20)
    return fig, axes


def finalize_plot(fig: Figure, show: bool = True, save_path: str = None, dpi: int = 300):
    """
        Display and optionally save a Matplotlib figure.
        
        Args:
            fig: Matplotlib figure object to process.
            show: Whether to display the figure.
            save_path: Optional image save path, for example 'my_plots/chart.png'.
            dpi: Image save resolution in dots per inch.
    """
    # Automatically adjust layout so titles, labels, and similar elements do not overlap
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- Save logic ---
    if save_path:
        try:
            # Ensure the save directory exists; create it if needed
            directory = os.path.dirname(save_path)
            FileUtils.ensure_dir(directory)
            fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
            logger.info(f"图片已成功保存到: {save_path}")

        except Exception as e:
            logger.info(f"错误：保存图片失败。原因: {e}")

    # --- Display logic ---
    if show:
        plt.show()

    # Close the figure to free memory, especially when generating many figures in a loop
    plt.close(fig)
