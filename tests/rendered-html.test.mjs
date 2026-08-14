import assert from "node:assert/strict";
import test from "node:test";

async function loadWorker(suffix) {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${suffix}`);
  const { default: worker } = await import(workerUrl.href);
  return worker;
}

test("server-renders the Vertice dashboard", async () => {
  const worker = await loadWorker("page");
  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );

  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>V.rtice . Intelig.ncia de Mercado<\/title>/i);
  assert.match(html, /Mercados em perspectiva/);
  assert.match(html, /Atlassian/);
  assert.match(html, /BDRs &amp; spreads/);
  assert.match(html, /Conector Python preparado/);
  assert.doesNotMatch(html, /codex-preview/);
  assert.doesNotMatch(html, /react-loading-skeleton/);
});

test("returns a safe fallback while the market API is not configured", async () => {
  const worker = await loadWorker("api");
  const response = await worker.fetch(new Request("http://localhost/api/market"), {});
  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.mode, "demo");
  assert.deepEqual(payload.assets, []);
});
