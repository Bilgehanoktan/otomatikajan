export const isAuthenticated = ({ req: { user } }: any) => {
  return Boolean(user)
}

export const isAdmin = ({ req: { user } }: any) => {
  return Boolean(user?.roles?.includes('admin'))
}

export const isEditorOrAdmin = ({ req: { user } }: any) => {
  const roles = user?.roles || []
  return roles.includes('admin') || roles.includes('editor')
}

export const isOperatorOrAbove = ({ req: { user } }: any) => {
  const roles = user?.roles || []
  return roles.includes('admin') || roles.includes('editor') || roles.includes('operator')
}
