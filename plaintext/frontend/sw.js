const CACHE_NAME = "sulfluminense-v1";
const ARQUIVOS_CACHE = [
  "./",
  "./index.html",
  "./dados_noticias.json"
];

// Instalação — armazena arquivos essenciais
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ARQUIVOS_CACHE))
  );
  self.skipWaiting();
});

// Ativação — limpa caches antigos
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(nomes =>
      Promise.all(nomes.filter(n => n !== CACHE_NAME).map(c => caches.delete(c)))
    )
  );
  self.clients.claim();
});

// Estratégia: Rede primeiro, depois cache
self.addEventListener("fetch", e => {
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});