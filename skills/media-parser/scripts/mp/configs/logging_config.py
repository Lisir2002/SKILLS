import logging

# 技能场景：只输出到控制台，不写文件日志（避免污染用户目录）
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)

# 兼容原代码：导出一个通用的 logger
logger = logging.getLogger('media-parser')

def get_logger(name):
    """
    获取带名字的 logger。
    推荐用法：在每个模块开头使用
    from configs.logging_config import get_logger
    logger = get_logger(__name__)
    """
    return logging.getLogger(name)
