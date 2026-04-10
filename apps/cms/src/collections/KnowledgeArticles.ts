import type { CollectionConfig } from 'payload'
import { isAuthenticated, isEditorOrAdmin, isAdmin } from '../access/auth'
import { emitWebhook } from '../hooks/emitWebhook'

export const KnowledgeArticles: CollectionConfig = {
  slug: 'knowledge-articles',
  admin: {
    useAsTitle: 'title',
    group: 'Content',
    defaultColumns: ['title', 'slug', '_status', 'updatedAt'],
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
      name: 'slug',
      type: 'text',
      required: true,
      unique: true,
      index: true,
    },
    {
      name: 'summary',
      type: 'textarea',
    },
    {
      name: 'audience',
      type: 'select',
      defaultValue: 'internal',
      options: [
        { label: 'Internal', value: 'internal' },
        { label: 'Customer', value: 'customer' },
        { label: 'Operator', value: 'operator' },
      ],
    },
    {
      name: 'tags',
      type: 'array',
      fields: [
        {
          name: 'tag',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      name: 'content',
      type: 'richText',
      required: true,
    },
    {
      name: 'relatedRunbooks',
      type: 'relationship',
      relationTo: 'runbooks',
      hasMany: true,
    },
  ],
}
