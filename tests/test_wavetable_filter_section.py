import handlers.wavetable_param_editor_handler_class as wpeh


def test_filter_routing_section():
    handler = wpeh.WavetableParamEditorHandler()
    assert handler._get_section("Voice_Global_FilterRouting") == "Filter"
