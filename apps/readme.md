
 # apps/main.py 顶部新增代码
 import sys
 from pathlib import Path
 import logging
 import json  # JSON数据处理
 from pydantic import BaseModel, Field
 from qgis._core import QgsApplication, QgsSettings
 from core.maps import Maps  # 导入地图处理类
 import yaml
 from fastapi import FastAPI
 import uvicorn

 app = FastAPI(
     title="QGIS 专题图导出",
     description="基于 pyqgis 的专题图制作与导出,用于生成暴雨、地震灾害类分布图",
     version="1.0.0"
 )


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
     """
         加载 application.yml 配置文件
         :param config_path: 配置文件路径（默认：apps/config/application.yml）
         :return: 解析后的配置字典
         """
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

         logging.info(f"成功加载配置文件：{config_path_str}")
         logging.info(f"配置内容：{json.dumps(config_data, ensure_ascii=False, indent=2)}")
         return config_data

     except Exception as e:
         logging.error(f"加载配置文件失败：{str(e)}", exc_info=True)
         raise  # 抛出异常，终止程序执行


 def run(model, data, config):
     try:
         root = config['qgis']['root']
         # ---初始化QGIS资源---
         QgsApplication.setPrefixPath(root, True)
         # 创建对QgsApplication的引用，第二个参数设置为False将禁用GUI
         qgs = QgsApplication([], False)
         settings = QgsSettings()
         settings.setValue("/qgis/render_decorations", False)
         settings.setValue("/qgis/parallel_rendering", True)
         settings.setValue("/qgis/use_spatial_index", True)
         # 加载提供者（QGIS数据驱动模块）
         qgs.initQgis()
         # 核心代码，地图操作
         mp = Maps(model, data, config)
         mapName = mp.load()  # 执行地图加载、处理、导出流程

         # 脚本完成后，调用exitQgis（）从内存中删除提供者和图层注册
         qgs.exitQgis()
         logging.info("qgis已退出")
         print("qgis已退出")

         return mapName
     except:
         print(sys.exc_info())  # 打印异常信息
         logging.error(sys.exc_info())  # 记录异常日志


 @app.post("/qgis/make/eq", summary="地图导出接口")
 def start(request: MapModel):
     logging.info("__main__")
     # 加载配置文件
     config = load_config()
     req = request.dict()

     print(req)

     logging.info(req)
     # 制图
     mapName = run(req, None, config)  # 带额外数据执行

     return mapName


 if __name__ == "__main__":
     # 启动FastAPI服务
     uvicorn.run(
         app="main:app",
         host="0.0.0.0",
         port=18998,
         reload=True,  # 开发环境开启，生产环境关闭
         log_level="info"
     )





if __name__ == "__main__":

    # 加载配置文件
    config = load_config()

    jobj = {
        "centerX": 109.0298,
        "centerY": 34.2985,
        "eqInfo": "时间：2025年05月20日 17时09分\r"
                  "\n震级：6.4级\r"
                  "\n位置：陕西省西安市雁塔区县XX乡",
        "event": "d9cd789c-59b5-4ba4-984d-741e6c9aab78",
        "mapLayout": "A3",
        "mapTime": "制图时间：2025年05月20日",
        "mapTitle": "陕西西安6.4级地震影响估计范围分布图（测试地震）",
        "mapUint": "制图单位：西安市应急管理局",
        "name": "暴雨城市生命线工程分布图",
        "outFile": "D:/项目/qgis-xian/qgis-xian/apps/output/img/暴雨城市生命线工程分布图.jpg",
        "path": "D:/项目/qgis-xian/qgis-xian/apps/template/storm/暴雨城市生命线工程分布图.qgz",
        "queueId": "d9cd789c-59b5-4ba4-984d-741e6c9aab7801",
        "zoomRule": "1",
        "zoomValue": ""
    }

    # jobj = json.loads(jsonModel)  # 解析为JSON对象

    # 处理第二个参数（额外数据）
    if len(sys.argv) > 2:
        # jsonData = base64.b64decode(sys.argv[2]).decode('utf-8')  # 解码额外数据
        # logging.info(jsonData)
        # run(jobj, json.loads(jsonData), config)  # 带额外数据执行
        run(jobj, None, config)  # 带额外数据执行
    else:
        run(jobj, None, config)  # 无额外数据执行

