#!/usr/bin/env python3
"""Utilities for MelodicSampler presets."""
import json
import urllib.parse
import os
import shutil
import logging
from core.config import MELODIC_SAMPLER_SAMPLE_DIR

logger = logging.getLogger(__name__)


def get_melodic_sampler_sample(preset_path):
    """Return the sample name and path for a MelodicSampler preset."""
    try:
        with open(preset_path, "r") as f:
            preset_data = json.load(f)

        sample_uri = None

        def find_sampler(data):
            nonlocal sample_uri
            if sample_uri is not None:
                return
            if isinstance(data, dict):
                if data.get("kind") == "melodicSampler":
                    sample_uri = data.get("deviceData", {}).get("sampleUri")
                else:
                    for v in data.values():
                        if sample_uri is None:
                            find_sampler(v)
            elif isinstance(data, list):
                for item in data:
                    if sample_uri is None:
                        find_sampler(item)

        find_sampler(preset_data)

        if not sample_uri:
            return {
                "success": True,
                "message": "No sample loaded",
                "sample_name": None,
                "sample_path": None,
            }

        # Get filename from URI and convert to local path if needed
        name_part = sample_uri.rsplit("/", 1)[-1]
        sample_name = urllib.parse.unquote(name_part)
        if sample_uri.startswith("ableton:/user-library/Samples/"):
            sample_path = sample_uri.replace(
                "ableton:/user-library/Samples/",
                "/data/UserData/UserLibrary/Samples/",
                1,
            )
        elif sample_uri.startswith("file://"):
            sample_path = sample_uri.split("file://", 1)[1]
        else:
            sample_path = sample_uri
        sample_path = urllib.parse.unquote(sample_path)

        return {
            "success": True,
            "message": "Found sample",
            "sample_name": sample_name,
            "sample_path": sample_path,
        }

    except Exception as exc:
        logger.warning("Error reading melodic sampler preset: %s", exc)
        return {
            "success": False,
            "message": f"Error reading preset: {exc}",
            "sample_name": None,
            "sample_path": None,
        }


def replace_melodic_sampler_sample(preset_path, new_sample_path,
                                   dest_dir=MELODIC_SAMPLER_SAMPLE_DIR):
    """Replace the sample in ``preset_path`` with ``new_sample_path``.

    The new sample is copied to ``dest_dir`` and the preset's ``sampleUri``
    updated to reference the placed file. Returns a dict with ``success`` and
    ``message`` keys and the path to the updated preset.
    """
    try:
        os.makedirs(dest_dir, exist_ok=True)
        filename = os.path.basename(new_sample_path)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copy(new_sample_path, dest_path)

        encoded = urllib.parse.quote(dest_path)
        if encoded.startswith('/data/UserData/UserLibrary/Samples/'):
            sample_uri = encoded.replace(
                '/data/UserData/UserLibrary/Samples/',
                'ableton:/user-library/Samples/'
            )
        else:
            sample_uri = 'file://' + encoded

        with open(preset_path, 'r') as f:
            data = json.load(f)

        updated = False

        def apply(data_node):
            nonlocal updated
            if isinstance(data_node, dict):
                if data_node.get('kind') == 'melodicSampler':
                    if 'deviceData' not in data_node:
                        data_node['deviceData'] = {}
                    data_node['deviceData']['sampleUri'] = sample_uri
                    updated = True
                else:
                    for v in data_node.values():
                        apply(v)
            elif isinstance(data_node, list):
                for item in data_node:
                    apply(item)

        apply(data)

        if not updated:
            return {
                'success': False,
                'message': 'MelodicSampler device not found in preset'
            }

        with open(preset_path, 'w') as f:
            json.dump(data, f, indent=2)

        return {
            'success': True,
            'message': f'Replaced sample with {filename}',
            'path': preset_path,
            'sample_path': dest_path,
        }

    except Exception as exc:
        logger.error('Sample replace failed: %s', exc)
        return {'success': False, 'message': f'Error replacing sample: {exc}'}

