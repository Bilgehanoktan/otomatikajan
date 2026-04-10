import type { CollectionConfig } from 'payload'
import { isAuthenticated, isEditorOrAdmin, isAdmin } from '../access/auth'

export const Media: CollectionConfig = {
  slug: 'media',
  access: {
    read: isAuthenticated,
    create: isEditorOrAdmin,
    update: isEditorOrAdmin,
    delete: isAdmin,
  },
  upload: true,
  admin: {
    useAsTitle: 'filename',
    group: 'Content',
  },
  fields: [
    {
      name: 'alt',
      type: 'text',
    },
    {
      name: 'category',
      type: 'select',
      options: [
        { label: 'Image', value: 'image' },
        { label: 'PDF', value: 'pdf' },
        { label: 'Diagram', value: 'diagram' },
        { label: 'Other', value: 'other' },
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
  ],
}
