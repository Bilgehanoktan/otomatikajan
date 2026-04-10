import type { CollectionConfig } from 'payload'
import { isEditorOrAdmin, isAdmin } from '../access/auth'

export const SkillCatalog: CollectionConfig = {
  slug: 'skill-catalog',
  admin: {
    useAsTitle: 'displayName',
    group: 'AI Config',
  },
  access: {
    read: isEditorOrAdmin,
    create: isAdmin,
    update: isAdmin,
    delete: isAdmin,
  },
  fields: [
    {
      name: 'skillId',
      type: 'text',
      required: true,
      unique: true,
    },
    {
      name: 'displayName',
      type: 'text',
      required: true,
    },
    {
      name: 'summary',
      type: 'textarea',
    },
    {
      name: 'inputSchemaText',
      type: 'textarea',
    },
    {
      name: 'outputSchemaText',
      type: 'textarea',
    },
    {
      name: 'exampleUseCases',
      type: 'array',
      fields: [
        {
          name: 'example',
          type: 'textarea',
          required: true,
        },
      ],
    },
    {
      name: 'enabledForUI',
      type: 'checkbox',
      defaultValue: true,
    },
    {
      name: 'docsUrl',
      type: 'text',
    },
  ],
}
