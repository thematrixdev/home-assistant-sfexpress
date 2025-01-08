"""Utility functions for SF Express HK integration."""
import hashlib
import json
import base64

def decode_secret(encoded: str) -> str:
    """Decode base64 encoded secret."""
    return base64.b64decode(encoded).decode('utf-8')

BODY_SECRET = "TndwQDlCMlZPUE1mUFFpNEI5Tn4mUEpGUVlxNkNTT3c="
FIRST_SECRET = "ZXYyV01CfnE0YSZheVNEdkVORDU3SThCK2duVkReQG8="
SECOND_SECRET = "NmhuOFRUZWtPcEVLOTJhJSt1eWdHQWxoaSRiYSRZNjI="

def md5_hex(string: str) -> str:
    return hashlib.md5(string.encode("utf-8")).hexdigest()

def generate_syttoken(
    body_json: str,
    device_id: str,
    client_version: str,
    time_interval: str,
    region_code: str,
    language_code: str,
    js_bundle: str,
) -> str:
    body_secret = decode_secret(BODY_SECRET)
    body_hash = md5_hex(body_json + "&" + body_secret)

    first_secret = decode_secret(FIRST_SECRET)
    raw_str1 = (
        device_id
        + time_interval
        + client_version
        + first_secret
        + region_code
        + language_code
        + body_hash
        + js_bundle
    )

    md5_1 = md5_hex(raw_str1 + "&" + first_secret)

    second_secret = decode_secret(SECOND_SECRET)
    return md5_hex(md5_1 + "&" + second_secret)
