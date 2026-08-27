'''
Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import base64
import os

# Placeholders. They keep unsigned requests (openid4vp-v1-unsigned) working out of
# the box; signed requests need real material supplied via the environment below.
_PLACEHOLDER_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
<Your private key / Should get it directly from your
Key Management service>
-----END PRIVATE KEY-----"""

_PLACEHOLDER_CERTIFICATE = """-----BEGIN CERTIFICATE-----
<Your Pulic cert / Can be added here, can come from
your Key management Service.>
-----END CERTIFICATE-----"""


def _pem_from_env(var_name: str, placeholder: str) -> str:
    """Reads a PEM blob from the environment, falling back to the placeholder.

    The signing key must never be baked into the image, so it is injected at
    runtime instead. Multi-line values are awkward in most container UIs, so the
    variable may hold either the PEM itself or its base64 encoding.

    Args:
        var_name: Name of the environment variable to read.
        placeholder: Value to return when the variable is unset or empty.

    Returns:
        The PEM string.

    Raises:
        ValueError: If the variable is set but is neither PEM nor base64-encoded PEM.
    """
    raw = os.environ.get(var_name, "").strip()
    if not raw:
        return placeholder
    if "-----BEGIN" in raw:
        # Allow literal "\n" escapes, which some secret stores produce.
        return raw.replace("\\n", "\n")
    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"{var_name} is neither a PEM block nor valid base64-encoded PEM"
        ) from exc
    if "-----BEGIN" not in decoded:
        raise ValueError(f"{var_name} decoded from base64 but contains no PEM block")
    return decoded


PRIVATE_KEY = _pem_from_env("VERIFIER_PRIVATE_KEY", _PLACEHOLDER_PRIVATE_KEY)
CERTIFICATE = _pem_from_env("VERIFIER_CERTIFICATE", _PLACEHOLDER_CERTIFICATE)

# True once both values have been replaced with real material.
SIGNING_CONFIGURED = (
    PRIVATE_KEY != _PLACEHOLDER_PRIVATE_KEY and CERTIFICATE != _PLACEHOLDER_CERTIFICATE
)
