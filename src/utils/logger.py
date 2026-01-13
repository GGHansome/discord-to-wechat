import logging

def setup_logger(name: str = "root") -> logging.Logger:
    """配置并返回Logger实例"""
    # 避免重复添加handler
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的Logger"""
    return logging.getLogger(name)

