import crypto from 'node:crypto'
import type { CollectionAfterChangeHook } from 'payload'

export const emitWebhook: CollectionAfterChangeHook = async ({
  collection,
  doc,
  operation,
}) => {
  const webhookURL = process.env.FASTAPI_PAYLOAD_WEBHOOK_URL
  const webhookSecret = process.env.FASTAPI_PAYLOAD_WEBHOOK_SECRET

  if (!webhookURL || !webhookSecret) {
    return doc
  }

  const payload = {
    collection: collection.slug,
    operation,
    docId: doc?.id ?? null,
    slug: doc?.slug ?? null,
    status: doc?._status ?? null,
    updatedAt: doc?.updatedAt || new Date().toISOString(),
    payload: doc,
  }

  const rawBody = JSON.stringify(payload)
  const signature = crypto
    .createHmac('sha256', webhookSecret)
    .update(rawBody)
    .digest('hex')

  try {
    const response = await fetch(webhookURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Payload-Signature': signature,
        'X-Payload-Collection': collection.slug,
        'X-Payload-Operation': operation,
      },
      body: rawBody,
    })
    
    if (!response.ok) {
        console.error(`Payload webhook hatası: ${response.statusText}`)
    }
  } catch (error) {
    console.error('Payload webhook gönderimi başarısız:', error)
  }

  return doc
}
