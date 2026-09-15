import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

type CustomRole = { id: number; name: string }
type RoleUser = { id: string; name: string; avatarUrl?: string | null }
type Props = { guildId: string; roleId?: number; onRoleOpen: (roleId: number) => void; onBackToRoles: () => void }
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export function CustomRolesPanel({ guildId, roleId, onRoleOpen, onBackToRoles }: Props) {
  const [roles, setRoles] = useState<CustomRole[]>([])
  const [name, setName] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [selectionMode, setSelectionMode] = useState(false)
  const [assignedUsers, setAssignedUsers] = useState<RoleUser[]>([])
  const [searchResults, setSearchResults] = useState<RoleUser[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState('')
  const [usersLoading, setUsersLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const loadRoles = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/dashboard`, { credentials: 'include' })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setRoles(data.customRoles ?? [])
    } catch {
      setError('カスタムロールを取得できませんでした。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadRoles() }, [guildId])

  const selectedRole = roles.find((role) => role.id === roleId) ?? null

  const loadRoleUsers = async () => {
    if (!roleId) return
    setUsersLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${roleId}/users`, { credentials: 'include' })
      if (!response.ok) throw new Error()
      const data = await response.json()
      setAssignedUsers(data.assignedUsers ?? [])
    } catch {
      setError('ロールユーザーを取得できませんでした。')
    } finally {
      setUsersLoading(false)
    }
  }

  useEffect(() => { if (roleId) void loadRoleUsers() }, [guildId, roleId])

  useEffect(() => {
    if (!roleId || searchQuery.trim().length < 1) { setSearchResults([]); return }
    const timer = window.setTimeout(async () => {
      setSearchLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${roleId}/users/search?q=${encodeURIComponent(searchQuery)}&limit=25`, { credentials: 'include' })
        const data = await response.json()
        setSearchResults(data.users ?? [])
      } finally {
        setSearchLoading(false)
      }
    }, 250)
    return () => window.clearTimeout(timer)
  }, [guildId, roleId, searchQuery])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setMessage('')
    setError('')
    const roleName = name.trim()
    if (!roleName) return setError('ロール名を入力してください。')
    const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: roleName }) })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) return setError(data.detail ?? 'カスタムロールを作成できませんでした。')
    setName('')
    setMessage(`「${roleName}」を作成しました。`)
    await loadRoles()
  }

  const saveEdit = async (role: CustomRole) => {
    const roleName = editingName.trim()
    if (!roleName) return setError('ロール名を入力してください。')
    const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${role.id}`, { method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: roleName }) })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) return setError(data.detail ?? 'カスタムロールを更新できませんでした。')
    setEditingId(null)
    setMessage(`「${roleName}」に変更しました。`)
    await loadRoles()
  }

  const remove = async (role: CustomRole) => {
    if (!window.confirm(`「${role.name}」を削除しますか？\n関連する付与情報とチャンネル紐づけも削除されます。`)) return
    const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${role.id}`, { method: 'DELETE', credentials: 'include' })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) return setError(data.detail ?? 'カスタムロールを削除できませんでした。')
    setMessage(`「${role.name}」を削除しました。`)
    await loadRoles()
  }

  const removeSelected = async () => {
    if (!selectedIds.length) return
    if (!window.confirm(`選択した${selectedIds.length}件のカスタムロールを削除しますか？`)) return
    const results = await Promise.all(selectedIds.map((id) => fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${id}`, { method: 'DELETE', credentials: 'include' })))
    if (results.some((response) => !response.ok)) return setError('一部のカスタムロールを削除できませんでした。')
    setSelectedIds([])
    setMessage(`${results.length}件のカスタムロールを削除しました。`)
    await loadRoles()
  }

  const addUser = async () => {
    const user = searchResults.find((item) => item.id === selectedUserId)
    if (!user || !roleId) return
    const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${roleId}/users`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ userId: Number(user.id), userName: user.name }) })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) return setError(data.detail ?? 'ユーザーにロールを付与できませんでした。')
    setSelectedUserId('')
    setMessage(`${user.name} にロールを付与しました。`)
    await loadRoleUsers()
  }

  const removeUser = async (user: RoleUser) => {
    if (!roleId || !window.confirm(`「${user.name}」からこのロールを外しますか？`)) return
    const response = await fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guildId)}/custom-roles/${roleId}/users/${user.id}`, { method: 'DELETE', credentials: 'include' })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) return setError(data.detail ?? 'ユーザーからロールを外せませんでした。')
    setMessage(`${user.name} からロールを外しました。`)
    await loadRoleUsers()
  }

  return <section className="custom-roles-panel">{selectedRole ? <><div className="custom-roles-intro"><div><button type="button" className="role-back" onClick={() => { setSelectionMode(false); setSelectedIds([]); onBackToRoles() }}>← Custom roles</button><p className="discord-eyebrow">ROLE DETAIL</p><h2>{selectedRole.name}</h2><p>このカスタムロールの名前を変更または削除できます。</p></div></div>{message && <p className="role-message success">{message}</p>}{error && <p className="role-message error">{error}</p>}<div className="role-detail-actions">{editingId === selectedRole.id ? <><input className="role-name-edit-input" value={editingName} onChange={(event) => setEditingName(event.target.value)} maxLength={100} placeholder="新しいロール名を入力" autoFocus /><button type="button" onClick={() => void saveEdit(selectedRole)}>保存</button><button type="button" className="muted" onClick={() => setEditingId(null)}>キャンセル</button></> : <><button type="button" onClick={() => { setEditingId(selectedRole.id); setEditingName(''); setError('') }}>ロール名を変更</button><button type="button" className="danger" onClick={() => void remove(selectedRole)}>削除</button></>}</div><section className="role-users-panel"><div className="role-users-heading"><div><p className="discord-eyebrow">ROLE MEMBERS</p><h3>このロールを付けているユーザー</h3></div><span>{assignedUsers.length}人</span></div>{usersLoading ? <p className="role-empty">読み込み中...</p> : assignedUsers.length ? <div className="assigned-user-list">{assignedUsers.map((user) => <div className="assigned-user-row" key={user.id}>{user.avatarUrl ? <img className="user-avatar" src={user.avatarUrl} alt="" /> : <span className="user-avatar">{user.name.slice(0, 1).toUpperCase()}</span>}<strong>{user.name}</strong><button type="button" onClick={() => void removeUser(user)}>ロールを外す</button></div>)}</div> : <p className="role-empty">このロールを付けているユーザーはいません。</p>}<div className="assign-user-form"><label htmlFor="role-user-select">未付与ユーザーにロールを付ける</label><div className="assign-user-controls"><input id="role-user-search" value={searchQuery} onChange={(event) => { setSearchQuery(event.target.value); setSelectedUserId('') }} placeholder="ユーザー名で検索" />{searchLoading ? <span className="user-search-status">検索中...</span> : searchResults.length > 0 && <select id="role-user-select" value={selectedUserId} onChange={(event) => setSelectedUserId(event.target.value)}><option value="">候補を選択</option>{searchResults.map((user) => <option key={user.id} value={user.id}>{user.name}</option>)}</select>}<button type="button" disabled={!selectedUserId} onClick={() => void addUser()}>付与する</button></div></div></section></> : <><div className="custom-roles-intro"><div><p className="discord-eyebrow">CUSTOM ROLES</p><h2>カスタムロールを管理</h2><p>サーバー内で使用するカスタムロールを登録・編集・削除できます。</p></div><span className="role-count">{roles.length} roles</span></div><form className="role-create-form" onSubmit={submit}><label htmlFor="custom-role-name">新しいカスタムロール</label><div><input id="custom-role-name" value={name} onChange={(event) => setName(event.target.value)} maxLength={100} placeholder="例: black cat" /><button type="submit" className="role-create-button">追加する</button></div></form>{message && <p className="role-message success">{message}</p>}{error && <p className="role-message error">{error}</p>}<div className="role-list-header"><h3>登録済みカスタムロール</h3><div className="role-list-tools"><button type="button" className="role-tool-button refresh" onClick={() => void loadRoles()}>更新</button><button type="button" className="role-tool-button select" onClick={() => { setSelectionMode((mode) => !mode); setSelectedIds([]) }}>{selectionMode ? 'キャンセル' : '選択'}</button>{selectionMode && <button type="button" className="danger" disabled={!selectedIds.length} onClick={() => void removeSelected()}>選択を削除 ({selectedIds.length})</button>}</div></div>{loading ? <p className="role-empty">読み込み中...</p> : roles.length === 0 ? <p className="role-empty">カスタムロールはまだありません。</p> : <div className="role-list">{roles.map((role) => <div className="role-row-wrap" key={role.id}>{selectionMode && <input type="checkbox" checked={selectedIds.includes(role.id)} onChange={(event) => setSelectedIds((current) => event.target.checked ? [...current, role.id] : current.filter((id) => id !== role.id))} />}<button className="role-row" type="button" onClick={() => selectionMode ? setSelectedIds((current) => current.includes(role.id) ? current.filter((id) => id !== role.id) : [...current, role.id]) : onRoleOpen(role.id)}><strong>{role.name}</strong></button></div>)}</div>}</>}</section>
}
