from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capture_public_http_source.py"


class CapturePublicHttpSourceTests(unittest.TestCase):
    def _fake_curl(self, *, status: int = 200, final_url: str = "https://example.com/page", body: str = "<html><title>Example</title><main>Visible official text.</main></html>", redirect_location: str | None = None, failed_url: str | None = None) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        directory = Path(tmp.name)
        script = directory / "curl"
        script.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import pathlib
                import sys

                args = sys.argv[1:]
                if '--request' not in args or args[args.index('--request') + 1] != 'GET':
                    raise SystemExit('curl helper did not use GET')
                if '-I' in args or '--head' in args:
                    raise SystemExit('curl helper must not use HEAD')
                output = pathlib.Path(args[args.index('--output') + 1])
                headers = pathlib.Path(args[args.index('--dump-header') + 1])
                counter = pathlib.Path(__file__).with_name('counter')
                first_request = {redirect_location!r} is not None and not counter.exists()
                requested_url = args[args.index('--url') + 1]
                if requested_url == {failed_url!r}:
                    status = 404
                    location = None
                    response_body = ''
                elif first_request:
                    counter.write_text('1', encoding='utf-8')
                    status = 302
                    location = {redirect_location!r}
                    response_body = ''
                else:
                    status = {status!r}
                    location = None
                    response_body = {body!r}
                output.write_text(response_body, encoding='utf-8')
                headers.write_text('HTTP/1.1 %s Fixture\\r\\nContent-Type: text/html\\r\\n%s\\r\\n' % (status, ('Location: %s\\r\\n' % location) if location else ''), encoding='utf-8')
                write_out = args[args.index('--write-out') + 1]
                sys.stdout.write(write_out.replace('%{{http_code}}', str(status)).replace('%{{url_effective}}', args[args.index('--url') + 1]).replace('%{{content_type}}', 'text/html').replace('\\\\t', '\\t'))
                """
            ),
            encoding="utf-8",
        )
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        (directory / "sitecustomize.py").write_text(
            "import socket\n"
            "def public_getaddrinfo(host, port, *args, **kwargs):\n"
            "    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', port))]\n"
            "socket.getaddrinfo = public_getaddrinfo\n",
            encoding="utf-8",
        )
        return tmp, script

    def _run(self, *urls: str, fake: tuple[tempfile.TemporaryDirectory[str], Path]) -> tuple[int, dict]:
        tmp, _ = fake
        env = dict(os.environ)
        env["PATH"] = f"{Path(tmp.name)}{os.pathsep}{env.get('PATH', '')}"
        env["PYTHONPATH"] = f"{Path(tmp.name)}{os.pathsep}{env.get('PYTHONPATH', '')}"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *(item for url in urls for item in ("--url", url)), "--format", "json"],
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return proc.returncode, json.loads(proc.stdout)

    def test_public_html_emits_shell_adapter_source_and_observation(self) -> None:
        fake = self._fake_curl()
        try:
            code, payload = self._run("https://example.com/page", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["does_not_search_web"])
        self.assertNotIn("search.web", json.dumps(payload))
        report = payload["capability_adapter_reports"][0]
        operation = report["host_tools"]["shell_http"]["operations"]["open_source"][0]
        self.assertEqual(operation["request_method"], "GET")
        self.assertEqual(operation["http_status"], 200)
        self.assertEqual(payload["observations"][0]["capability"], "source.open")
        self.assertEqual(payload["observations"][0]["concrete_tool"], "curl")
        self.assertIn("Visible official text.", payload["observations"][0]["raw_excerpt"])

    def test_redirect_requires_public_final_url_and_records_it(self) -> None:
        fake = self._fake_curl(redirect_location="https://www.example.com/final")
        try:
            code, payload = self._run("https://example.com/redirect", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertEqual(code, 0)
        operation = payload["capability_adapter_reports"][0]["host_tools"]["shell_http"]["operations"]["open_source"][0]
        self.assertEqual(operation["final_url"], "https://www.example.com/final")

    def test_non_success_status_fails_without_source_records(self) -> None:
        fake = self._fake_curl(status=404)
        try:
            code, payload = self._run("https://example.com/missing", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertNotEqual(code, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["sources"], [])
        self.assertIn("capture_http_status_not_success", {item["code"] for item in payload["issues"]})

    def test_empty_visible_body_fails(self) -> None:
        fake = self._fake_curl(body="<html><title>Empty</title><script>hidden()</script></html>")
        try:
            code, payload = self._run("https://example.com/empty", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertNotEqual(code, 0)
        self.assertIn("capture_excerpt_missing", {item["code"] for item in payload["issues"]})

    def test_private_or_credential_url_is_rejected_before_curl(self) -> None:
        fake = self._fake_curl()
        try:
            for url in ("http://127.0.0.1/admin", "https://user:pass@example.com/page", "https://example.com/page?token=secret"):
                code, payload = self._run(url, fake=fake)
                self.assertNotEqual(code, 0)
                self.assertIn("capture_url_not_public", {item["code"] for item in payload["issues"]})
        finally:
            fake[0].cleanup()

    def test_multiple_public_urls_receive_stable_distinct_record_ids(self) -> None:
        fake = self._fake_curl()
        try:
            code, payload = self._run("https://example.com/first", "https://example.com/second", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["sources"]), 2)
        self.assertEqual(len(payload["observations"]), 2)
        source_ids = [item["source_id"] for item in payload["sources"]]
        observation_ids = [item["observation_id"] for item in payload["observations"]]
        self.assertEqual(len(set(source_ids)), 2)
        self.assertEqual(len(set(observation_ids)), 2)
        self.assertEqual({item["source_id"] for item in payload["observations"]}, set(source_ids))

    def test_batch_failure_discards_prior_capture_records(self) -> None:
        fake = self._fake_curl(failed_url="https://example.com/second")
        try:
            code, payload = self._run("https://example.com/first", "https://example.com/second", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["observations"], [])
        self.assertEqual(payload["capability_adapter_reports"], [])
        self.assertIn("capture_http_status_not_success", {item["code"] for item in payload["issues"]})

    def test_source_ids_are_stable_across_separate_invocations(self) -> None:
        fake = self._fake_curl()
        try:
            first_code, first = self._run("https://example.com/first", fake=fake)
            second_code, second = self._run("https://example.com/second", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertNotEqual(first["sources"][0]["source_id"], second["sources"][0]["source_id"])
        self.assertNotEqual(first["observations"][0]["observation_id"], second["observations"][0]["observation_id"])

    def test_duplicate_url_batch_is_rejected_without_records(self) -> None:
        fake = self._fake_curl()
        try:
            code, payload = self._run("https://example.com/duplicate", "https://example.com/duplicate", fake=fake)
        finally:
            fake[0].cleanup()
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["sources"], [])
        self.assertEqual(payload["observations"], [])
        self.assertIn("capture_duplicate_url", {item["code"] for item in payload["issues"]})


if __name__ == "__main__":
    unittest.main()
