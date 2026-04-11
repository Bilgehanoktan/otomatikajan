import { handleRequests } from '@payloadcms/next/routes'
import config from '../../../../../payload.config'

export const GET = handleRequests({ config })
export const POST = handleRequests({ config })
export const OPTIONS = handleRequests({ config })
