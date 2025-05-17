export async function fetchServers(includeExcluded = false) {
  const url = includeExcluded ? '/api/servers?include_excluded=true' : '/api/servers';
  const res = await fetch(url);
  return res.json();
}

export async function excludeServers(ips) {
  try {
    await Promise.all(ips.map(ip =>
      fetch('/api/servers/exclude', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip })
      })
    ));
  } catch (err) {
    console.error("Error excluding servers:", err);
  }
}

export async function includeServers(ips) {
  try {
  await Promise.all(ips.map(ip =>
    fetch('/api/servers/include', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
      })
    ));
  } catch (err) {
    console.error("Error excluding servers:", err);
  }
}

export async function checkHost(ip, port) {
  const res = await fetch(`/api/servers/check?ip=${ip}&websockify_port=${port}`);
  if (!res.ok) throw new Error("Check failed");
  const j = await res.json();
  return j.reachable;
}
