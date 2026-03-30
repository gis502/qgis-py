import logging  # 导入自定义日志工具
from qgis._core import QgsScaleBarSettings, QgsLayoutExporter, QgsCoordinateTransform, QgsCoordinateReferenceSystem, \
    QgsPointXY, QgsGeometry, QgsRectangle


class MapUtils:
    """出图工具类（封装地图缩放、文本更新、比例尺调整、导出等功能）"""

    def __init__(self, config, project, layout):
        self.config = config  # 配置参数
        self.project = project  # QGIS项目对象
        self.layout = layout  # 布局对象（用于地图排版）
        self.imap = layout.itemById("Map")  # 获取ID为"Map"的地图项

    # 缩放
    def Zoom(self, rule, data):
        logging.info(data)  # 记录缩放参数日志
        zoom = MapZoom(self.project, self.layout, self.imap)  # 创建缩放操作对象
        # 2024  Zoom转换（将数字规则映射为方法名）
        # NO("10", "不缩放"),
        # PAN("11", "平移"),
        # LAYER("12", "单图层"),
        # M_LAYER("13", "多图层"),
        # DISTANCE("14", "距离"),
        # M_LAYER2("15", "按图层合并缩放");
        if rule == "11":
            rule = "FlatToCenter"  # 平移至中心点
        elif rule == "12":
            rule = "Layer"  # 单图层缩放
        elif rule == "13":
            rule = "LayerIntersect"  # 多图层相交缩放
        elif rule == "14":
            rule = "CenterDistance"  # 中心距离缩放
        elif rule == "15":
            rule = "LayerMerged"  # 多图层合并缩放
        else:
            rule = "FlatToCenter"  # 默认平移至中心点
        eval("zoom." + rule + "(data)")  # 动态调用对应缩放方法

    # 文本更新
    def Update(self, model, key):
        label = self.layout.itemById(key)  # 获取布局中ID为key的文本标签
        if (label != None):
            label.setText(model[key])  # 更新标签文本为model中key对应的值

    # 比例尺更新
    def UpdateScale(self):
        ScaleBar = self.layout.itemById("ScaleBar")  # 获取ID为"ScaleBar"的比例尺控件
        if ScaleBar == None:
            logging.warning("比例尺不存在或控件标识不等于 ScaleBar")  # 日志警告
            return
        # 设置比例尺段大小模式为"适应宽度"
        ScaleBar.setSegmentSizeMode(QgsScaleBarSettings.SegmentSizeMode.SegmentSizeFitWidth)
        ScaleBar.setMaximumBarWidth(70)  # 最大宽度
        ScaleBar.setMinimumBarWidth(40)  # 最小宽度

    # 布局设置器
    def QgsLayoutSettings(self):
        dpi = self.config["qgis"]["exportDpi"]  # 设置dpi
        # 设置多个导出格式
        settings = {
            'PDF': QgsLayoutExporter.PdfExportSettings(),
            'PNG': QgsLayoutExporter.ImageExportSettings(),
            'JPG': QgsLayoutExporter.ImageExportSettings(),
            'SVG': QgsLayoutExporter.SvgExportSettings()
        }

        for img_format in ['PNG', 'JPG']:
            settings[img_format].dpi = dpi
        settings['JPG'].jpegQuality = 85

        return settings['PNG']

    # 导出图片
    def Export(self, path):
        try:
            qle = QgsLayoutExporter(self.layout)  # 创建布局导出器
            # 布局设置
            setting = self.QgsLayoutSettings()
            # 导出为图片
            res = qle.exportToImage(path, setting)
        except Exception as e:
            raise Exception(f"导出失败... {str(e)}")


class MapZoom:
    """地图缩放操作类（封装多种缩放逻辑）"""

    def __init__(self, project, layout, imap):
        self.project = project  # QGIS项目对象
        self.layout = layout  # 布局对象
        self.imap = imap  # 地图项对象

    # 设置坐标系转换
    def SetSrc(self, crs):
        qct = QgsCoordinateTransform()  # 坐标系转换对象
        qct.setDestinationCrs(self.imap.crs())  # 目标坐标系为地图当前坐标系
        if crs == None:
            qct.setSourceCrs(QgsCoordinateReferenceSystem("EPSG:4326"))  # 源坐标系默认WGS84（经纬度）
        else:
            qct.setSourceCrs(crs)  # 自定义源坐标系
        return qct

    # 平移至中心点
    def FlatToCenter(self, data):
        logging.info("平移至中心点")
        qct = self.SetSrc(None)  # 源坐标系为WGS84
        point = QgsPointXY(float(data["X"]), float(data["Y"]))  # 解析中心点坐标（经纬度）
        qgm = QgsGeometry.fromWkt(point.asWkt())  # 转换为QGIS几何对象
        # 坐标转换（从源坐标系到地图坐标系）
        qgm.transform(qct, QgsCoordinateTransform.TransformDirection.ForwardTransform)
        cpoint = qgm.asPoint()  # 转换后的中心点
        # 保持当前地图宽度和高度，以新中心点创建矩形范围
        qr = QgsRectangle.fromCenterAndSize(cpoint, self.imap.extent().width(), self.imap.extent().height())
        self.imap.zoomToExtent(qr)  # 缩放至该范围（实现平移）

    # 中心距离缩放（以中心点为圆心，指定距离为半径缩放）
    def CenterDistance(self, data):
        logging.info("中心距离")
        qct = self.SetSrc(None)
        point = QgsPointXY(float(data["X"]), float(data["Y"]))  # 中心点坐标
        qgm = QgsGeometry.fromWkt(point.asWkt())
        qgm.transform(qct, QgsCoordinateTransform.TransformDirection.ForwardTransform)
        # 缓冲距离（单位：公里，转换为米后缓冲），并扩大10%范围
        box = qgm.buffer(float(data["value"]) / 1000, 100).boundingBox()  # 平面 4326
        # box = qgm.buffer(float(data["value"])/111,100).boundingBox()#投影坐标系下的缓冲计算
        self.imap.zoomToExtent(box.buffered(box.width() * 0.1))

    # 按单图层缩放（缩放至指定图层范围）
    def Layer(self, data):
        logging.info("按图层缩放")
        layers = self.project.mapLayersByName(data["value"])  # 根据名称获取图层
        if len(layers) == 0:
            logging.warning("图层不存在：" + data["value"])  # 图层不存在时警告
            return
        layer = layers[0]
        if layer.featureCount() == 0.0:  # 图层无要素时，默认平移至中心点
            self.FlatToCenter(data)
            return

        qct = self.SetSrc(layer.crs())  # 源坐标系为图层坐标系
        # 将图层范围转换为几何对象
        qgm = QgsGeometry.fromWkt(layer.extent().asWktPolygon())
        qgm.transform(qct, QgsCoordinateTransform.TransformDirection.ForwardTransform)  # 转换到地图坐标系
        box = qgm.boundingBox()  # 获取范围矩形
        self.imap.zoomToExtent(box.buffered(box.width() * 0.1))  # 扩大10%范围后缩放

    # 多图层合并缩放（缩放至多个图层的合并范围）
    def LayerMerged(self, data):
        logging.info("多图层合并")
        layers = data["value"].split(",")  # 图层名称以逗号分隔
        box = None
        for lay in layers:
            temp = self.project.mapLayersByName(lay)
            if len(temp) == 0:
                logging.warning("图层不存在：" + lay)
            else:
                layer = temp[0]
                qct = self.SetSrc(layer.crs())
                qgm = QgsGeometry.fromWkt(layer.extent().asWktPolygon())
                qgm.transform(qct, QgsCoordinateTransform.TransformDirection.ForwardTransform)
                if box == None:
                    box = qgm.boundingBox()  # 初始化范围
                else:
                    box.combineExtentWith(qgm.boundingBox())  # 合并范围
        if box != None:
            self.imap.zoomToExtent(box.buffered(box.width() * 0.1))  # 扩大10%范围后缩放

    # 多图层相交缩放（缩放至多个图层的相交范围）
    def LayerIntersect(self, data):
        logging.info("多图层相交")
        layers = data["value"].split(",")  # 图层名称以逗号分隔
        box = None
        for lay in layers:
            temp = self.project.mapLayersByName(lay)
            if len(temp) == 0:
                logging.warning("图层不存在：" + lay)
            else:
                layer = temp[0]
                qct = self.SetSrc(layer.crs())
                layer.selectAll()  # 选中图层所有要素
                geom = None
                # 合并选中要素的几何范围
                for feature in layer.selectedFeatureIds():
                    if geom == '':
                        geom = layer.getGeometry(feature)
                    else:
                        geom = geom.combine(layer.getGeometry(feature))
                qgm = QgsGeometry.fromWkt(geom.asWkt())
                qgm.transform(qct, QgsCoordinateTransform.TransformDirection.ForwardTransform)
                if box == None:
                    box = qgm.boundingBox()  # 初始化范围
                else:
                    box = box.intersection(qgm)  # 计算相交范围
        if box != None:
            box = box.boundingBox()
            self.imap.zoomToExtent(box.buffered(box.width() * 0.1))  # 扩大10%范围后缩放
