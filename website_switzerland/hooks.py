import importlib.util
import pathlib


def _migration(version):
    path = pathlib.Path(__file__).parent / "migrations" / version
    path /= "post-migration.py"
    spec = importlib.util.spec_from_file_location(
        f"website_switzerland_{version}", path
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def post_init_hook(env):
    """The mail texts of the registration stages are shipped with the
    migration that wrote them: a new database gets them too."""
    _migration("18.0.1.0.13")._load_texts(env)
    _migration("18.0.1.0.16")._sign_by_responsible(env)
