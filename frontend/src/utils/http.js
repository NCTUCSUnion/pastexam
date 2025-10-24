export function isUnauthorizedError(error) {
  if (!error) return false

  if (error.isUnauthorized) return true

  const status = error.response?.status ?? error.status
  return status === 401
}
