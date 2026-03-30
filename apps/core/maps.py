import os
import importlib  # 动态导入模块
import logging
import sys
from qgis._core import QgsProject
from .map_utils import MapUtils


class Maps:
    def __init__(self, model, data, config):
        self.model = model  # 震情基本数据
        self.data = data  # 额外数据
        self.config = config  # 配置参数

    def load(self):
        # ---加载地图模板---
        project = QgsProject.instance()  # 获取QGIS项目实例
        project.read(self.model["path"])  # 读取地图模板（.qgs或.qgz文件）

        db_config = self.config["db"]  # 需在application.yml中添加db配置

        # 遍历所有图层，更新PostgreSQL图层的连接
        for layer in project.mapLayers().values():
            if layer.providerType() == "postgres":  # 仅处理 PostgreSQL 图层
                try:
                    # 检查配置项是否完整
                    required_keys = ["host", "port", "database", "username", "password"]
                    missing_keys = [k for k in required_keys if k not in db_config]
                    if missing_keys:
                        logging.error(f"数据库配置缺失键：{missing_keys}，跳过图层 {layer.name()}")
                        continue

                    # 获取当前图层的数据源 URI
                    uri = layer.dataProvider().uri()

                    # 使用位置参数传递，而非关键字参数
                    uri.setConnection(
                        db_config["host"],  # 主机
                        str(db_config["port"]),  # 端口转换为字符串
                        db_config["database"],  # 数据库名
                        db_config["username"],  # 用户名
                        db_config["password"]  # 密码
                    )

                    # 重新设置数据源，刷新连接
                    layer.setDataSource(uri.uri(), layer.name(), "postgres")

                    # 验证图层是否有效
                    if layer.isValid():
                        logging.info(f"图层 {layer.name()} 数据库连接更新成功")
                    else:
                        logging.error(f"图层 {layer.name()} 更新连接后仍无效，请检查配置")
                except Exception as e:
                    logging.error(f"更新图层 {layer.name()} 连接失败：{str(e)}")

        logging.info("读取project完成，模板路径：" + self.model["path"] + " 画幅：" + self.model["mapLayout"])
        # logging.info("图层--" + str(len(project.mapLayersByName('eqcenter'))))  # 日志记录特定图层数量
        qLayout = project.layoutManager().layoutByName(self.model["mapLayout"])  # 获取指定名称的布局
        imap = qLayout.itemById("Map")  # 获取地图项
        mapUtils = MapUtils(self.config, project, qLayout)  # 创建地图工具实例

        # 设置坐标系（当前注释掉，未启用）
        # kid = 32000 + (700 if float(self.model["centerY"]) < 0 else 600) + (int(float(self.model["centerX"])/6)+31)
        # logging.info("设置坐标系：" + str(kid))
        # imap.setCrs(QgsCoordinateReferenceSystem(kid,QgsCoordinateReferenceSystem.CrsType.EpsgCrsId))

        # 修改格网
        # logging.info("修改格网")
        # grid = imap.grid()
        # grid.setLineSymbol(None)
        # grid.setAnnotationDisplay(QgsLayoutItemMapGrid.DisplayMode.HideAll,QgsLayoutItemMapGrid.BorderSide.Left)
        # grid.setAnnotationDisplay(QgsLayoutItemMapGrid.DisplayMode.HideAll, QgsLayoutItemMapGrid.BorderSide.Right)
        # grid.setAnnotationDisplay(QgsLayoutItemMapGrid.DisplayMode.HideAll, QgsLayoutItemMapGrid.BorderSide.Bottom)
        # grid.setAnnotationDisplay(QgsLayoutItemMapGrid.DisplayMode.HideAll, QgsLayoutItemMapGrid.BorderSide.Top)

        # 按照过滤图层，避免以前的数据干扰(动态加载map_filter.py)
        if os.path.exists(os.path.join(os.path.split(os.path.realpath(__file__))[0], 'map_filter.py')):
            # 添加模块所在目录到 Python 搜索路径
            sys.path.insert(0, os.path.split(os.path.realpath(__file__))[0])
            importlib.import_module('map_filter').Filter(project, self.model)

        # 缩放地图
        logging.info("缩放地图")
        # 调用缩放方法（参数：缩放规则、中心点坐标、缩放值）
        mapUtils.Zoom(self.model["zoomRule"],
                      {'X': self.model["centerX"], 'Y': self.model["centerY"], 'value': self.model["zoomValue"]})

        # 修改制图时间、单位、地图名称等文本
        logging.info("正在修改地震信息...")
        mapUtils.Update(self.model, "mapTitle")  # 更新地图标题
        mapUtils.Update(self.model, "mapTime")  # 更新制图时间
        mapUtils.Update(self.model, "mapUnit")  # 更新单位
        mapUtils.Update(self.model, "info")  # 更新地震信息

        # 修改比例尺
        logging.info("修改比例尺")
        mapUtils.UpdateScale()

        # 导出图片
        logging.info("导出图片")
        mapUtils.Export(self.model["outFile"])  # 导出至指定路径

        logging.info(self.model["event"] + "导出完成")  # 记录导出完成日志
        return self.model["name"]
