def load_layout(config, layout):
    final = {}
    for item in layout:
        if item["fieldName"] not in config.keys():
            final[item["fieldName"]] = item["defaultValue"]
        else:
            final[item["fieldName"]] = config[item["fieldName"]]
    return final

def get_item_to_save_from_layout(config, layout):
    config_to_save={}
    for item in layout:
        if item["fieldName"] in config.keys():
            config_to_save[item["fieldName"]] = config[item["fieldName"]]
    return config_to_save