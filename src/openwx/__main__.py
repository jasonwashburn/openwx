"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """OpenWx."""


if __name__ == "__main__":
    main(prog_name="openwx")  # pragma: no cover
