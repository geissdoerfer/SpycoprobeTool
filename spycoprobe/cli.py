import click

from spycoprobe.spycoprobe import SpycoProbe
from spycoprobe.spycoprobe import DeviceNotFoundError

from spycoprobe.protocol import IOSetState


@click.group(context_settings=dict(help_option_names=["-h", "--help"], obj={}))
@click.option(
    "--device",
    "-d",
    type=click.Path(exists=True),
    required=False,
    help="Path to USB device",
)
@click.pass_context
def cli(ctx, device):
    if device is None:
        try:
            ctx.obj["probe"] = SpycoProbe()
        except DeviceNotFoundError:
            raise click.UsageError("Couldn't find a Spycoprobe USB device. Try specifying the device with '-d'.")
    else:
        ctx.obj["probe"] = SpycoProbe(device)
    ctx.obj["probe"].__enter__()


@cli.result_callback()
@click.pass_context
def process_result(ctx, result, **kwargs):
    ctx.obj["probe"].__exit__()


@cli.command(short_help="Flash provided hex image")
@click.option(
    "--image",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Path to MSP430 image in intelhex format",
)
@click.option("--verify", is_flag=True, default=True, help="Verify while writing")
@click.pass_context
def flash(ctx, image, verify):
    ctx.obj["probe"].start()
    ctx.obj["probe"].flash(image, verify)
    ctx.obj["probe"].stop()


@cli.command(short_help="Halt target")
@click.pass_context
def halt(ctx):
    ctx.obj["probe"].start()
    ctx.obj["probe"].halt()
    ctx.obj["probe"].stop()


@cli.command(short_help="Control target power supply")
@click.option("--on/--off", required=True)
@click.pass_context
def target_power(ctx, on):
    ctx.obj["probe"].target_power(on)


@cli.command(short_help="Control GPIO pin")
@click.option("--pin-no", "-p", type=int, required=True, help="Pin number")
@click.option(
    "--state",
    "-s",
    type=click.Choice(["high", "1", "low", "0", "input"], case_sensitive=False),
    required=True,
    help="Pin state",
)
@click.pass_context
def gpio_set(ctx, pin_no, state):
    if state in ["high", "1"]:
        ctx.obj["probe"].gpio_set(pin_no, IOSetState.IOSET_OUT_HIGH)
    elif state in ["low", "0"]:
        ctx.obj["probe"].gpio_set(pin_no, IOSetState.IOSET_OUT_LOW)
    else:
        ctx.obj["probe"].gpio_set(pin_no, IOSetState.IOSET_IN)


@cli.command(short_help="Read GPIO pin")
@click.option("--pin-no", "-p", type=int, required=True, help="Pin number")
@click.pass_context
def gpio_get(ctx, pin_no):
    state = ctx.obj["probe"].gpio_get(pin_no)
    click.echo(state)
