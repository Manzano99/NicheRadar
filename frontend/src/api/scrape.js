export async function fetchNotino(limit = 8, country = 'es') {
  const res = await fetch(`/api/scrape/notino?limit=${limit}&country=${country}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}