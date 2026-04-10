import type { GlobalConfig } from 'payload'
import { isEditorOrAdmin } from '../access/auth'

export const DashboardContent: GlobalConfig = {
  slug: 'dashboard-content',
  admin: {
    group: 'Settings',
  },
  access: {
    read: () => true,
    update: isEditorOrAdmin,
  },
  versions: {
    drafts: true,
  },
  fields: [
    {
      name: 'welcomeTitle',
      type: 'text',
    },
    {
      name: 'welcomeText',
      type: 'textarea',
    },
    {
      name: 'helpLinks',
      type: 'array',
      fields: [
        {
          name: 'label',
          type: 'text',
          required: true,
        },
        {
          name: 'url',
          type: 'text',
          required: true,
        },
      ],
    },
  ],
}
