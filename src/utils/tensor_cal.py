import torch
def get_intersection(tensor_a, tensor_b):
    common_data = tensor_a[torch.isin(tensor_a, tensor_b)]
    return common_data