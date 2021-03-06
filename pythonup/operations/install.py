import functools

import click
import packaging.version

from .. import installations, versions

from .common import check_installation, version_command
from .link import link_commands, unlink_commands, use_versions


def has_any_installations():
    for version in versions.iter_versions():
        try:
            version.find_installation()
        except installations.InstallationNotFoundError:
            continue
        else:
            return True
    return False


@version_command()
def install(version, use):
    check_installation(
        version, expect=False,
        on_exit=functools.partial(link_commands, version),
    )

    if not use and not has_any_installations():
        use = True
        click.echo('Will use {} after installation'.format(version))

    version.install()
    link_commands(version)
    if use:
        use_versions([version])


@version_command()
def uninstall(version):
    check_installation(
        version, expect=True,
        on_exit=functools.partial(unlink_commands, version),
    )
    click.echo(f'Uninstalling {version}...')
    unlink_commands(version)
    removed_path = version.uninstall()
    click.echo(f'Removed {version} from {removed_path}')


@version_command()
def upgrade(version):
    installation = check_installation(
        version, expect=True,
        on_exit=functools.partial(link_commands, version),
    )
    try:
        curr_build = packaging.version.Version(installation.get_build_name())
    except installation.InvalidBuildError:
        click.echo(f'Unrecognized build at {installation.root}', err=True)
        click.get_current_context().exit(1)
    best_build = packaging.version.Version(version.find_best_build_name())
    if curr_build == best_build:
        click.echo(f'{version} is up to date ({curr_build})')
    elif curr_build > best_build:
        click.echo(f'{version} is up to date ({curr_build} > {best_build})')
    else:
        click.echo(f'Upgrading {version} from {curr_build} to {best_build}...')
        version.install(build_name=str(best_build))
    link_commands(version)
