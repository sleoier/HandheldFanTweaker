import asyncio

import decky

from handheld_fan_tweaker.composition import build_service, build_underclock_service
from handheld_fan_tweaker.domain import FanCurvesError

# The fan daemon puts the fastest cluster back to full speed every time it
# applies a profile, so the chosen underclock is checked again this often.
UNDERCLOCK_CHECK_S = 3


class Plugin:
    async def _main(self):
        self.service = build_service(decky.DECKY_PLUGIN_SETTINGS_DIR)
        self.underclock = build_underclock_service(decky.DECKY_PLUGIN_SETTINGS_DIR)
        try:
            outcome = await asyncio.to_thread(self.service.reconcile_on_start)
            decky.logger.info("HandheldFanTweaker: reconcile_on_start → %s", outcome)
        except Exception:
            decky.logger.exception("HandheldFanTweaker: reconcile_on_start failed")
        self._underclock_task = asyncio.get_running_loop().create_task(self._keep_underclock())

    async def _unload(self):
        task = getattr(self, "_underclock_task", None)
        if task:
            task.cancel()
        decky.logger.info("HandheldFanTweaker: unloaded")

    async def get_state(self):
        return await self._call(self.service.state)

    async def get_telemetry(self):
        return await self._call(self.service.telemetry)

    async def set_curve(self, profile: str, points: list):
        return await self._call(self.service.set_curve, profile, points)

    async def reset_curve(self, profile: str):
        return await self._call(self.service.reset_curve, profile)

    async def get_underclock(self):
        return await self._call(self.underclock.state)

    async def set_underclock(self, level: str):
        return await self._call(self.underclock.set_level, level)

    async def _keep_underclock(self):
        while True:
            try:
                changed = await asyncio.to_thread(self.underclock.enforce)
                if changed:
                    decky.logger.info("HandheldFanTweaker: underclock re-applied on %s", ", ".join(changed))
            except Exception:
                decky.logger.exception("HandheldFanTweaker: underclock check failed")
            await asyncio.sleep(UNDERCLOCK_CHECK_S)

    async def _call(self, fn, *args):
        try:
            return {"ok": True, "value": await asyncio.to_thread(fn, *args)}
        except FanCurvesError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            decky.logger.exception("HandheldFanTweaker: unexpected error in %s", getattr(fn, "__name__", fn))
            return {"ok": False, "error": f"unexpected error: {exc}"}
