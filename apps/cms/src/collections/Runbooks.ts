import type { CollectionConfig } from 'payload'
import { isAuthenticated, isEditorOrAdmin, isAdmin } from '../access/auth'
import { emitWebhook } from '../hooks/emitWebhook'

export const Runbooks: CollectionConfig = {
  slug: 'runbooks',
  admin: {
    useAsTitle: 'title',
    group: 'Operations',
    defaultColumns: ['title', 'systemArea', 'severity', '_status', 'updatedAt'],
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
      name: 'systemArea',
      type: 'select',
      options: [
        { label: 'API', value: 'api' },
        { label: 'Worker', value: 'worker' },
        { label: 'Dashboard', value: 'dashboard' },
        { label: 'Database', value: 'database' },
        { label: 'Infra', value: 'infra' },
      ],
      required: true,
    },
    {
      name: 'severity',
      type: 'select',
      defaultValue: 'medium',
      options: [
        { label: 'Low', value: 'low' },
        { label: 'Medium', value: 'medium' },
        { label: 'High', value: 'high' },
        { label: 'Critical', value: 'critical' },
      ],
    },
    {
      name: 'preconditions',
      type: 'textarea',
    },
    {
      name: 'steps',
      type: 'array',
      required: true,
      fields: [
        {
          name: 'step',
          type: 'textarea',
          required: true,
        },
      ],
    },
    {
      name: 'rollbackSteps',
      type: 'array',
      fields: [
        {
          name: 'step',
          type: 'textarea',
          required: true,
        },
      ],
    },
    {
      name: 'owner',
      type: 'text',
    },
    {
      name: 'lastReviewedAt',
      type: 'date',
    },
    {
      name: 'revisionNote',
      type: 'textarea',
    },
  ],
}
