import logging  # Python内置日志模块
import os       # 文件路径处理模块
import datetime # 时间处理模块

def info(str):
    """记录INFO级别的日志到info_日期.log文件"""
    script_path = os.path.split(os.path.realpath(__file__))[0]  # 获取当前脚本所在目录
    nowTime = datetime.datetime.now().strftime('%Y%m%d')       # 获取当前日期（年月日）
    path = os.path.join(script_path+r'\logs', 'info_' +nowTime+".log")  # 日志文件路径（logs子目录下）
    isExists = os.path.exists(script_path+r'\logs')            # 检查logs目录是否存在
    if not isExists:
        os.makedirs(script_path+r'\logs')                      # 不存在则创建logs目录
    logger = logging.getLogger("run")                          # 创建名为"run"的日志器
    logger.setLevel(level=logging.INFO)                        # 设置日志级别为INFO
    handler = logging.FileHandler(path)                        # 创建文件处理器（指定日志文件）
    handler.setLevel(logging.INFO)                             # 处理器日志级别为INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s => %(message)s')  # 日志格式
    handler.setFormatter(formatter)                            # 绑定格式到处理器
    logger.addHandler(handler)                                 # 日志器添加处理器
    logger.info(str)                                           # 写入INFO日志
    logger.removeHandler(handler)                              # 移除处理器（避免重复输出）

def warning(str):
    """记录WARNING级别的日志到info_日期.log文件（与INFO共用文件）"""
    # 逻辑与info()基本一致，区别在于日志级别为WARNING
    script_path = os.path.split(os.path.realpath(__file__))[0]
    nowTime = datetime.datetime.now().strftime('%Y%m%d')
    path = os.path.join(script_path+r'\logs', 'info_' +nowTime+".log")
    isExists = os.path.exists(script_path+r'\logs')
    if not isExists:
        os.makedirs(script_path+r'\logs')
    logger = logging.getLogger("run")
    logger.setLevel(level=logging.WARNING)
    handler = logging.FileHandler(path)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s => %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.warning(str)
    logger.removeHandler(handler)

def error(str):
    """记录ERROR级别的日志到error_日期.log文件"""
    # 逻辑与info()基本一致，区别在于日志级别为ERROR，且日志文件前缀为error_
    script_path = os.path.split(os.path.realpath(__file__))[0]
    nowTime = datetime.datetime.now().strftime('%Y%m%d')
    path = os.path.join(script_path+r'\logs', 'error_' +nowTime+".log")
    isExists = os.path.exists(script_path+r'\logs')
    if not isExists:
        os.makedirs(script_path+r'\logs')
    logger = logging.getLogger("run")
    logger.setLevel(level=logging.ERROR)
    handler = logging.FileHandler(path)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s => %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.error(str)
    logger.removeHandler(handler)