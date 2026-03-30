import os
import sys
from pathlib import Path
import logging
import json
from pydantic import BaseModel, Field
from qgis._core import QgsApplication, QgsSettings
from core.maps import Maps
import yaml
from fastapi import FastAPI, Request
import uvicorn
import atexit

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="QGIS 专题图导出",
    description="基于 pyqgis 的专题图制作与导出,用于生成暴雨、地震灾害类分布图",
    version="1.0.0"
)

# 全局QGIS应用实例
qgs_app = None
config = None


# 模型参数
class MapModel(BaseModel):
    centerX: float = Field(..., description="地图中心点X坐标（经度）")
    centerY: float = Field(..., description="地图中心点Y坐标（纬度）")
    info: str = Field(..., description="信息文本")
    event: str = Field(..., description="事件ID（用于图层过滤）")
    mapLayout: str = Field(..., description="QGIS布局名称（如A3）")
    mapTime: str = Field(..., description="制图时间文本")
    mapTitle: str = Field(..., description="地图标题")
    mapUnit: str = Field(..., description="制图单位文本")
    name: str = Field(..., description="地图名称")
    outFile: str = Field(..., description="导出文件路径（含文件名）")
    path: str = Field(..., description="QGIS模板文件路径（.qgs/.qgz）")
    queueId: str = Field(..., description="队列ID（用于图层过滤）")
    zoomRule: str = Field(default="1", description="缩放规则")
    zoomValue: str = Field(default="", description="缩放值")


def load_config(config_path=None):
    # 默认配置文件路径
    if config_path is None:
        # 获取当前脚本所在目录的父目录，拼接配置文件路径
        current_dir = Path(__file__).resolve().parent
        config_path = current_dir / "config" / "application.yml"

    # 转换为字符串路径
    config_path_str = str(config_path)

    try:
        # 检查文件是否存在
        if not Path(config_path_str).exists():
            raise FileNotFoundError(f"配置文件不存在：{config_path_str}")

        # 读取并解析 YAML 文件
        with open(config_path_str, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return config_data

    except Exception as e:
        logging.error(f"加载配置文件失败：{str(e)}", exc_info=True)
        raise  # 抛出异常，终止程序执行


def init_qgis():
    """
    初始化QGIS应用
    """
    global qgs_app, config

    # 加载配置
    if config is None:
        config = load_config()

    # 初始化QGIS（只初始化一次）
    if qgs_app is None:
        root = config['qgis']['root']
        QgsApplication.setPrefixPath(root, True)

        # 设置环境变量
        os.environ['QGIS_PREFIX_PATH'] = os.path.join(root, "apps", "qgis")
        os.environ['PATH'] = os.path.join(root, "bin") + ";" + os.environ["PATH"]
        os.environ['PATH'] = os.path.join(root, "apps", "qgis", "bin") + ";" + os.environ["PATH"]
        os.environ['PATH'] = os.path.join(root, "apps", "Python312", "lib") + ";" + os.environ["PATH"]

        # 把QGIS的Python路径加入系统
        sys.path.insert(0, os.path.join(root, "apps", "qgis", "python"))
        sys.path.insert(0, os.path.join(root, "apps", "Python312", "Lib", "site-packages"))

        # 创建QgsApplication实例（禁用GUI）
        qgs_app = QgsApplication([], False)

        # 配置QGIS参数
        settings = QgsSettings()
        settings.setValue("/qgis/render_decorations", False)
        settings.setValue("/qgis/parallel_rendering", True)
        settings.setValue("/qgis/use_spatial_index", True)

        # 加载QGIS提供者
        qgs_app.initQgis()
        logging.info("QGIS初始化完成")

        # 注册程序退出时的清理函数
        atexit.register(cleanup_qgis)


def cleanup_qgis():
    """
    清理QGIS资源
    """
    global qgs_app
    if qgs_app is not None:
        qgs_app.exitQgis()
        qgs_app = None
        logging.info("QGIS资源已清理")


def run(model, data):
    """
    执行地图生成逻辑
    """
    try:
        # 核心代码，地图操作
        mp = Maps(model, data, config)
        mapName = mp.load()  # 执行地图加载、处理、导出流程
        logging.info(f"地图生成成功：{mapName}")
        return mapName

    except Exception as e:
        logging.error(f"地图生成失败：{str(e)}", exc_info=True)
        raise  # 抛出异常让FastAPI返回错误响应


@app.post("/qgis/make/map", summary="地图导出接口")
async def start(request: Request, model: MapModel):
    # 打印原始请求体
    raw_body = await request.body()
    logging.info(f"原始请求体：{raw_body.decode('utf-8')}")

    logging.info("接收到地图导出请求")
    # 确保QGIS已初始化
    init_qgis()

    # 转换请求参数
    req = model.dict()
    logging.info(f"解析后的参数：{json.dumps(req, ensure_ascii=False, indent=2)}")
    # 执行制图逻辑
    mapName = run(req, None)

    return mapName


if __name__ == "__main__":
    # 启动FastAPI服务
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=18998,
        reload=False,  # 生产环境必须关闭reload！reload会导致重复初始化QGIS
        log_level="info"
    )
