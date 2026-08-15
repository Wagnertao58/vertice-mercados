"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Asset = {
  ticker: string; name: string; market: string; currency: string; price: number;
  change: number; month: number; year: number; volatility: number; beta: number;
  drawdown: number; volume: string; color: string; bars: number[];
};

const demoAssets: Asset[] = [
  { ticker: "TEAM", name: "Atlassian", market: "NASDAQ", currency: "US$", price: 165.98, change: 2.84, month: 80.9, year: 14.2, volatility: 48.7, beta: 1.12, drawdown: -31.4, volume: "4,8 mi", color: "#6757d9", bars: [35,39,37,42,46,43,49,53,58,55,62,67,71,76,73,82,86,91,88,96] },
  { ticker: "RNG", name: "RingCentral", market: "NYSE", currency: "US$", price: 67.78, change: 1.96, month: 66.9, year: 38.5, volatility: 42.1, beta: 1.08, drawdown: -18.7, volume: "2,1 mi", color: "#2b91d0", bars: [30,33,31,38,36,42,44,41,48,51,49,57,61,59,68,72,70,77,82,88] },
  { ticker: "T1AM34", name: "Atlassian BDR", market: "B3", currency: "R$", price: 44.81, change: 2.67, month: 78.4, year: 17.9, volatility: 51.2, beta: 1.15, drawdown: -32.8, volume: "294", color: "#6757d9", bars: [34,37,36,41,44,43,47,51,56,54,60,65,69,74,72,79,84,88,86,94] },
  { ticker: "R2NG34", name: "RingCentral BDR", market: "B3", currency: "R$", price: 14.64, change: 1.72, month: 64.1, year: 42.3, volatility: 45.6, beta: 1.11, drawdown: -20.1, volume: "1,2 mil", color: "#2b91d0", bars: [29,31,30,35,34,39,43,40,46,49,47,54,58,57,64,68,67,73,78,84] },
  { ticker: "NVDA", name: "NVIDIA", market: "NASDAQ", currency: "US$", price: 225.30, change: 0.54, month: 10.7, year: 61.8, volatility: 39.4, beta: 1.72, drawdown: -16.2, volume: "182 mi", color: "#78b942", bars: [46,49,47,52,55,51,58,60,57,64,68,66,72,76,73,79,83,80,86,90] },
  { ticker: "PETR4", name: "Petrobras PN", market: "B3", currency: "R$", price: 41.92, change: -0.38, month: 4.6, year: 21.3, volatility: 27.8, beta: 1.09, drawdown: -12.6, volume: "32 mi", color: "#f0a93b", bars: [53,51,54,50,55,58,56,60,57,62,64,61,65,68,66,70,69,73,71,75] },
  { ticker: "AAPL", name: "Apple", market: "NASDAQ", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#555d66", bars: [50,52,49,55,54,57,59,56,61,64,62,66,68,67,71,74,72,77,80,82] },
  { ticker: "MSFT", name: "Microsoft", market: "NASDAQ", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#3478c0", bars: [44,47,46,50,52,51,55,57,56,60,63,61,65,68,67,71,73,76,78,81] },
  { ticker: "AMZN", name: "Amazon", market: "NASDAQ", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#d9892b", bars: [41,44,43,48,46,51,54,52,57,59,58,62,65,63,68,70,73,71,77,80] },
  { ticker: "GOOGL", name: "Alphabet", market: "NASDAQ", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#4285f4", bars: [48,46,50,52,51,55,58,56,60,63,61,66,64,69,72,70,75,77,79,83] },
  { ticker: "META", name: "Meta Platforms", market: "NASDAQ", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#3468b2", bars: [45,48,47,51,54,52,57,55,60,62,65,63,68,71,69,74,76,79,82,84] },
  { ticker: "VALE3", name: "Vale ON", market: "B3", currency: "R$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#0d8068", bars: [58,56,59,57,61,63,60,64,66,65,68,70,69,72,74,73,76,78,77,81] },
  { ticker: "ITUB4", name: "Itaú Unibanco PN", market: "B3", currency: "R$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#e57d27", bars: [47,49,48,52,51,54,56,55,59,61,60,64,66,65,69,71,70,74,76,79] },
  { ticker: "IBOV", name: "Ibovespa", market: "B3", currency: "", price: 138742, change: 0.42, month: 3.1, year: 12.4, volatility: 18.2, beta: 1, drawdown: -11.8, volume: "—", color: "#0d8068", bars: [47,49,48,51,53,52,56,55,59,61,60,64,66,65,69,71,70,74,76,79] },
  { ticker: "SP500", name: "S&P 500", market: "NYSE", currency: "", price: 7799, change: 0.65, month: 2.8, year: 17.6, volatility: 15.1, beta: 1, drawdown: -9.7, volume: "—", color: "#315ca8", bars: [48,50,49,53,52,56,58,57,61,63,62,66,68,67,71,73,72,76,79,82] },
  { ticker: "NASDAQ", name: "Nasdaq Composite", market: "NASDAQ", currency: "", price: 26803, change: 0.81, month: 4.2, year: 21.8, volatility: 19.3, beta: 1, drawdown: -12.2, volume: "—", color: "#6757d9", bars: [46,49,48,52,55,53,58,60,59,63,66,64,69,71,70,75,77,80,83,86] },
  { ticker: "VIX", name: "CBOE Volatility Index", market: "CBOE", currency: "", price: 14.62, change: -0.07, month: -8.4, year: -11.2, volatility: 86.3, beta: 0, drawdown: -74.1, volume: "—", color: "#c84d4d", bars: [75,71,74,68,70,64,67,61,63,58,60,54,56,51,53,48,50,45,47,42] },
  { ticker: "USD-BRL", name: "Dólar / Real", market: "FX", currency: "R$", price: 5.40, change: -0.24, month: -1.1, year: 3.7, volatility: 12.8, beta: 0, drawdown: -8.2, volume: "—", color: "#b48c2b", bars: [60,62,61,64,63,66,65,68,67,70,69,72,71,74,73,76,75,78,77,80] },
  { ticker: "EUR-BRL", name: "Euro / Real", market: "FX", currency: "R$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#2d8f73", bars: [51,53,52,55,54,57,56,59,58,61,60,63,62,65,64,67,66,69,68,71] },
  { ticker: "EUR-USD", name: "Euro / Dólar", market: "FX", currency: "US$", price: 0, change: 0, month: 0, year: 0, volatility: 0, beta: 0, drawdown: 0, volume: "—", color: "#3468b2", bars: [49,51,50,53,52,55,54,57,56,59,58,61,60,63,62,65,64,67,66,69] },
];

const periods = ["1D", "5D", "1M", "6M", "1A", "5A"];

type MarketFilter = "all" | "brazil" | "usa" | "fx";
type ClassFilter = "all" | "stock" | "bdr" | "index" | "currency";
type RankedAsset = Asset & { score: number; assetClass: ClassFilter };

const bdrTickers = new Set(["T1AM34", "R2NG34"]);
const indexTickers = new Set(["IBOV", "SP500", "NASDAQ", "VIX"]);

function classifyAsset(item: Asset): Exclude<ClassFilter, "all"> {
  if (bdrTickers.has(item.ticker)) return "bdr";
  if (indexTickers.has(item.ticker)) return "index";
  if (item.market === "FX") return "currency";
  return "stock";
}

function classifyMarket(item: Asset): Exclude<MarketFilter, "all"> {
  if (item.market === "B3") return "brazil";
  if (item.market === "FX") return "fx";
  return "usa";
}

function normalized(value: number, values: number[], inverse = false) {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const result = maximum === minimum ? 1 : (value - minimum) / (maximum - minimum);
  return inverse ? 1 - result : result;
}

function rankAssets(items: Asset[]): RankedAsset[] {
  const eligible = items.filter((item) => item.price > 0 && Number.isFinite(item.month) && Number.isFinite(item.volatility));
  if (!eligible.length) return [];
  const monthlyReturns = eligible.map((item) => item.month);
  const yearlyReturns = eligible.map((item) => item.year);
  const volatilities = eligible.map((item) => item.volatility);
  const drawdowns = eligible.map((item) => Math.abs(item.drawdown));
  return eligible.map((item) => {
    const score = 100 * (
      normalized(item.month, monthlyReturns) * .40 +
      normalized(item.volatility, volatilities, true) * .30 +
      normalized(Math.abs(item.drawdown), drawdowns, true) * .20 +
      normalized(item.year, yearlyReturns) * .10
    );
    return { ...item, score: Math.round(score), assetClass: classifyAsset(item) };
  }).sort((left, right) => right.score - left.score);
}

const marketLabels: Record<MarketFilter, string> = { all: "Todos os mercados", brazil: "Brasil", usa: "Estados Unidos", fx: "Câmbio" };
const classLabels: Record<ClassFilter, string> = { all: "Todas as classes", stock: "Ações", bdr: "BDRs", index: "Índices", currency: "Moedas" };

type ApiAsset = {
  ticker: string; price: number; day_change_pct: number; return_1m_pct: number;
  return_1y_pct: number; annualized_volatility_pct: number | null;
  max_drawdown_pct: number | null; beta: number | null; volume: number | null;
  bars: number[]; currency: "USD" | "BRL";
};

type HistoryPoint = {
  date: string;
  close: number;
  adjusted_close: number;
  return_pct: number;
  volume: number | null;
};

type HistoryMode = "loading" | "live" | "fallback";

type DataHealthItem = {
  ticker: string;
  status: "current" | "stale" | "error" | "missing";
  last_price_date: string | null;
  last_error: string | null;
};

type DataHealth = {
  mode?: string;
  status: "healthy" | "attention" | "empty";
  checked_at: string;
  total_assets: number;
  current_assets: number;
  stale_assets: number;
  error_assets: number;
  missing_assets: number;
  coverage_pct: number;
  total_price_rows: number;
  last_update_at: string | null;
  items: DataHealthItem[];
};

type MacroSeries = {
  code: string;
  name: string;
  country: "BR" | "US";
  category: "interest" | "inflation" | "currency";
  unit: string;
  frequency: "daily" | "monthly";
  latest_value: number | null;
  previous_value: number | null;
  change: number | null;
  as_of: string | null;
  points: { date: string; value: number }[];
};

type CorrelationCell = { row: string; column: string; value: number | null; observations: number };

type MacroDashboard = {
  mode?: string;
  status?: string;
  as_of?: string;
  series: MacroSeries[];
  correlation: {
    labels: string[];
    names?: Record<string, string>;
    cells: CorrelationCell[];
    method?: string;
    period_months?: number;
  };
};

const demoMacroSeries: MacroSeries[] = [
  { code: "BR_SELIC", name: "Selic efetiva", country: "BR", category: "interest", unit: "% a.a.", frequency: "daily", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "BR_CDI", name: "CDI", country: "BR", category: "interest", unit: "% a.a.", frequency: "daily", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "BR_IPCA", name: "IPCA em 12 meses", country: "BR", category: "inflation", unit: "% a.a.", frequency: "monthly", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "BR_IGPM", name: "IGP-M em 12 meses", country: "BR", category: "inflation", unit: "% a.a.", frequency: "monthly", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "US_FEDFUNDS", name: "Fed Funds efetiva", country: "US", category: "interest", unit: "% a.a.", frequency: "monthly", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "US_CPI", name: "CPI em 12 meses", country: "US", category: "inflation", unit: "% a.a.", frequency: "monthly", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "US_T10Y", name: "Treasury 10 anos", country: "US", category: "interest", unit: "% a.a.", frequency: "daily", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
  { code: "US_DOLLAR", name: "Dólar amplo", country: "US", category: "currency", unit: "índice", frequency: "daily", latest_value: null, previous_value: null, change: null, as_of: null, points: [] },
];

function formatMacroValue(item: MacroSeries) {
  if (item.latest_value === null) return "—";
  return item.unit.startsWith("%") ? `${item.latest_value.toFixed(2)}%` : item.latest_value.toFixed(2);
}

function correlationBackground(value: number | null) {
  if (value === null) return "#f2f4f3";
  const alpha = .10 + Math.abs(value) * .55;
  return value >= 0 ? `rgba(13, 128, 104, ${alpha})` : `rgba(200, 77, 77, ${alpha})`;
}

function formatHistoryDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", year: "2-digit" })
    .format(new Date(`${value}T12:00:00Z`))
    .replace(". de ", " ")
    .toUpperCase();
}

export default function Home() {
  const [selected, setSelected] = useState("TEAM");
  const [period, setPeriod] = useState("1M");
  const [query, setQuery] = useState("");
  const [usd, setUsd] = useState(5.40);
  const [assets, setAssets] = useState(demoAssets);
  const [dataMode, setDataMode] = useState<"loading" | "live" | "demo" | "unavailable">("loading");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [rankingMarket, setRankingMarket] = useState<MarketFilter>("all");
  const [rankingClass, setRankingClass] = useState<ClassFilter>("stock");
  const [historyPoints, setHistoryPoints] = useState<HistoryPoint[]>([]);
  const [historyMode, setHistoryMode] = useState<HistoryMode>("loading");
  const [dataHealth, setDataHealth] = useState<DataHealth | null>(null);
  const [macroData, setMacroData] = useState<MacroDashboard | null>(null);
  const [macroMode, setMacroMode] = useState<"loading" | "live" | "unavailable">("loading");
  const loadingRef = useRef(false);
  const watch = assets.slice(0, 5);
  const asset = assets.find((item) => item.ticker === selected) ?? assets[0];
  const filtered = useMemo(() => assets.filter((item) => `${item.ticker} ${item.name} ${item.market}`.toLowerCase().includes(query.toLowerCase())), [assets, query]);
  const theoretical = asset.ticker === "TEAM" ? asset.price * usd / 20 : asset.ticker === "RNG" ? asset.price * usd / 25 : null;
  const strip = ["IBOV", "SP500", "NASDAQ", "USD-BRL", "VIX"].map((ticker) => assets.find((item) => item.ticker === ticker)).filter((item): item is Asset => Boolean(item));
  const updatedAt = lastUpdated ? Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(lastUpdated) : null;
  const ranking = useMemo(() => rankAssets(assets.filter((item) =>
    (rankingMarket === "all" || classifyMarket(item) === rankingMarket) &&
    (rankingClass === "all" || classifyAsset(item) === rankingClass)
  )).slice(0, 8), [assets, rankingClass, rankingMarket]);
  const chartBars = useMemo(() => {
    if (historyMode !== "live" || historyPoints.length < 2) {
      return asset.bars.map((height, index) => ({ height, label: `Ponto ${index + 1}` }));
    }
    const closes = historyPoints.map((point) => point.adjusted_close);
    const low = Math.min(...closes);
    const high = Math.max(...closes);
    return historyPoints.map((point) => ({
      height: high === low ? 55 : Math.round(18 + (point.adjusted_close - low) / (high - low) * 78),
      label: `${formatHistoryDate(point.date)} · ${asset.currency} ${point.close.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}`,
    }));
  }, [asset.bars, asset.currency, historyMode, historyPoints]);
  const chartLabels = historyMode === "live" && historyPoints.length > 1
    ? [historyPoints[0], historyPoints[Math.floor(historyPoints.length / 2)], historyPoints.at(-1)!].map((point) => formatHistoryDate(point.date))
    : ["INÍCIO", period, "ATUAL"];
  const macroSeries = macroData?.series?.length ? macroData.series : demoMacroSeries;
  const correlationLookup = useMemo(() => new Map(
    (macroData?.correlation.cells ?? []).map((cell) => [`${cell.row}:${cell.column}`, cell]),
  ), [macroData]);

  const loadMarketData = useCallback(async (initial = false) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    if (initial) setDataMode("loading");
    else setIsRefreshing(true);
    try {
      const response = await fetch("/api/market", { cache: "no-store" });
      const payload = await response.json() as { mode?: string; as_of?: string; assets?: ApiAsset[] };
      if (!response.ok) throw new Error("Market API unavailable");
      if (payload.mode === "live" && payload.assets?.length) {
        setAssets((current) => current.map((item) => {
          const live = payload.assets?.find((candidate) => candidate.ticker === item.ticker);
          if (!live) return item;
          return { ...item, currency: item.currency === "" ? "" : live.currency === "USD" ? "US$" : "R$", price: live.price,
            change: live.day_change_pct, month: live.return_1m_pct, year: live.return_1y_pct,
            volatility: live.annualized_volatility_pct ?? item.volatility, beta: live.beta ?? item.beta,
            drawdown: live.max_drawdown_pct ?? item.drawdown,
            volume: live.volume ? Intl.NumberFormat("pt-BR", { notation: "compact" }).format(live.volume) : item.volume,
            bars: live.bars?.length ? live.bars : item.bars };
        }));
        const liveUsd = payload.assets.find((item) => item.ticker === "USD-BRL");
        if (liveUsd?.price) setUsd(liveUsd.price);
        setLastUpdated(payload.as_of ? new Date(payload.as_of) : new Date());
        setDataMode("live");
      } else setDataMode(payload.mode === "unavailable" ? "unavailable" : "demo");
    } catch {
      setDataMode((current) => current === "live" ? "live" : "unavailable");
    } finally {
      loadingRef.current = false;
      setIsRefreshing(false);
    }
  }, []);

  const loadDataHealth = useCallback(async () => {
    try {
      const response = await fetch("/api/data-health", { cache: "no-store" });
      const payload = await response.json() as DataHealth;
      if (!response.ok || payload.mode !== "live") throw new Error("Data health unavailable");
      setDataHealth(payload);
    } catch {
      setDataHealth(null);
    }
  }, []);

  const loadMacroData = useCallback(async () => {
    try {
      const response = await fetch("/api/macro", { cache: "no-store" });
      const payload = await response.json() as MacroDashboard;
      if (!response.ok || payload.mode !== "live" || !payload.series?.length) throw new Error("Macro data unavailable");
      setMacroData(payload);
      setMacroMode("live");
    } catch {
      setMacroData(null);
      setMacroMode("unavailable");
    }
  }, []);

  useEffect(() => {
    void loadMarketData(true);
    const timer = window.setInterval(() => void loadMarketData(), 5 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [loadMarketData]);

  useEffect(() => {
    void loadDataHealth();
    const timer = window.setInterval(() => void loadDataHealth(), 5 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [loadDataHealth]);

  useEffect(() => {
    void loadMacroData();
    const timer = window.setInterval(() => void loadMacroData(), 30 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [loadMacroData]);

  useEffect(() => {
    const controller = new AbortController();
    setHistoryMode("loading");
    void fetch(`/api/history?ticker=${encodeURIComponent(selected)}&period=${encodeURIComponent(period)}`, {
      cache: "no-store",
      signal: controller.signal,
    }).then(async (response) => {
      const payload = await response.json() as { mode?: string; points?: HistoryPoint[] };
      if (!response.ok || payload.mode !== "live" || !payload.points?.length) throw new Error("History unavailable");
      setHistoryPoints(payload.points);
      setHistoryMode("live");
    }).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setHistoryPoints([]);
      setHistoryMode("fallback");
    });
    return () => controller.abort();
  }, [period, selected]);

  return (
    <main>
      <aside className="sidebar">
        <div className="brand"><span className="brandmark">V</span><div><strong>Vértice</strong><small>market intelligence</small></div></div>
        <nav>
          <button className="nav active"><span>◫</span> Visão geral</button>
          <button className="nav"><span>⌁</span> Análise de ativo</button>
          <button className="nav"><span>⇄</span> Comparador</button>
          <button className="nav"><span>◇</span> BDRs & spreads</button>
          <button className="nav phase-two-nav" onClick={() => document.getElementById("macroeconomia")?.scrollIntoView({ behavior: "smooth" })}><span>◎</span> Macroeconomia</button>
          <button className="nav" onClick={() => document.getElementById("correlacoes")?.scrollIntoView({ behavior: "smooth" })}><span>⌗</span> Correlações</button>
        </nav>
        <div className="phase"><small>FASE 2</small><strong>Macro & correlações</strong><div><i style={{width: "55%"}} /></div><span>Fontes oficiais em integração</span></div>
        <div className="source-note"><span className={`dot ${dataMode === "live" ? "online" : ""}`} /> {dataMode === "live" ? isRefreshing ? "Atualizando dados" : "Dados conectados" : dataMode === "loading" ? "Conectando dados" : "Dados demonstrativos"}<br/><small>{dataMode === "live" ? `API ativa${updatedAt ? ` · consulta ${updatedAt}` : ""}` : "Conector Python preparado"}</small></div>
      </aside>

      <section className="workspace">
        <header>
          <div><p className="eyebrow">VISÃO GERAL</p><h1>Mercados em perspectiva</h1><p className="subtitle">Acompanhe ativos, risco e exposição cambial em um só lugar.</p><p className="auto-note">Painel a cada 5 min · histórico diário às 19h30</p></div>
          <div className="header-actions"><button className="refresh" onClick={() => void loadMarketData()} disabled={isRefreshing}>{isRefreshing ? "Atualizando…" : "Atualizar dados"}</button><button className="date">14 AGO 2026 <span>⌄</span></button><button className="avatar">WG</button></div>
        </header>

        <div className="ticker-strip">
          {strip.map((item) => <div key={item.ticker}><small>{item.ticker === "SP500" ? "S&P 500" : item.ticker === "USD-BRL" ? "USD/BRL" : item.ticker}</small><strong>{item.currency}{item.currency ? " " : ""}{item.price.toLocaleString("pt-BR", { minimumFractionDigits: item.ticker === "USD-BRL" ? 4 : item.price >= 1000 ? 0 : 2, maximumFractionDigits: item.ticker === "USD-BRL" ? 4 : item.price >= 1000 ? 0 : 2 })}</strong><em className={item.change >= 0 ? "up" : "down"}>{item.change >= 0 ? "+" : ""}{item.change.toFixed(2)}%</em></div>)}
        </div>

        <section id="macroeconomia" className="card macro-card">
          <div className="macro-head">
            <div><p className="eyebrow">FASE 2 · MACROECONOMIA</p><h3>Pulso monetário e inflação</h3><p>Brasil e Estados Unidos normalizados em uma mesma leitura temporal.</p></div>
            <span className={`macro-badge ${macroMode === "live" ? "live" : ""}`}><i />{macroMode === "live" ? "Fontes oficiais conectadas" : macroMode === "loading" ? "Conectando indicadores" : "Aguardando primeira coleta"}</span>
          </div>
          <div className="macro-grid">
            {macroSeries.map((item) => {
              const heights = item.points.slice(-12).map((point) => point.value);
              const low = heights.length ? Math.min(...heights) : 0;
              const high = heights.length ? Math.max(...heights) : 1;
              return <article key={item.code} className="macro-indicator">
                <div className="macro-indicator-head"><span>{item.country === "BR" ? "BRASIL" : "EUA"}</span><em>{item.frequency === "daily" ? "DIÁRIO" : "MENSAL"}</em></div>
                <h4>{item.name}</h4>
                <div className="macro-value"><strong>{formatMacroValue(item)}</strong><small className={(item.change ?? 0) >= 0 ? "up" : "down"}>{item.change === null ? "sem leitura" : `${item.change >= 0 ? "+" : ""}${item.change.toFixed(2)} p.p.`}</small></div>
                <div className="macro-spark" aria-label={`Evolução de ${item.name}`}>
                  {(heights.length ? heights : Array.from({length: 12}, (_, index) => index + 1)).map((value, index) => <i key={`${item.code}-${index}`} style={{height: `${heights.length ? 18 + (value - low) / Math.max(high - low, .0001) * 76 : 24 + index * 3}%`}} />)}
                </div>
                <small className="macro-date">{item.as_of ? `Referência ${item.as_of}` : "Coleta oficial pendente"}</small>
              </article>;
            })}
          </div>

          <div id="correlacoes" className="correlation-panel">
            <div className="correlation-head"><div><p className="eyebrow">MATRIZ DE CORRELAÇÃO</p><h3>Ativos versus cenário macro</h3></div><span>{macroData?.correlation.period_months ?? 24} meses · frequência mensal</span></div>
            {macroData?.correlation.labels.length ? <div className="correlation-scroll"><table>
              <thead><tr><th>Variável</th>{macroData.correlation.labels.map((label) => <th key={label}>{label.replace("BR_", "").replace("US_", "")}</th>)}</tr></thead>
              <tbody>{macroData.correlation.labels.map((row) => <tr key={row}><th title={macroData.correlation.names?.[row]}>{row.replace("BR_", "").replace("US_", "")}</th>{macroData.correlation.labels.map((column) => {
                const cell = correlationLookup.get(`${row}:${column}`);
                return <td key={column} style={{background: correlationBackground(cell?.value ?? null)}} title={`${macroData.correlation.names?.[row] ?? row} × ${macroData.correlation.names?.[column] ?? column} · ${cell?.observations ?? 0} observações`}>{cell?.value === null || cell?.value === undefined ? "—" : cell.value.toFixed(2)}</td>;
              })}</tr>)}</tbody>
            </table></div> : <div className="correlation-placeholder"><strong>Matriz preparada</strong><span>Será preenchida após a primeira sincronização conjunta de mercado e indicadores macroeconômicos.</span></div>}
            <div className="correlation-legend"><span><i className="negative" /> relação inversa</span><span><i /> neutra</span><span><i className="positive" /> relação positiva</span><em>{macroData?.correlation.method ?? "Retornos dos ativos e variações dos indicadores serão alinhados por mês."}</em></div>
          </div>
          <p className="macro-source"><strong>Fontes:</strong> Banco Central do Brasil (SGS), Federal Reserve Bank of New York, BLS, U.S. Treasury e Federal Reserve Board. Séries sujeitas a revisão; correlação não implica causalidade.</p>
        </section>

        <section className="card ranking-card">
          <div className="ranking-head">
            <div><p className="eyebrow">RANKING DE CONSISTÊNCIA</p><h3>Valorização com menor variância</h3><p>Compare retorno e risco dentro do universo selecionado.</p></div>
            <div className="ranking-filters">
              <label>Mercado<select aria-label="Filtrar ranking por mercado" value={rankingMarket} onChange={(event) => setRankingMarket(event.target.value as MarketFilter)}>{Object.entries(marketLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
              <label>Classe<select aria-label="Filtrar ranking por classe" value={rankingClass} onChange={(event) => setRankingClass(event.target.value as ClassFilter)}>{Object.entries(classLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            </div>
          </div>
          <div className="ranking-scroll">
            <table>
              <thead><tr><th>Posição e ativo</th><th>Mercado</th><th>Retorno 1M</th><th>Volatilidade</th><th>Drawdown</th><th>Score relativo</th></tr></thead>
              <tbody>{ranking.map((item, index) => <tr key={item.ticker}>
                <td><span className="rank-number">{index + 1}</span><button className="rank-asset" onClick={() => setSelected(item.ticker)}><i style={{background: item.color}}>{item.ticker[0]}</i><span><strong>{item.ticker}</strong><small>{item.name}</small></span></button></td>
                <td><strong className="market-badge">{item.market}</strong><small>{classLabels[item.assetClass]}</small></td>
                <td><strong className={item.month >= 0 ? "up" : "down"}>{item.month >= 0 ? "+" : ""}{item.month.toFixed(1)}%</strong></td>
                <td>{item.volatility.toFixed(1)}%</td>
                <td className="down">{item.drawdown.toFixed(1)}%</td>
                <td><div className="score-cell"><strong>{item.score}</strong><span><i style={{width: `${item.score}%`}} /></span></div></td>
              </tr>)}</tbody>
            </table>
            {!ranking.length && <p className="ranking-empty">Nenhum ativo disponível para esta combinação de filtros.</p>}
          </div>
          <p className="ranking-method"><strong>Como calculamos:</strong> 40% retorno em 1 mês · 30% menor volatilidade · 20% menor drawdown · 10% retorno em 1 ano. Score relativo de 0 a 100; não constitui recomendação.</p>
        </section>

        <div className="grid">
          <section className="card analysis">
            <div className="card-head"><div><p className="eyebrow">ANÁLISE PRINCIPAL</p><div className="asset-title"><span style={{background: asset.color}}>{asset.ticker[0]}</span><div><h2>{asset.name}</h2><p>{asset.ticker} · {asset.market}</p></div></div></div><button className="ghost">Adicionar à lista +</button></div>
            <div className="price-row"><div><strong>{asset.currency} {asset.price.toLocaleString("pt-BR", {minimumFractionDigits:2})}</strong><span className={asset.change >= 0 ? "up pill" : "down pill"}>{asset.change >= 0 ? "↗" : "↘"} {Math.abs(asset.change).toFixed(2)}%</span></div><small>Último fechamento · {historyMode === "live" ? `${historyPoints.length} pontos armazenados` : historyMode === "loading" ? "carregando histórico" : dataMode === "live" ? "fonte conectada" : "modo demonstrativo"}</small></div>
            <div className="periods">{periods.map(p => <button key={p} onClick={() => setPeriod(p)} className={period === p ? "selected" : ""}>{p}</button>)}</div>
            <div className="chart" aria-label={`Gráfico de ${asset.name} no período ${period}`}>
              <div className="grid-lines"><i/><i/><i/><i/></div>
              <div className="bars">{chartBars.map((point,i) => <b key={`${point.label}-${i}`} title={point.label} style={{height:`${point.height}%`, background: asset.color, opacity: .34 + i / Math.max(chartBars.length * 1.8, 1)}} />)}</div>
              <div className="history-status"><span className={historyMode === "live" ? "history-live" : ""} />{historyMode === "live" ? "Histórico persistido no Supabase" : historyMode === "loading" ? "Consultando histórico…" : "Visualização temporária"}</div>
              <div className="chart-labels">{chartLabels.map((label) => <span key={label}>{label}</span>)}</div>
            </div>
            <div className="metrics">
              <div><small>RETORNO 1M</small><strong className="up">+{asset.month.toFixed(1)}%</strong></div>
              <div><small>VOLATILIDADE</small><strong>{asset.volatility.toFixed(1)}%</strong></div>
              <div><small>BETA</small><strong>{asset.beta.toFixed(2)}</strong></div>
              <div><small>MAX. DRAWDOWN</small><strong className="down">{asset.drawdown.toFixed(1)}%</strong></div>
              <div><small>VOLUME MÉDIO</small><strong>{asset.volume}</strong></div>
            </div>
          </section>

          <aside className="right-column">
            <section className="card watchlist">
              <div className="card-head"><div><p className="eyebrow">MINHA LISTA</p><h3>Ativos monitorados</h3></div><span className="count">{watch.length}</span></div>
              {watch.map(item => <button key={item.ticker} onClick={() => setSelected(item.ticker)} className={selected === item.ticker ? "watch active-row" : "watch"}><span className="mini-logo" style={{background:item.color}}>{item.ticker[0]}</span><span><strong>{item.ticker}</strong><small>{item.name}</small></span><span className="watch-price"><strong>{item.currency} {item.price.toFixed(2)}</strong><em className={item.change >= 0 ? "up" : "down"}>{item.change >= 0 ? "+" : ""}{item.change.toFixed(2)}%</em></span></button>)}
            </section>
            <section className="card bdr-card">
              <p className="eyebrow">CALCULADORA DE BDR</p><h3>Paridade cambial</h3>
              <label>Dólar comercial <span>R$ {usd.toFixed(2)}</span><input type="range" min="4.5" max="6.5" step="0.01" value={usd} onChange={e => setUsd(Number(e.target.value))}/></label>
              <div className="formula"><span>Ação original</span><strong>{asset.currency} {asset.price.toFixed(2)}</strong><i>× {usd.toFixed(2)} ÷ {asset.ticker === "RNG" ? 25 : 20}</i><span>BDR teórico</span><strong>{theoretical ? `R$ ${theoretical.toFixed(2)}` : "Selecione TEAM ou RNG"}</strong></div>
            </section>
          </aside>
        </div>

        <section className="card explorer">
          <div className="card-head"><div><p className="eyebrow">EXPLORADOR MULTIATIVOS</p><h3>Ações, BDRs, moedas e índices</h3></div><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Buscar ticker, empresa ou mercado..." aria-label="Buscar ativo" /></div>
          <div className="asset-chips">{filtered.map(item => <button key={item.ticker} onClick={() => {setSelected(item.ticker); setQuery("")}}><span style={{background:item.color}}>{item.ticker[0]}</span><strong>{item.ticker}</strong><small>{item.market}</small></button>)}</div>
        </section>

        <section className="card data-health-card">
          <div className="health-head">
            <div><p className="eyebrow">SAÚDE DOS DADOS</p><h3>Coleta e cobertura histórica</h3><p>A rotina diária verifica cada ativo e registra qualquer falha para recuperação.</p></div>
            <span className={`health-badge ${dataHealth?.status === "healthy" ? "healthy" : "attention"}`}><i />{dataHealth ? dataHealth.status === "healthy" ? "Operação estável" : "Requer atenção" : "Conectando monitor"}</span>
          </div>
          {dataHealth ? <>
            <div className="health-metrics">
              <div><small>ATIVOS ATUAIS</small><strong>{dataHealth.current_assets}<em>/{dataHealth.total_assets}</em></strong></div>
              <div><small>COBERTURA</small><strong>{dataHealth.coverage_pct.toFixed(1)}<em>%</em></strong></div>
              <div><small>REGISTROS HISTÓRICOS</small><strong>{Intl.NumberFormat("pt-BR", { notation: "compact" }).format(dataHealth.total_price_rows)}</strong></div>
              <div><small>PENDÊNCIAS</small><strong>{dataHealth.stale_assets + dataHealth.error_assets + dataHealth.missing_assets}</strong></div>
            </div>
            <div className="health-footer"><span>Última verificação: {new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(dataHealth.checked_at))}</span><div>{dataHealth.items.filter((item) => item.status !== "current").slice(0, 5).map((item) => <span key={item.ticker} className={`health-issue ${item.status}`}>{item.ticker} · {item.status === "stale" ? "atrasado" : item.status === "error" ? "falha" : "sem histórico"}</span>)}</div></div>
          </> : <p className="health-placeholder">O monitor será preenchido assim que a API concluir a consulta de integridade.</p>}
        </section>
      </section>
    </main>
  );
}
