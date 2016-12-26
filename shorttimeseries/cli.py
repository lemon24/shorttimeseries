import click

from . import parse, InvalidTimestamp


@click.command()
@click.argument('file',
    type=click.File())
@click.option('-i', '--initial')
@click.option('-p', '--precision',
    type=click.Choice(['day', 'hour', 'minute', 'second']), default='minute')
def main(file, initial, precision):
    try:
        for timestamp, label in parse(file, initial, precision):
            click.echo("{:%Y-%m-%dT%H:%M:%S} {}".format(timestamp, label))
    except ValueError as e:
        raise click.BadParameter(str(e))
    except InvalidTimestamp as e:
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()

