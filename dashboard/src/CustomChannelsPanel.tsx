import { useEffect, useState } from 'react'

type Channel = {
  id: string
  name: string
  categoryName: string
  customRoleName: string
  customRoleId: number | null
  userCount: number
}

type Props = {
  guildId: string
  channels: Channel[]
  channelId?: string
  onChannelOpen?: (channelId: string) => void
  onRoleOpen?: (roleId: number) => void
  onBackToChannels?: () => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function responseError(response: Response, fallback: string) {
  const body = await response.json().catch(() => null) as { detail?: string } | null
  return body?.detail ? `${fallback} (${body.detail})` : `${fallback} (HTTP ${response.status})`
}

export function CustomChannelsPanel({ guildId, channels, channelId, onChannelOpen, onRoleOpen, onBackToChannels }: Props) {
  const selected = channelId === undefined ? undefined : channels.find((channel) => channel.id === channelId)
  const [channelName, setChannelName] = useState(selected?.name ?? '')
  const [editing, setEditing] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    setChannelName(selected?.name ?? '')
    setEditing(false)
    setMessage('')
    setError('')
  }, [selected?.id, selected?.name])

  if (channelId !== undefined) {
    if (!selected) return <section className="custom-channels-panel"><p className="channel-empty">チャンネル情報を取得できませんでした。</p></section>
    const saveName = async () => {
      const name = channelName.trim()
      if (!name) return setError('チャンネル名を入力してください。')
      setError('')
      const response = await fetch(`${API_BASE_URL}/api/guilds/${guildId}/custom-channels/${selected.id}`, { method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
      if (!response.ok) return setError(await responseError(response, 'チャンネル名を変更できませんでした。'))
      setEditing(false)
      setMessage('チャンネル名を変更しました。')
    }
    const removeChannel = async () => {
      if (!window.confirm(`#${selected.name} を削除しますか？`)) return
      const response = await fetch(`${API_BASE_URL}/api/guilds/${guildId}/custom-channels/${selected.id}`, { method: 'DELETE', credentials: 'include' })
      if (!response.ok) return setError(await responseError(response, 'チャンネルを削除できませんでした。'))
      onBackToChannels?.()
    }
    return <section className="custom-channels-panel"><button className="channel-back" type="button" onClick={onBackToChannels}>← チャンネル一覧に戻る</button><div className="channel-detail"><p className="discord-eyebrow">CUSTOM CHANNEL</p><h2>#{selected.name}</h2><p className="managed-channel-category">カテゴリ: {selected.categoryName}</p><p className="managed-channel-role">閲覧可能なカスタムロール: <b>{selected.customRoleName}</b></p><small>{selected.userCount} users</small><div className="channel-detail-actions">{editing ? <><input className="channel-name-input" value={channelName} onChange={(event) => setChannelName(event.target.value)} placeholder="新しいチャンネル名" /><button type="button" onClick={saveName}>保存</button><button className="muted" type="button" onClick={() => setEditing(false)}>キャンセル</button></> : <button type="button" onClick={() => { setChannelName(''); setEditing(true) }}>チャンネル名を変更</button>}<button type="button" onClick={() => selected.customRoleId !== null && onRoleOpen?.(selected.customRoleId)}>カスタムロール設定</button><button className="danger" type="button" onClick={removeChannel}>チャンネルを削除</button></div>{message && <p className="channel-message success">{message}</p>}{error && <p className="channel-message error">{error}</p>}</div></section>
  }

  const grouped = channels.reduce<Record<string, Channel[]>>((result, channel) => {
    const category = channel.categoryName || 'カテゴリなし'
    ;(result[category] ??= []).push(channel)
    return result
  }, {})

  const categories = Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b, 'ja'))

  return (
    <section className="custom-channels-panel">
      <div className="custom-channels-heading">
        <p className="discord-eyebrow">CUSTOM CHANNELS</p>
        <h2>カスタムロールで作成されたチャンネル</h2>
        <p>カスタムロールに紐づくチャンネルだけを表示しています。</p>
      </div>

      {categories.length === 0 ? (
        <p className="channel-empty">登録されているカスタムロール用チャンネルはありません。</p>
      ) : (
        categories.map(([categoryName, categoryChannels]) => (
          <section className="channel-category" key={categoryName}>
            <div className="channel-category-list">
              {categoryChannels.map((channel) => (
                    <article className="managed-channel-card" key={channel.id} role="button" tabIndex={0} onClick={() => onChannelOpen?.(channel.id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onChannelOpen?.(channel.id) }}>
                  <span className="managed-channel-category">{categoryName}</span>
                  <div className="managed-channel-name">
                    <span className="channel-hash">#</span>
                    <strong>{channel.name}</strong>
                  </div>
                  <p className="managed-channel-role">
                    閲覧可能なカスタムロール: <b>{channel.customRoleName}</b>
                  </p>
                  <small>{channel.userCount} users</small>
                    </article>
              ))}
            </div>
          </section>
        ))
      )}
    </section>
  )
}
