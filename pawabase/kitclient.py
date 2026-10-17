"""The client the ``pawabase`` command and the emulator use: the SDK client plus the calls only function authors need.

Deploying a bundle, reading run logs, running a function or a flow as an operator, and executing ``ctx.runtime`` methods on the deployment are about
*writing functions*, so they live here and not in the ``pawabase`` client SDK. Everything is the management plane of the key's own environment.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

from .client import AsyncPawabase, Pawabase


class _Kit:
    """Endpoints written once against ``_call`` (a value on the blocking client, an awaitable on the async one)."""

    environment: str

    def _manage(self, suffix: str) -> str:
        return f"/platform/v1/envs/{quote(self.environment)}{suffix}"

    # ── functions: deploying and running them ───────────────────────────

    def deployed_functions(self, *, branch: str | None = None) -> Any:
        """Functions visible to the environment (and *branch*), each saying whether it came from a branch, a deployment or the runtime's mounted code."""
        return self._call("GET", self._manage("/functions"), params={"branch": branch} if branch else None, retry=True)

    def deploy_functions(
        self, archive: str, *, branch: str = "main", manifest: Mapping[str, Any] | None = None, runtime: str = "python3.11", limits: Mapping[str, Any] | None = None
    ) -> Any:
        """Upload a base64 ``.tar.gz`` bundle and activate it. Not retried: a half-seen deploy must be looked at, not repeated."""
        return self._call("POST", self._manage("/function-deployments"), json={"archive": archive, "branch": branch, "manifest": dict(manifest or {}), "runtime": runtime, "limits": dict(limits or {})})

    def deployments(self, *, branch: str | None = None, limit: int = 50) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if branch:
            params["branch"] = branch
        return self._call("GET", self._manage("/function-deployments"), params=params, retry=True)

    def deployment(self, deployment_id: str) -> Any:
        return self._call("GET", self._manage(f"/function-deployments/{quote(deployment_id)}"), retry=True)

    def activate_deployment(self, deployment_id: str) -> Any:
        """Make an earlier deployment the active one again (a rollback)."""
        return self._call("POST", self._manage(f"/function-deployments/{quote(deployment_id)}/activate"))

    def remove_deployment(self, deployment_id: str) -> Any:
        return self._call("DELETE", self._manage(f"/function-deployments/{quote(deployment_id)}"))

    def function_branches(self) -> Any:
        return self._call("GET", self._manage("/function-branches"), retry=True)

    def remove_function_branch(self, branch: str) -> Any:
        """Delete the functions deployed on *branch*. The environment's own are untouched."""
        return self._call("DELETE", self._manage(f"/function-branches/{quote(branch)}"))

    def function_runs(self, function: str | None = None, *, branch: str | None = None, status: str | None = None, after: str | None = None, limit: int = 50) -> Any:
        params = {k: v for k, v in {"function": function, "branch": branch, "status": status, "after": after, "limit": limit}.items() if v not in (None, "")}
        return self._call("GET", self._manage("/function-runs"), params=params, retry=True)

    function_logs = function_runs

    def function_run(self, run_id: str) -> Any:
        return self._call("GET", self._manage(f"/function-runs/{quote(run_id)}"), retry=True)

    def run_function(self, name: str, input: Any = None, *, branch: str | None = None, as_user: Mapping[str, Any] | None = None) -> Any:
        """Run a deployed function now as an operator (or ``as_user``), bypassing its HTTP policy. Returns ``{"status", "result" | "error"}``."""
        return self._call("POST", self._manage(f"/functions/{quote(name)}/invoke"), json={"input": input, "branch": branch, "as_user": dict(as_user) if as_user else None})

    # ── triggers: events, flows, schedules ──────────────────────────────

    def emit_event(self, name: str, payload: Any = None) -> Any:
        """Publish an event on the environment: every subscription and flow listening for it runs."""
        return self._call("POST", self._manage("/events"), json={"name": name, "payload": payload})

    def events(self, name: str | None = None, *, limit: int = 20) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if name:
            params["name"] = name
        return self._call("GET", self._manage("/events"), params=params, retry=True)

    def run_flow(self, name: str, input: Any = None, *, as_user: Mapping[str, Any] | None = None, entry: str | None = None) -> Any:
        return self._call("POST", self._manage(f"/flows/{quote(name)}/run"), json={"input": input, "as_user": dict(as_user) if as_user else None, "entry": entry})

    def run_schedule(self, name: str) -> Any:
        """Fire a schedule now, exactly as the scheduler would."""
        return self._call("POST", self._manage(f"/schedules/{quote(name)}/run"))

    def definitions(self, kind: str, *, branch: str | None = None) -> Any:
        """The environment's ``routes``, ``flows``, ``schedules``, ``subscriptions``, ``inbound-hooks`` … (a branch's draft, when *branch* is given)."""
        return self._call("GET", self._manage(f"/{kind}"), params={"branch": branch} if branch and branch != "main" else None, retry=True)

    def branches(self) -> Any:
        return self._call("GET", self._manage("/branches"), retry=True)

    # ── the runtime, remotely ───────────────────────────────────────────

    def runtime_call(self, method: str, args: list[Any] | None = None, kwargs: Mapping[str, Any] | None = None, *, as_user: Mapping[str, Any] | None = None, branch: str | None = None) -> Any:
        """One ``ctx.runtime`` method, executed on the deployment (needs the ``runtime:use`` scope). Values are in :mod:`pawabase.codec` form."""
        return self._call("POST", self._manage("/runtime/call"), json={"method": method, "args": args or [], "kwargs": dict(kwargs or {}), "as_user": dict(as_user) if as_user else None, "branch": branch})

    def identify(self, token: str | None) -> Any:
        """The ``auth`` context a user's access token stands for (anonymous when it is missing, forged or expired). Verified on the deployment."""
        return self._call("POST", self._manage("/runtime/identify"), json={"token": token})

    def runtime_db(self, op: str, **fields: Any) -> Any:
        return self._call("POST", self._manage("/runtime/db"), json={"op": op, **fields})


class KitClient(_Kit, Pawabase):
    """Blocking client with the function-author calls."""


class AsyncKitClient(_Kit, AsyncPawabase):
    """Async client with the function-author calls."""
