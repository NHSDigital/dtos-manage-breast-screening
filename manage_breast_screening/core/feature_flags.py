from pathlib import Path

import yaml
from openfeature import api
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider


def setup_feature_flags(flags_yaml_path: Path) -> None:
    """Initialise the OpenFeature InMemoryProvider from a YAML flags file.

    Call from AppConfig.ready(). The YAML file must follow the structure::

        flags:
          my_flag: true    # true to enable, false to disable
    """
    with flags_yaml_path.open() as f:
        data = yaml.safe_load(f)

    raw_flags = data.get("flags", {})
    provider_flags = {
        name: InMemoryFlag(
            default_variant="on" if enabled else "off",
            variants={"on": True, "off": False},
        )
        for name, enabled in raw_flags.items()
    }
    api.set_provider(InMemoryProvider(provider_flags))
