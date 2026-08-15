const allowedPeriods = new Set(["1D", "5D", "1M", "6M", "1A", "5A"]);

export async function GET(request: Request) {
  const marketApiUrl = process.env.MARKET_API_URL?.replace(/\/$/, "");
  const search = new URL(request.url).searchParams;
  const ticker = search.get("ticker")?.trim().toUpperCase();
  const requestedPeriod = search.get("period")?.trim().toUpperCase() ?? "1M";
  const period = allowedPeriods.has(requestedPeriod) ? requestedPeriod : "1M";

  if (!ticker || !/^[A-Z0-9&.-]{1,16}$/.test(ticker)) {
    return Response.json({ mode: "unavailable", reason: "Invalid ticker", points: [] }, { status: 400 });
  }
  if (!marketApiUrl) {
    return Response.json({ mode: "demo", reason: "MARKET_API_URL is not configured", points: [] });
  }

  try {
    const response = await fetch(
      `${marketApiUrl}/v1/assets/${encodeURIComponent(ticker)}/history?period=${encodeURIComponent(period)}`,
      { cache: "no-store", signal: AbortSignal.timeout(60_000) },
    );
    if (!response.ok) throw new Error(`Market API returned ${response.status}`);
    return Response.json({ mode: "live", ...(await response.json()) });
  } catch (error) {
    return Response.json(
      { mode: "unavailable", reason: error instanceof Error ? error.message : "Unknown API error", points: [] },
      { status: 502 },
    );
  }
}
