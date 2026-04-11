import { withPayload } from '@payloadcms/next/withPayload'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Turbopack may cause issues with Payload 3.x CSS injection in some environments
  experimental: {
    turbo: {
      enabled: false,
    },
  },
}

export default withPayload(nextConfig, {
  configPath: path.resolve(__dirname, './payload.config.ts'),
})
