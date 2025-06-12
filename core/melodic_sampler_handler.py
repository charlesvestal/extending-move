#!/usr/bin/env python3
"""Utilities for MelodicSampler presets."""
import json
import urllib.parse
import os
import logging

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

        # Get filename from URI
        name_part = sample_uri.rsplit("/", 1)[-1]
        sample_name = urllib.parse.unquote(name_part)
        sample_path = urllib.parse.unquote(sample_uri)

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
