import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ApiError, api } from '../api/client'
import App from '../App'
import { AuthProvider } from '../auth/AuthProvider'
import { installFakeBackend, storeValidSession } from './fakeBackend'

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('API client', () => {
  it('turns FastAPI validation errors into a readable message', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: [{ loc: ['body', 'ticker'], msg: 'Value error, Bad ticker' }] }), { status: 422 }),
    )
    await expect(api.addToWatchlist('t', 'X Y', 'NSE')).rejects.toThrow('ticker: Bad ticker')
  })

  it('reports an unreachable server clearly', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    const error = await api.me('t').catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(0)
    expect(error.message).toMatch(/Cannot reach the server/)
  })
})

describe('Routing and authentication', () => {
  it('sends anonymous users to the login page', async () => {
    installFakeBackend()
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('registers a new user and opens the workspace', async () => {
    const { state } = installFakeBackend()
    const user = userEvent.setup()
    renderApp('/register')

    await user.type(screen.getByLabelText('Email'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'Str0ngPassw0rd')
    await user.type(screen.getByLabelText('Confirm password'), 'Str0ngPassw0rd')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('heading', { name: 'Watchlist' })).toBeInTheDocument()
    expect(state.users['alice@example.com']).toBe('Str0ngPassw0rd')
    expect(JSON.parse(localStorage.getItem('sra.session')).token).toBe('valid-token')
  })

  it('validates passwords before calling the server', async () => {
    const { fetchMock } = installFakeBackend()
    const user = userEvent.setup()
    renderApp('/register')

    await user.type(screen.getByLabelText('Email'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'onlyletters')
    await user.type(screen.getByLabelText('Confirm password'), 'onlyletters')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(screen.getByRole('alert')).toHaveTextContent('at least one letter and one number')

    await user.clear(screen.getByLabelText('Password'))
    await user.type(screen.getByLabelText('Password'), 'Str0ngPassw0rd')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match')

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows the server message for wrong credentials', async () => {
    installFakeBackend()
    const user = userEvent.setup()
    renderApp('/login')

    await user.type(screen.getByLabelText('Email'), 'nobody@example.com')
    await user.type(screen.getByLabelText('Password'), 'Wr0ngpass')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })

  it('restores a stored session after a page reload', async () => {
    installFakeBackend()
    storeValidSession()
    renderApp('/')
    expect(await screen.findByText('alice@example.com')).toBeInTheDocument()
  })

  it('discards a stored session the server rejects', async () => {
    installFakeBackend()
    localStorage.setItem('sra.session', JSON.stringify({ token: 'revoked', expiresAt: Date.now() + 60_000 }))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(localStorage.getItem('sra.session')).toBeNull()
  })

  it('ignores an expired stored session', async () => {
    const { fetchMock } = installFakeBackend()
    localStorage.setItem('sra.session', JSON.stringify({ token: 'valid-token', expiresAt: Date.now() - 1 }))
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('signs out', async () => {
    installFakeBackend()
    storeValidSession()
    const user = userEvent.setup()
    renderApp('/')
    await user.click(await screen.findByRole('button', { name: 'Sign out' }))
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(localStorage.getItem('sra.session')).toBeNull()
  })
})

describe('Workspace', () => {
  it('adds, rejects duplicates, and removes watchlist stocks', async () => {
    installFakeBackend()
    storeValidSession()
    const user = userEvent.setup()
    renderApp('/')

    const tickerInput = await screen.findByLabelText('Ticker symbol')
    await user.type(tickerInput, ' reliance ')
    await user.click(screen.getByRole('button', { name: 'Add' }))
    const list = await screen.findByRole('list', { name: 'Saved stocks' })
    expect(within(list).getByText('RELIANCE')).toBeInTheDocument()

    await user.type(tickerInput, 'RELIANCE')
    await user.click(screen.getByRole('button', { name: 'Add' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('already saved')

    await user.click(screen.getByRole('button', { name: 'Remove RELIANCE (NSE)' }))
    expect(await screen.findByText('Your watchlist is empty.')).toBeInTheDocument()
  })

  it('rejects an invalid ticker without calling the server', async () => {
    const { fetchMock } = installFakeBackend()
    storeValidSession()
    const user = userEvent.setup()
    renderApp('/')

    await user.type(await screen.findByLabelText('Ticker symbol'), 'AB CD')
    const callsBefore = fetchMock.mock.calls.length
    await user.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Ticker may contain only')
    expect(fetchMock.mock.calls.length).toBe(callsBefore)
  })

  it('saves preferences', async () => {
    const { state } = installFakeBackend()
    storeValidSession()
    const user = userEvent.setup()
    renderApp('/')

    const saveButton = await screen.findByRole('button', { name: 'Save preferences' })
    expect(saveButton).toBeDisabled() // nothing changed yet
    await user.selectOptions(screen.getByLabelText('Default market'), 'NYSE')
    await user.click(saveButton)
    expect(await screen.findByText('Preferences saved')).toBeInTheDocument()
    expect(state.preferences.default_market).toBe('NYSE')
  })

  it('shows an honest empty research history', async () => {
    installFakeBackend()
    storeValidSession()
    renderApp('/')
    expect(await screen.findByText(/No research yet/)).toBeInTheDocument()
  })

  it('logs the user out when the server says the session expired', async () => {
    installFakeBackend()
    storeValidSession()
    renderApp('/')
    await screen.findByLabelText('Default market') // wait until the workspace has loaded
    // Simulate the token becoming invalid on the server.
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Could not validate credentials' }), { status: 401 }),
    )
    const user = userEvent.setup()
    await user.selectOptions(screen.getByLabelText('Default market'), 'BSE')
    await user.click(screen.getByRole('button', { name: 'Save preferences' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument())
  })
})
