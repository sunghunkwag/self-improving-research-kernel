from pathlib import Path

from shared.local_corpus import load_inventory


def test_load_inventory_normalizes_rows_and_preserves_order(tmp_path):
    first = tmp_path / "first.py"
    second = tmp_path / "second.PY"
    home_file = Path("~/omega_inventory_home.py").expanduser()
    inventory = tmp_path / "inventory.txt"
    inventory.write_text(
        "\n".join(
            [
                "",
                "# comment rows are ignored",
                f" {first} ",
                f'"{second}"',
                str(first),
                str(tmp_path / "notes.txt"),
                f"'{home_file}'",
                "relative_module.py",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert load_inventory(inventory) == [
        first,
        second,
        home_file,
        Path("relative_module.py"),
    ]
