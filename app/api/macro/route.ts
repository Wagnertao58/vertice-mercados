export async function GET() {
  const marketApiUrl = process.env.MARKET_API_URL?.replace(/\/$/, "");
  if (!marketApiUrl) {
    return Response.json({ mode: "demo", reason: "MARKET_API_URL is not configured", series: [], correlation: { labels: [], cells: [] } });
  }
  try {
    const response = await fetch(`${marketApiUrl}/v1/macro/dashboard?months=24`, {
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    if (!response.ok) throw new Error(`Market API returned ${response.status}`);
    return Response.json({ mode: "live", ...(await response.json()) });
  } catch (error) {
    return Response.json(
      { mode: "unavailable", reason: error instanceof Error ? error.message : "Unknown API error", series: [], correlation: { labels: [], cells: [] } },
      { status: 502 },
    );
  }
}
