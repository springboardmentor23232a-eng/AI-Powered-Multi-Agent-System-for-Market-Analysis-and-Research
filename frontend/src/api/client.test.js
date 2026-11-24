import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'
import { AxiosError, AxiosHeaders } from 'axios'
import api, { configureAuth, refreshSession } from './client.js'

const originalAdapter = api.defaults.adapter
const originalWindow = globalThis.window
const originalCustomEvent = globalThis.CustomEvent

function response(config, status, data) {
  return {
    config,
    data,
    headers: new AxiosHeaders(),
    status,
    statusText: status === 200 ? 'OK' : 'Error',
  }
}

function rejectResponse(config, status, data = {}) {
  const result = response(config, status, data)
  return Promise.reject(
    new AxiosError(`Request failed with status code ${status}`, AxiosError.ERR_BAD_RESPONSE, config, null, result),
  )
}

afterEach(() => {
  api.defaults.adapter = originalAdapter
  configureAuth({ getToken: () => null, onExpired: () => {} })
  if (originalWindow === undefined) delete globalThis.window
  else globalThis.window = originalWindow
  if (originalCustomEvent === undefined) delete globalThis.CustomEvent
  else globalThis.CustomEvent = originalCustomEvent
})

test('Strict Mode startup and a 401 response share one refresh request', async () => {
  let releaseRefresh
  let refreshRequests = 0
  let protectedRequests = 0
  const refreshGate = new Promise((resolve) => {
    releaseRefresh = resolve
  })

  globalThis.CustomEvent = class {
    constructor(type, options) {
      this.type = type
      this.detail = options.detail
    }
  }
  globalThis.window = { dispatchEvent() {} }
  configureAuth({ getToken: () => null, onExpired: () => {} })
  api.defaults.adapter = async (config) => {
    if (config.url === '/auth/refresh') {
      refreshRequests += 1
      await refreshGate
      return response(config, 200, { access_token: 'fresh-token', user: { id: 1 } })
    }
    if (config.url === '/protected') {
      protectedRequests += 1
      if (protectedRequests === 1) return rejectResponse(config, 401)
      return response(config, 200, { ok: true })
    }
    throw new Error(`Unexpected request: ${config.url}`)
  }

  const startup = refreshSession()
  const strictModeStartup = refreshSession()
  const protectedRequest = api.get('/protected')
  await new Promise((resolve) => setImmediate(resolve))
  assert.equal(refreshRequests, 1)
  assert.equal(startup, strictModeStartup)

  releaseRefresh()
  const [session, , result] = await Promise.all([startup, strictModeStartup, protectedRequest])
  assert.equal(session.access_token, 'fresh-token')
  assert.equal(result.data.ok, true)
  assert.equal(refreshRequests, 1)
  assert.equal(protectedRequests, 2)
})

test('refresh authentication failures expire the session', async () => {
  let expiredCalls = 0
  configureAuth({ getToken: () => null, onExpired: () => { expiredCalls += 1 } })
  api.defaults.adapter = async (config) => {
    if (config.url === '/protected') return rejectResponse(config, 401)
    if (config.url === '/auth/refresh') return rejectResponse(config, 401)
    throw new Error(`Unexpected request: ${config.url}`)
  }

  await assert.rejects(api.get('/protected'), (error) => error.response.status === 401)
  assert.equal(expiredCalls, 1)
})

test('temporary refresh failures do not expire the session', async () => {
  let expiredCalls = 0
  configureAuth({ getToken: () => null, onExpired: () => { expiredCalls += 1 } })
  api.defaults.adapter = async (config) => {
    if (config.url === '/protected') return rejectResponse(config, 401)
    if (config.url === '/auth/refresh') return rejectResponse(config, 503)
    throw new Error(`Unexpected request: ${config.url}`)
  }

  await assert.rejects(api.get('/protected'), (error) => error.response.status === 503)
  assert.equal(expiredCalls, 0)
})

test('network refresh failures do not expire the session', async () => {
  let expiredCalls = 0
  configureAuth({ getToken: () => null, onExpired: () => { expiredCalls += 1 } })
  api.defaults.adapter = async (config) => {
    if (config.url === '/protected') return rejectResponse(config, 401)
    if (config.url === '/auth/refresh') {
      return Promise.reject(new AxiosError('Network Error', AxiosError.ERR_NETWORK, config))
    }
    throw new Error(`Unexpected request: ${config.url}`)
  }

  await assert.rejects(api.get('/protected'), (error) => error.code === AxiosError.ERR_NETWORK)
  assert.equal(expiredCalls, 0)
})
