def filter_self_info(entity, is_enhance, ignore_list):
    mes = {}
    for i in entity:
        if i in ignore_list:
            continue
        if not is_enhance:
            if i.find("uncertain_") != -1:
                continue
        mes[i] = entity[i]
    return mes