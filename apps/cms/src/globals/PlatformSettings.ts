import type { GlobalConfig } from 'payload'
import { isEditorOrAdmin } from '../access/auth'

export const PlatformSettings: GlobalConfig = {
  slug: 'platform-settings',
  admin: {
    group: 'Settings',
  },
  access: {
    read: () => true,
    update: isEditorOrAdmin,
  },
  fields: [
    {
      name: 'platformName',
      type: 'text',
      defaultValue: 'Sovereign AGI',
    },
    {
      name: 'supportEmail',
      type: 'text',
    },
    {
      name: 'maintenanceBanner',
      type: 'text',
    },
    {
      name: 'showMaintenanceBanner',
      type: 'checkbox',
      defaultValue: false,
    },
  ],
}
