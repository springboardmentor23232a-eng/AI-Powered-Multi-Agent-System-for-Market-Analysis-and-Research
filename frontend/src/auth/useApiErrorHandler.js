import { useCallback } from 'react'

import { useAuth } from './AuthContext'

// Returns a function that turns an API error into a message for the user.
// If the server says the session is no longer valid (401), the user is logged out.
export function useApiErrorHandler() {
  const { logout } = useAuth()
  return useCallback(
    (error) => {
      if (error?.status === 401) {
        logout()
        return 'Your session has expired. Please sign in again.'
      }
      return error?.message ?? 'Something went wrong'
    },
    [logout],
  )
}
