import test from 'node:test'
import assert from 'node:assert/strict'
import { createRequestDeduper } from '../src/lib/requestDeduper.js'

test('identical overlapping reads share a request; later reads fetch fresh data', async () => {
  const read = createRequestDeduper()
  let calls = 0
  let resolve
  const fetch = () => { calls++; return new Promise(done => { resolve = done }) }
  const first = read('/news?tag=Finance', fetch)
  const second = read('/news?tag=Finance', fetch)
  assert.equal(first, second)
  await Promise.resolve()
  assert.equal(calls, 1)
  resolve(['finance story'])
  assert.deepEqual(await second, ['finance story'])
  assert.deepEqual(await read('/news?tag=Finance', () => ['new story']), ['new story'])
})

test('different filters do not share results and rejected requests can be retried', async () => {
  const read = createRequestDeduper()
  const [ai, finance] = await Promise.all([read('AI', () => ['AI']), read('Finance', () => ['Finance'])])
  assert.deepEqual(ai, ['AI'])
  assert.deepEqual(finance, ['Finance'])
  await assert.rejects(read('Finance', () => { throw new Error('offline') }), /offline/)
  assert.deepEqual(await read('Finance', () => ['recovered']), ['recovered'])
})
