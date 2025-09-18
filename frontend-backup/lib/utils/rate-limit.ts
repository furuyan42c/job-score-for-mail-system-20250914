// Rate limiting utilities
// Basic implementation to resolve import errors

const requests = new Map();

export function rateLimit(key: string, limit: number = 100, windowMs: number = 60000) {
  const now = Date.now();
  const windowStart = now - windowMs;

  if (!requests.has(key)) {
    requests.set(key, []);
  }

  const keyRequests = requests.get(key);
  const recentRequests = keyRequests.filter((time: number) => time > windowStart);

  if (recentRequests.length >= limit) {
    return false;
  }

  recentRequests.push(now);
  requests.set(key, recentRequests);

  return true;
}

export function getRateLimit(key: string) {
  return requests.get(key) || [];
}