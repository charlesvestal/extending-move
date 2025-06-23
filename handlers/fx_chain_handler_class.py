#!/usr/bin/env python3
import os
import json
import logging

from handlers.base_handler import BaseHandler
from core.file_browser import generate_dir_html
from core.fx_chain_handler import parse_chain, create_chain, load_schema
from core.refresh_handler import refresh_library

logger = logging.getLogger(__name__)

DEFAULT_CHAIN = os.path.join('examples', 'Audio Effects', 'Dynamics', 'Punch Glue.json')
SAVE_DIR = '/data/UserData/UserLibrary/Audio Effects'

EFFECT_KINDS = [
    'autoFilter', 'channelEq', 'chorus', 'compressor', 'delay',
    'reverb', 'saturator', 'phaser', 'redux2'
]

class FxChainHandler(BaseHandler):
    def handle_get(self):
        base_dir = '/data/UserLibrary/Audio Effects'
        if not os.path.exists(base_dir) and os.path.exists('examples/Audio Effects'):
            base_dir = 'examples/Audio Effects'
        browser_html = generate_dir_html(
            base_dir,
            '',
            '/fx-chain',
            'preset_select',
            'select_preset',
            filter_key='fx'
        )
        core_li = (
            '<li class="dir closed" data-path="Core Library">'
            '<span>📁 Core Library</span>'
            '<ul class="hidden"></ul></li>'
        )
        if browser_html.endswith('</ul>'):
            browser_html = browser_html[:-5] + core_li + '</ul>'
        return {
            'file_browser_html': browser_html,
            'message': '',
            'selected_preset': None,
            'browser_root': base_dir,
            'browser_filter': 'fx',
            'effect_kinds': EFFECT_KINDS,
            'chain_data': None,
            'message_type': 'info',
        }

    def handle_post(self, form):
        action = form.getvalue('action')
        if action == 'select_preset':
            path = form.getvalue('preset_select')
            if not path:
                return self.format_error_response('No preset selected')
            result = parse_chain(path)
            if not result.get('success'):
                return self.format_error_response(result.get('message'))
            base_dir = '/data/UserLibrary/Audio Effects'
            if not os.path.exists(base_dir) and os.path.exists('examples/Audio Effects'):
                base_dir = 'examples/Audio Effects'
            browser_html = generate_dir_html(
                base_dir,
                '',
                '/fx-chain',
                'preset_select',
                'select_preset',
                filter_key='fx'
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'
            return {
                'file_browser_html': browser_html,
                'message': 'Loaded preset',
                'selected_preset': path,
                'browser_root': base_dir,
                'browser_filter': 'fx',
                'effect_kinds': EFFECT_KINDS,
                'chain_data': result,
                'message_type': 'success',
            }
        if action == 'new_chain':
            effects = []
            for i in range(4):
                kind = form.getvalue(f'effect{i}')
                if kind:
                    schema = load_schema(kind)
                    params = {}
                    for p, info in schema.items():
                        if info['type'] == 'number':
                            params[p] = info.get('min', 0)
                        elif info['type'] == 'boolean':
                            params[p] = False
                        elif info['type'] == 'enum' and info.get('options'):
                            params[p] = info['options'][0]
                    effects.append({'kind': kind, 'parameters': params})
            result = {
                'success': True,
                'name': form.getvalue('new_chain_name') or 'New Chain',
                'effects': effects,
                'macros': {},
            }
            base_dir = '/data/UserLibrary/Audio Effects'
            if not os.path.exists(base_dir) and os.path.exists('examples/Audio Effects'):
                base_dir = 'examples/Audio Effects'
            browser_html = generate_dir_html(
                base_dir,
                '',
                '/fx-chain',
                'preset_select',
                'select_preset',
                filter_key='fx'
            )
            core_li = (
                '<li class="dir closed" data-path="Core Library">'
                '<span>📁 Core Library</span>'
                '<ul class="hidden"></ul></li>'
            )
            if browser_html.endswith('</ul>'):
                browser_html = browser_html[:-5] + core_li + '</ul>'
            return {
                'file_browser_html': browser_html,
                'message': 'Create new chain',
                'selected_preset': None,
                'browser_root': base_dir,
                'browser_filter': 'fx',
                'effect_kinds': EFFECT_KINDS,
                'chain_data': result,
                'message_type': 'info',
            }
        if action == 'save_chain':
            name = form.getvalue('chain_name') or 'FX Chain'
            effects = []
            for i in range(4):
                kind = form.getvalue(f'effect{i}_kind')
                if not kind:
                    continue
                schema = load_schema(kind)
                params = {}
                for param in schema.keys():
                    field = f'effect{i}_{param}'
                    if field in form:
                        val = form.getvalue(field)
                        info = schema[param]
                        if info['type'] == 'number':
                            try:
                                val = float(val)
                            except ValueError:
                                val = info.get('min', 0)
                        elif info['type'] == 'boolean':
                            val = val == 'on'
                        params[param] = val
                effects.append({'kind': kind, 'parameters': params})
            macros = {}
            for m in range(8):
                choice = form.getvalue(f'macro{m}')
                if choice:
                    idx, param = choice.split(':')
                    macros[m] = {'effect_index': int(idx), 'param': param}
            os.makedirs(SAVE_DIR, exist_ok=True)
            out_path = os.path.join(SAVE_DIR, f'{name}.json')
            result = create_chain(name, effects, macros, out_path)
            if result['success']:
                refresh_library(out_path)
            return {
                'file_browser_html': '',
                'message': result['message'],
                'selected_preset': out_path if result['success'] else None,
                'browser_root': SAVE_DIR,
                'browser_filter': 'fx',
                'effect_kinds': EFFECT_KINDS,
                'chain_data': None,
                'message_type': 'success' if result['success'] else 'error',
            }
        return self.format_error_response('Unknown action')
