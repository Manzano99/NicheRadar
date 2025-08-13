import { useEffect, useState } from "react";
import { fetchNotino } from "../api/scrape";

export default function NotinoList() {
  const [data, setData] = useState([]);
  const [country, setCountry] = useState("es");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchNotino(12, country)
      .then(setData)
      .catch(e => setErr(e.message))
      .finally(() => setLoading(false));
  }, [country]);

  return (
    <div style={{maxWidth: 1100, margin: "0 auto", padding: 16}}>
      <header style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom: 12}}>
        <h1 style={{fontSize: 22, fontWeight: 600}}>NicheRadar — Notino</h1>
        <select value={country} onChange={(e)=>setCountry(e.target.value)}>
          <option value="es">🇪🇸 ES</option>
          <option value="fr">🇫🇷 FR</option>
          <option value="de">🇩🇪 DE</option>
          <option value="it">🇮🇹 IT</option>
        </select>
      </header>

      {loading && <div>Cargando…</div>}
      {err && <div style={{color:"crimson"}}>Error: {err}</div>}

      {!loading && !err && (
        <div style={{
          display:"grid",
          gridTemplateColumns:"repeat(auto-fill, minmax(240px, 1fr))",
          gap: 12
        }}>
          {data.map((p, i) => (
            <a key={i} href={p.url} target="_blank" rel="noreferrer"
               style={{border:"1px solid #e5e7eb", borderRadius:12, padding:12, textDecoration:"none", color:"inherit"}}>
              {p.image && <img src={p.image} alt={p.name} style={{width:"100%", height:160, objectFit:"contain"}} />}
              <div style={{fontWeight:600, marginTop:8, fontSize:14, lineHeight:1.3}}>{p.name}</div>
              <div style={{opacity:0.8, marginTop:4}}>
                {Number(p.price).toFixed(2)} {p.currency}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}