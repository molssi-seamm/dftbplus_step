import json
from pathlib import Path
import pkg_resources

from seamm_util import element_data


atno = {symbol: d["atomic number"] for symbol, d in element_data.items()}


def computational_models_metadata():
    """Create the metadata for the computational models from the paramater metadata."""
    data_path = Path(pkg_resources.resource_filename(__name__, "data"))
    path = data_path / "metadata.json"
    with open(path) as fd:
        package_data = json.load(fd)

    models = {}
    for base_model, base_model_data in package_data.items():
        models[base_model] = {}
        model_data = models[base_model]["models"] = {}
        for tmp, data in base_model_data["datasets"].items():
            dataset = tmp.split(" - ")[1]
            if "element sets" in data:
                symbols = set()
                for element_set in data["element sets"]:
                    symbols |= set(element_set)
                elements = [f"{z}" for z in sorted([atno[s] for s in symbols])]
                if "parent" not in data or data["parent"] is None:
                    if dataset not in model_data:
                        model_data[dataset] = {"parameterizations": {}}
                    name = dataset
                else:
                    parent = data["parent"]
                    if parent not in model_data:
                        model_data[parent] = {"parameterizations": {}}
                    name = parent
                pdata = model_data[name]["parameterizations"][dataset] = {}
                pdata["code"] = "dftb+"
                pdata["periodic"] = True
                pdata["reactions"] = True
                pdata["optimization"] = True
                pdata["elements"] = ",".join(elements)
            elif "elements" in data:
                elements = data["elements"]
                if dataset not in model_data:
                    model_data[dataset] = {"parameterizations": {}}
                pdata = model_data[dataset]["parameterizations"][dataset] = {}
                pdata["code"] = "dftb+"
                pdata["periodic"] = True
                pdata["reactions"] = True
                pdata["optimization"] = True
                pdata["elements"] = elements
    return models
