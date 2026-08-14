"use client";

import { useEffect, useMemo, useState } from "react";

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
];

const periods = ["1D", "5D", "1M", "6M", "1A", "5A"];

type ApiAsset = {
  ticker: string; price: number; day_change_pct: number; return_1m_pct: number;
  return_1y_pct: number; annualized_volatility_pct: number | null;
  max_drawdown_pct: number | null; beta: number | null; volume: number | null;
  bars: number[]; currency: "USD" | "BRL";
};

export default function Home() {
  const [selected, setSelected] = useState("TEAM");
  const [period, setPeriod] = useState("1M");
  const [query, setQuery] = useState("");
  const [usd, setUsd] = useState(5.40);
  const [assets, setAssets] = useState(demoAssets);
  const [dataMode, setDataMode] = useState<"loading" | "live" | "demo" | "unavailable">("loading");
  const watch = assets.slice(0, 5);
  const asset = assets.find((item) => item.ticker === selected) ?? assets[0];
  const filtered = useMemo(() => assets.filter((item) => `${item.ticker} ${item.name}`.toLowerCase().includes(query.toLowerCase())), [query]);
  const theoretical = asset.ticker === "TEAM" ? asset.price * usd / 20 : asset.ticker === "RNG" ? asset.price * usd / 25 : null;

  useEffect(() => {
    fetch("/api/market").then((response) => response.json()).then((payload: { mode?: string; assets?: ApiAsset[] }) => {
      if (payload.mode === "live" && payload.assets?.length) {
        setAssets((current) => current.map((item) => {
          const live = payload.assets?.find((candidate) => candidate.ticker === item.ticker);
          if (!live) return item;
          return { ...item, currency: live.currency === "USD" ? "US$" : "R$", price: live.price,
            change: live.day_change_pct, month: live.return_1m_pct, year: live.return_1y_pct,
            volatility: live.annualized_volatility_pct ?? item.volatility, beta: live.beta ?? item.beta,
            drawdown: live.max_drawdown_pct ?? item.drawdown,
            volume: live.volume ? Intl.NumberFormat("pt-BR", { notation: "compact" }).format(live.volume) : item.volume,
            bars: live.bars?.length ? live.bars : item.bars };
        }));
        setDataMode("live");
      } else setDataMode(payload.mode === "unavailable" ? "unavailable" : "demo");
    }).catch(() => setDataMode("unavailable"));
  }, []);

  return (
    <main>
      <aside className="sidebar">
        <div className="brand"><span className="brandmark">V</span><div><strong>Vértice</strong><small>market intelligence</small></div></div>
        <nav>
          <button className="nav active"><span>◫</span> Visão geral</button>
          <button className="nav"><span>⌁</span> Análise de ativo</button>
          <button className="nav"><span>⇄</span> Comparador</button>
          <button className="nav"><span>◇</span> BDRs & spreads</button>
          <button className="nav"><span>⌗</span> Correlações</button>
        </nav>
        <div className="phase"><small>FASE 1</small><strong>Mercado & risco</strong><div><i /></div><span>Fundação do painel concluída</span></div>
        <div className="source-note"><span className="dot" /> {dataMode === "live" ? "Dados conectados" : dataMode === "loading" ? "Conectando dados" : "Dados demonstrativos"}<br/><small>{dataMode === "live" ? "API Python ativa" : "Conector Python preparado"}</small></div>
      </aside>

      <section className="workspace">
        <header>
          <div><p className="eyebrow">VISÃO GERAL</p><h1>Mercados em perspectiva</h1><p className="subtitle">Acompanhe ativos, risco e exposição cambial em um só lugar.</p></div>
          <div className="header-actions"><button className="date">14 AGO 2026 <span>⌄</span></button><button className="avatar">WG</button></div>
        </header>

        <div className="ticker-strip">
          {[{s:"IBOV",v:"138.742",c:0.42},{s:"S&P 500",v:"7.799",c:0.65},{s:"NASDAQ",v:"26.803",c:0.81},{s:"USD/BRL",v:"5,40",c:-0.24},{s:"VIX",v:"14,62",c:-0.07}].map(x => <div key={x.s}><small>{x.s}</small><strong>{x.v}</strong><em className={x.c >= 0 ? "up" : "down"}>{x.c >= 0 ? "+" : ""}{x.c.toFixed(2)}%</em></div>)}
        </div>

        <div className="grid">
          <section className="card analysis">
            <div className="card-head"><div><p className="eyebrow">ANÁLISE PRINCIPAL</p><div className="asset-title"><span style={{background: asset.color}}>{asset.ticker[0]}</span><div><h2>{asset.name}</h2><p>{asset.ticker} · {asset.market}</p></div></div></div><button className="ghost">Adicionar à lista +</button></div>
            <div className="price-row"><div><strong>{asset.currency} {asset.price.toLocaleString("pt-BR", {minimumFractionDigits:2})}</strong><span className={asset.change >= 0 ? "up pill" : "down pill"}>{asset.change >= 0 ? "↗" : "↘"} {Math.abs(asset.change).toFixed(2)}%</span></div><small>Último fechamento · {dataMode === "live" ? "fonte conectada" : "modo demonstrativo"}</small></div>
            <div className="periods">{periods.map(p => <button key={p} onClick={() => setPeriod(p)} className={period === p ? "selected" : ""}>{p}</button>)}</div>
            <div className="chart" aria-label={`Gráfico de ${asset.name} no período ${period}`}>
              <div className="grid-lines"><i/><i/><i/><i/></div>
              <div className="bars">{asset.bars.map((h,i) => <b key={i} style={{height:`${h}%`, background: asset.color, opacity: .26 + i/30}} />)}</div>
              <div className="chart-labels"><span>15 JUL</span><span>24 JUL</span><span>02 AGO</span><span>13 AGO</span></div>
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
          <div className="card-head"><div><p className="eyebrow">EXPLORADOR</p><h3>Encontre um ativo</h3></div><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Buscar ticker ou empresa..." aria-label="Buscar ativo" /></div>
          <div className="asset-chips">{filtered.map(item => <button key={item.ticker} onClick={() => {setSelected(item.ticker); setQuery("")}}><span style={{background:item.color}}>{item.ticker[0]}</span><strong>{item.ticker}</strong><small>{item.market}</small></button>)}</div>
        </section>
      </section>
    </main>
  );
}
