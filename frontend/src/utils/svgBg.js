export function getCodeBgSvg() {
  const color =
    getComputedStyle(document.documentElement).getPropertyValue('--code-bg-svg-fill').trim() ||
    'rgba(60,60,60,0.07)'
  const encoded = encodeURIComponent(color)
  return `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><text x="20" y="30" font-family="monospace" font-size="10" fill="${encoded}">{}</text><text x="170" y="80" font-family="monospace" font-size="10" fill="${encoded}">for()</text><text x="60" y="150" font-family="monospace" font-size="10" fill="${encoded}">if()</text><text x="200" y="200" font-family="monospace" font-size="10" fill="${encoded}">while</text><text x="120" y="240" font-family="monospace" font-size="10" fill="${encoded}">;</text><text x="40" y="100" font-family="monospace" font-size="10" fill="${encoded}">==</text></svg>')`
}
