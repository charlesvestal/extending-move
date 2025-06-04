import os
import logging
import soundfile as sf
from core.refresh_handler import refresh_library

def get_wav_files(directory):
    """
    Retrieves a list of audio files (WAV and AIFF) from the specified directory.
    """
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.wav', '.aif', '.aiff')):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                audio_files.append(relative_path)
    return audio_files


def reverse_wav_file(filename, directory):
    """
    Handles reversing and un-reversing of PCM audio files (WAV, AIFF), including 24-bit.
    If the file ends with _reversed or _reverse, attempts to switch back to the original.
    Otherwise, creates a reversed version.
    Returns (success: bool, message: str, new_path: str).
    """
    filepath = os.path.join(directory, filename)
    if not os.path.isfile(filepath):
        return False, f"File does not exist: {filepath}", None

    base, ext = os.path.splitext(filename)
    ext_lower = ext.lower()

    # Toggle back to original
    if base.endswith('_reversed') or base.endswith('_reverse'):
        suffix_len = 9 if base.endswith('_reversed') else 8
        original_base = base[:-suffix_len]
        original_filename = f"{original_base}{ext_lower}"
        original_filepath = os.path.join(directory, original_filename)
        if os.path.exists(original_filepath):
            return True, f"Switched to original file: {original_filename}", original_filepath
        else:
            return False, f"Original file not found: {original_filename}", None

    # Build new reversed filename
    new_filename = f"{base}_reversed{ext_lower}"
    new_filepath = os.path.join(directory, new_filename)
    logging.info("Reversing %s -> %s", filepath, new_filepath)
    if os.path.exists(new_filepath):
        return True, f"Using existing reversed file: {new_filename}", new_filepath

    # Determine format for writing
    format_map = {
        '.wav': 'WAV',
        '.aif': 'AIFF',
        '.aiff': 'AIFF'
    }
    write_format = format_map.get(ext_lower)
    if write_format is None:
        return False, f"Unsupported file extension: {ext_lower}", None

    try:
        # Read audio using SoundFile as 32-bit integer data
        info = sf.info(filepath)
        data, samplerate = sf.read(filepath, dtype="int32")

        # Reverse in time
        reversed_data = data[::-1]

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(new_filepath), exist_ok=True)

        # Write out with correct format and subtype
        try:
            sf.write(
                new_filepath,
                reversed_data,
                samplerate,
                format=write_format,
                subtype=info.subtype,
            )
        except Exception as e:
            logging.warning(
                "Write failed for %s: %s. Trying Reversed folder", new_filepath, e
            )
            # If writing directly fails (e.g. read-only directory), write under
            # a Reversed/ subdirectory and return that path instead.
            alt_dir = os.path.join(directory, "Reversed", os.path.dirname(filename))
            os.makedirs(alt_dir, exist_ok=True)
            alt_filepath = os.path.join(alt_dir, new_filename)
            sf.write(
                alt_filepath,
                reversed_data,
                samplerate,
                format=write_format,
                subtype=info.subtype,
            )
            new_filepath = alt_filepath

        # Refresh library
        refresh_success, refresh_message = refresh_library()
        if refresh_success:
            msg = f"Successfully created reversed file: {new_filename}. Library refreshed."
        else:
            msg = f"Created reversed file: {new_filename}. Library refresh failed: {refresh_message}"

        return True, msg, new_filepath

    except Exception as e:
        logging.error("Reverse failed for %s: %s", filepath, e)
        return False, f"Error reversing file {filename}: {e}", None
