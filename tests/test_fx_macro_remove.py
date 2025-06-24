import json
from pathlib import Path
from core.fx_chain_handler import extract_fx_parameters, save_fx_chain_with_macros
from core.synth_preset_inspector_handler import extract_macro_information
from handlers.fx_chain_editor_handler_class import DEFAULT_MACRO_PARAMS


def test_remove_macro_assignments(tmp_path):
    src = Path("examples/Audio Effects/Auto Filter/Default Filter.json")
    dest = tmp_path / "chain.ablpreset"

    info = extract_fx_parameters(str(src))
    macros = []
    for i, pname in enumerate(DEFAULT_MACRO_PARAMS["Auto Filter"]):
        p_path = info["parameter_paths"].get(pname)
        macros.append(
            {
                "index": i,
                "name": f"Macro {i}",
                "value": 0.0,
                "parameters": [{"name": pname, "path": p_path}],
            }
        )
    res = save_fx_chain_with_macros(str(src), macros, str(dest))
    assert res["success"], res.get("message")

    m_info = extract_macro_information(str(dest))
    assert any(m["parameters"] for m in m_info["macros"])

    res = save_fx_chain_with_macros(str(dest), [], str(dest))
    assert res["success"], res.get("message")

    m_info = extract_macro_information(str(dest))
    assert not any(m["parameters"] for m in m_info["macros"])
