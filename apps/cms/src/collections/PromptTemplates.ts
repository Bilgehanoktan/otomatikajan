import type { CollectionConfig } from 'payload'
import { isEditorOrAdmin, isAdmin } from '../access/auth'
import { emitWebhook } from '../hooks/emitWebhook'

export const PromptTemplates: CollectionConfig = {
  slug: 'prompt-templates',
  admin: {
    useAsTitle: 'key',
    group: 'AI Config',
  },
  access: {
    read: isEditorOrAdmin,
    create: isAdmin,
    update: isAdmin,
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
      name: 'key',
      type: 'text',
      required: true,
      unique: true,
    },
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'purpose',
      type: 'textarea',
    },
    {
      name: 'template',
      type: 'textarea',
      required: true,
    },
    {
      name: 'variables',
      type: 'array',
      fields: [
        {
          name: 'name',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      name: 'safeForAutoUse',
      type: 'checkbox',
      defaultValue: false,
    },
  ],
}
