import click
from serial.tools import list_ports

from spycoprobe.spycoprobe import SpycoProbe
from spycoprobe.spycoprobe import INTERFACE_NAMES

from spycoprobe.intelhex import IntelHex16bitReader
from spycoprobe.protocol import REQUEST_MAX_DATA


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
        hits = list()
        for port in list_ports.comports():
            if port.interface in INTERFACE_NAMES:
                hits.append(port.device)
        if len(hits) == 1:
            click.echo(f"Found spycoprobe at {hits[0]}")
            device = hits[0]
        elif len(hits) > 1:
            click.UsageError(f"Found spycoprobes at {' and '.join(hits)}. Try specifying the device with '-d'.")

    if device is None:
        raise click.UsageError("Couldn't find a Spycoprobe USB device. Try specifying the device with '-d'.")

    ctx.obj["device"] = device


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
    ih = IntelHex16bitReader()
    ih.loadhex(image)

    with SpycoProbe(ctx.obj["device"]) as probe:
        probe.start()
        probe.halt()
        for pkt in ih.iter_packets(REQUEST_MAX_DATA):
            probe.write_mem(pkt.address, pkt.values)
            if verify:
                rb = probe.read_mem(pkt.address, len(pkt))
                if (rb != pkt.values).any():
                    print(rb, pkt.values)
                    raise click.ClickException(f"Verification failed at 0x{pkt.address:08X}!")
        probe.release()
        probe.stop()


@cli.command(short_help="Halt target")
@click.pass_context
def halt(ctx):
    with SpycoProbe(ctx.obj["device"]) as probe:
        probe.start()
        probe.halt()
        probe.stop()

@cli.command(short_help="Control target power supply")
@click.option("--on/--off", required=True)
@click.pass_context
def target_power(ctx, on):
    with SpycoProbe(ctx.obj["device"]) as probe:
        probe.target_power(on)