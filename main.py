import asyncio

import decky

from handheld_fan_tweaker.composition import build_service
from handheld_fan_tweaker.domain import FanCurvesError


class Plugin:
    async def _main(self):
        self.service = build_service(decky.DECKY_PLUGIN_SETTINGS_DIR)
        try:
            outcome = await asyncio.to_thread(self.service.reconcile_on_start)
            decky.logger.info("HandheldFanTweaker: reconcile_on_start → %s", outcome)
        except Exception:
            decky.logger.exception("HandheldFanTweaker: reconcile_on_start failed")

    async def _unload(self):
        decky.logger.info("HandheldFanTweaker: unloaded")

    async def get_state(self):
        return await self._call(self.service.state)

    async def get_telemetry(self):
        return await self._call(self.service.telemetry)

    async def set_curve(self, profile: str, points: list):
        return await self._call(self.service.set_curve, profile, points)

    async def reset_curve(self, profile: str):
        return await self._call(self.service.reset_curve, profile)

    async def _call(self, fn, *args):
        try:
            return {"ok": True, "value": await asyncio.to_thread(fn, *args)}
        except FanCurvesError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            decky.logger.exception("HandheldFanTweaker: unexpected error in %s", getattr(fn, "__name__", fn))
            return {"ok": False, "error": f"unexpected error: {exc}"}
