import type { CollectionConfig } from 'payload'
import { isAuthenticated, isEditorOrAdmin, isAdmin } from '../access/auth'
import { emitWebhook } from '../hooks/emitWebhook'

export const Announcements: CollectionConfig = {
  slug: 'announcements',
  admin: {
    useAsTitle: 'title',
    group: 'Content',
    defaultColumns: ['title', 'severity', 'startAt', 'endAt'],
  },
  access: {
    read: isAuthenticated,
    create: isEditorOrAdmin,
    update: isEditorOrAdmin,
    delete: isAdmin,
  },
  versions: {
    drafts: true,
  },
  hooks: {
    afterChange: [emitWebhook],
  },
  fields: [
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'message',
      type: 'textarea',
      required: true,
    },
    {
      name: 'severity',
      type: 'select',
      defaultValue: 'info',
      options: [
        { label: 'Info', value: 'info' },
        { label: 'Warning', value: 'warning' },
        { label: 'Critical', value: 'critical' },
      ],
    },
    {
      name: 'showOnDashboard',
      type: 'checkbox',
      defaultValue: true,
    },
    {
      name: 'startAt',
      type: 'date',
    },
    {
      name: 'endAt',
      type: 'date',
    },
  ],
}
