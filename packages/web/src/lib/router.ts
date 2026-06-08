export type RouteHandler = () => void;

let currentPath = window.location.pathname;
const listeners = new Set<() => void>();

export function getPath(): string {
  return currentPath;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notify(): void {
  for (const listener of listeners) listener();
}

export function navigate(path: string, replace = false): void {
  if (path === currentPath) return;
  if (replace) {
    window.history.replaceState({}, "", path);
  } else {
    window.history.pushState({}, "", path);
  }
  currentPath = path;
  notify();
}

export function parseDeckId(path: string): string | null {
  const match = path.match(/^\/deck\/([^/]+)$/);
  return match ? match[1] : null;
}

export function matchRoute(path: string): string {
  if (path === "/") return "home";
  if (path === "/library") return "library";
  if (path === "/build") return "build-redirect";
  if (path === "/build/review") return "build-review";
  if (path === "/build/result") return "build-result";
  if (parseDeckId(path)) return "deck-view";
  const stepMatch = path.match(/^\/build\/(\d)$/);
  if (stepMatch) return `build-step-${stepMatch[1]}`;
  return "not-found";
}

window.addEventListener("popstate", () => {
  currentPath = window.location.pathname;
  notify();
});
