import logging

def Filter(project, model):
    """
    图层过滤，按照不同的规则进行条件过滤（根据event和queueId筛选要素）
    """
    if model == None:
        logging.warning("过滤参数为空！！！")
        return

    logging.info("图层过滤")
    # 需要按event过滤的图层名称
    eqid = ["eqcenter", "震中"]
    # 需要按eqqueue_id过滤的图层名称（人员伤亡、经济损失等相关图层）
    eqidAndBatch = ["intensity", "intensity_mian", "dz_ryss", "dz_jjss", "dz_rysw", "dz_jzph", "dz_xzjl"]

    # 按event字段过滤图层（震中相关图层）
    logging.info("图层过滤--" + "event = '" + model["event"] + "'")

    for i in eqid:
        layers = project.mapLayersByName(i)  # 获取图层
        if len(layers) > 0:
            layer = project.mapLayersByName(i)[0]
            # 设置图层子集字符串（过滤条件）
            layer.setSubsetString("event = '" + model["event"] + "'")

    # 按eqqueue_id字段过滤图层（灾害相关图层）
    logging.info("图层过滤--" + "eqqueue_id = '" + model["queueId"] + "'")

    for i in eqidAndBatch:
        layers = project.mapLayersByName(i)
        if len(layers) > 0:
            layer = project.mapLayersByName(i)[0]
            layer.setSubsetString("eqqueue_id = '" + model["queueId"] + "'")
