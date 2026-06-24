import onnx
import argparse
import os


def onnx_type_to_triton_type(onnx_type):
    mapping = {
        onnx.TensorProto.FLOAT: "TYPE_FP32",
        onnx.TensorProto.FLOAT16: "TYPE_FP16",
        onnx.TensorProto.INT8: "TYPE_INT8",
        onnx.TensorProto.INT32: "TYPE_INT32",
        onnx.TensorProto.INT64: "TYPE_INT64",
    }
    return mapping.get(onnx_type, "TYPE_FP32")


def extract_tensor_info(tensor_list):
    info = []
    for tensor in tensor_list:
        name = tensor.name
        dtype = onnx_type_to_triton_type(tensor.type.tensor_type.elem_type)

        dims = []
        for dim in tensor.type.tensor_type.shape.dim:
            if dim.HasField("dim_value"):
                dims.append(str(dim.dim_value))
            else:
                pass

        info.append({"name": name, "dtype": dtype, "dims": dims})
    return info


def generate_pbtxt_and_get_shapes(
    model_name, onnx_path, output_dir, max_batch, pref_batches
):
    model = onnx.load(onnx_path)
    inputs = extract_tensor_info(model.graph.input)
    outputs = extract_tensor_info(model.graph.output)

    pbtxt = f'name: "{model_name}"\n'
    pbtxt += 'platform: "tensorrt_plan"\n'
    pbtxt += f"max_batch_size: {max_batch}\n\n"

    for inp in inputs:
        pbtxt += "input [\n  {\n"
        pbtxt += f'    name: "{inp["name"]}"\n'
        pbtxt += f'    data_type: {inp["dtype"]}\n'
        pbtxt += f'    dims: [ {", ".join(inp["dims"])} ]\n'
        pbtxt += "  }\n]\n\n"

    for out in outputs:
        pbtxt += "output [\n  {\n"
        pbtxt += f'    name: "{out["name"]}"\n'
        pbtxt += f'    data_type: {out["dtype"]}\n'
        pbtxt += f'    dims: [ {", ".join(out["dims"])} ]\n'
        pbtxt += "  }\n]\n\n"

    if max_batch > 0:
        pref_str = ", ".join(map(str, pref_batches))
        pbtxt += "dynamic_batching {\n"
        pbtxt += f"  preferred_batch_size: [ {pref_str} ]\n"
        pbtxt += "  max_queue_delay_microseconds: 1000\n"
        pbtxt += "}\n\n"

    pbtxt += "instance_group [\n  {\n    count: 2\n    kind: KIND_GPU\n  }\n]\n"

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "config.pbtxt"), "w") as f:
        f.write(pbtxt)

    main_input = inputs[0]
    input_name = main_input["name"]

    has_dynamic_batch = any(not str(d).isdigit() for d in main_input["dims"])
    if has_dynamic_batch or main_input["dims"][0] == "-1" or main_input["dims"][0] == "None" or not str(main_input["dims"][0]).isdigit():
        base_shape = "x".join(main_input["dims"][1:])
        min_shape = f"{input_name}:1x{base_shape}"
        opt_shape = f"{input_name}:4x{base_shape}"
        max_shape = f"{input_name}:{max_batch}x{base_shape}"
        print(f"SHAPES={min_shape};{opt_shape};{max_shape}")
    else:
        print("SHAPES=STATIC")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx_path", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--max_batch", type=int, default=8)
    parser.add_argument("--pref_batches", nargs="+", type=int, default=[4, 8])
    args = parser.parse_args()

    generate_pbtxt_and_get_shapes(
        args.model_name,
        args.onnx_path,
        args.output_dir,
        args.max_batch,
        args.pref_batches,
    )
