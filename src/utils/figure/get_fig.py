import os

import matplotlib.pyplot as plt
from loguru import logger
from matplotlib import font_manager
from matplotlib.figure import Figure

from utils.file.file_utils import FileUtils

FONT_PATH = "./data/simhei.ttf"

# 2. 检查字体文件是否存在，存在则加载
if os.path.exists(FONT_PATH):
    # 将字体文件加入到 matplotlib 的字体管理器中
    font_manager.fontManager.addfont(FONT_PATH)

    # 获取该字体的内部名称 (通常是 'SimHei')
    prop = font_manager.FontProperties(fname=FONT_PATH)
    font_name = prop.get_name()

    # 设置全局默认字体
    plt.rcParams["font.family"] = "sans-serif"  # 也就是默认使用无衬线字体系列
    plt.rcParams["font.sans-serif"] = [font_name]  # 指定该系列首选我们的字体

    # 解决负号显示问题
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
    显示并可选择性地保存 Matplotlib 图形。

    参数:
    ----------
    fig : matplotlib.figure.Figure 需要处理的 Matplotlib 画布对象。

    show : bool, optional

    save_path : str, optional 图片的保存路径 (例如 'my_plots/chart.png')。如果为 None，则不保存图片。默认为 None。

    dpi : int, optional 保存图片的分辨率 (dots per inch)，数值越高图片越清晰。默认为 300，适合大多数报告和出版物。
    """
    # 自动调整布局，确保标题、标签等不会重叠
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- 保存逻辑 ---
    if save_path:
        try:
            # 确保保存目录存在，如果不存在则创建
            directory = os.path.dirname(save_path)
            FileUtils.ensure_dir(directory)
            fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
            logger.info(f"图片已成功保存到: {save_path}")

        except Exception as e:
            logger.info(f"错误：保存图片失败。原因: {e}")

    # --- 显示逻辑 ---
    if show:
        plt.show()

    # 关闭图形对象以释放内存，这是一个好习惯，尤其是在循环中生成大量图形时
    plt.close(fig)
