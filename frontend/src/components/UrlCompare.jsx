import { useState } from "react";

export default function UrlCompare() {
  const [url, setUrl] = useState("");
  const [item, setItem] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  async function fetchItem() {
    setLoading(true); setErr(null); setItem(null);
    try {
      const res = await fetch(`/api/scrape/notino/product?url=${encodeURIComponent(url)}`);
      if (!res.ok) {
        const j = await res.json().catch(()=>null);
        throw new Error((j && j.detail) || `HTTP ${res.status}`);
      }
      const j = await res.json();
      setItem(j);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{maxWidth: 1100, margin:"24px auto", padding:16}}>
      <h2>Comparar por URL (Notino)</h2>
      <div style={{display:"flex", gap:8}}>
        <input
          value={url}
          onChange={e=>setUrl(e.target.value)}
          placeholder="Pega una URL de producto de Notino"
          style={{flex:1, padding:8}}
        />
        <button onClick={fetchItem} disabled={!url || loading} style={{padding:"8px 12px"}}>
          {loading ? "Buscando..." : "Obtener precio"}
        </button>
      </div>
      {err && <div style={{color:"crimson", marginTop:8}}>Error: {err}</div>}
      {item && (
        <div style={{marginTop:16, border:"1px solid #e5e7eb", borderRadius:12, padding:12, display:"flex", gap:16}}>
          {item.image && <img src={item.image} alt={item.name} style={{width:120, height:120, objectFit:"contain"}}/>}
          <div>
            <div style={{fontWeight:600}}>{item.name}</div>
            <div style={{opacity:0.8}}>{Number(item.price).toFixed(2)} {item.currency}</div>
            <a href={item.url} target="_blank" rel="noreferrer">Abrir en Notino</a>
          </div>
        </div>
      )}
    </div>
  );
}