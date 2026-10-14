from __future__ import annotations

from .application import FanCurveService
from .domain import BackendInfo
from .infrastructure import (
    DryRunDaemon,
    IniCurveFile,
    JsonSnapshotStore,
    SysfsTelemetry,
    SystemdDaemon,
    curves_support,
    detect,
)
from .infrastructure.daemons import under


def build_service(
    settings_dir: str,
    *,
    fs_root: str = "/",
    sys_root: str = "/",
    dry_run: bool = False,
) -> FanCurveService:
    """fs_root is the root for /etc, /usr and /var and sys_root the root for
    /sys, so the CLI and tests can point them at a fake tree."""
    telemetry = SysfsTelemetry(root=sys_root)
    snapshots = JsonSnapshotStore(settings_dir)
    spec = detect(fs_root)
    if spec is None:
        backend = BackendInfo(
            name=None,
            profiles=(),
            editable=False,
            reason="no supported fan daemon found (odin3d or konkrd)",
        )
        return FanCurveService(backend, telemetry, snapshots)

    editable, reason = curves_support(spec, fs_root)
    backend = BackendInfo(name=spec.name, profiles=spec.profiles, editable=editable, reason=reason)
    daemon_cls = DryRunDaemon if dry_run else SystemdDaemon
    daemon = daemon_cls(spec, root=fs_root)
    repository = IniCurveFile(under(fs_root, spec.config), spec.profiles)
    return FanCurveService(backend, telemetry, snapshots, repository=repository, daemon=daemon)
