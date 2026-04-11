import { postgresAdapter } from '@payloadcms/db-postgres'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import path from 'path'
import { buildConfig } from 'payload'
import { fileURLToPath } from 'url'
// import sharp from 'sharp'

import { Users } from './src/collections/Users'
import { Media } from './src/collections/Media'
import { KnowledgeArticles } from './src/collections/KnowledgeArticles'
import { Runbooks } from './src/collections/Runbooks'
import { Announcements } from './src/collections/Announcements'
import { PromptTemplates } from './src/collections/PromptTemplates'
import { SkillCatalog } from './src/collections/SkillCatalog'
import { DashboardContent } from './src/globals/DashboardContent'
import { PlatformSettings } from './src/globals/PlatformSettings'

const filename = fileURLToPath(import.meta.url)
const dirname = path.dirname(filename)

export default buildConfig({
  admin: {
    user: Users.slug,
    importMap: {
      baseDir: path.resolve(dirname),
    },
    components: {
      graphics: {
         Logo: './src/components/Logo#Logo',
         Icon: './src/components/Icon#Icon',
      },
    },
  },
  collections: [
    Users,
    Media,
    KnowledgeArticles,
    Runbooks,
    Announcements,
    PromptTemplates,
    SkillCatalog,
  ],
  globals: [
    DashboardContent,
    PlatformSettings,
  ],
  editor: lexicalEditor(),
  secret: process.env.PAYLOAD_SECRET || 'REPLACE_WITH_SECURE_SECRET',
  typescript: {
    outputFile: path.resolve(dirname, 'payload-types.ts'),
  },
  db: postgresAdapter({
    pool: {
      connectionString: process.env.DATABASE_URL || '',
    },
  }),
  // sharp,
})
