import { useEffect, useState } from 'react'
import { Header } from './Header'
import type { HeaderSession } from './Header'
import { CustomRolesPanel } from './CustomRolesPanel'
import { CustomChannelsPanel } from './CustomChannelsPanel'
import './ServerManagePage.css'

export type ManageGuild = { id: string; name: string; iconUrl?: string; memberCount?: number }
export type DashboardSection = 'home' | 'custom-roles' | 'custom-role-settings' | 'custom-channels' | 'custom-role-detail' | 'custom-channel-detail' | 'settings'
type Props = { session: HeaderSession; guild: ManageGuild; section: DashboardSection; roleId?: number; channelId?: string; onSectionChange: (section: DashboardSection) => void; onRoleOpen: (roleId: number) => void; onChannelOpen: (channelId: string) => void; onTop: () => void; onManage: () => void; onLogout: () => void }
type DashboardData = {
  customRoleCount: number
  customRoles: Array<{ id: number; name: string }>
  customRoleChannelCount: number
  channels: Array<{ id: string; name: string; categoryName: string; customRoleName: string; customRoleId: number | null; userCount: number }>
}
const sectionLabels: Record<DashboardSection, string> = { home: 'HOME', 'custom-roles': 'Custom roles', 'custom-role-settings': 'Custom role setting', 'custom-channels': 'Custom channels', 'custom-role-detail': 'Custom role', 'custom-channel-detail': 'Custom channel', settings: 'Settings' }
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export function ServerManagePage({ session, guild, section, roleId, channelId, onSectionChange, onRoleOpen, onChannelOpen, onTop, onManage, onLogout }: Props) {
  const activeMenu = sectionLabels[section]
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [dashboardError, setDashboardError] = useState('')

  useEffect(() => {
    let cancelled = false
    setDashboardError('')
    fetch(`${API_BASE_URL}/api/guilds/${encodeURIComponent(guild.id)}/dashboard`, { credentials: 'include' })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('dashboard request failed')))
      .then((data: DashboardData) => { if (!cancelled) setDashboard(data) })
      .catch(() => { if (!cancelled) setDashboardError('サーバー情報を取得できませんでした。') })
    return () => { cancelled = true }
  }, [guild.id])

  return <div className="server-manage-page"><Header session={session} onTop={onTop} onManage={onManage} onLogout={onLogout} /><div className="server-manage-layout"><aside className="server-sidebar"><div className="server-summary">{guild.iconUrl ? <img src={guild.iconUrl} alt="" /> : <span>{guild.name.slice(0, 1)}</span>}<div><strong>{guild.name}</strong><small>サーバー管理</small></div></div><p className="sidebar-label">SERVER TOP</p><nav><button className={section === 'home' ? 'active' : ''} type="button" onClick={() => onSectionChange('home')}><span>⌂</span>HOME</button></nav><p className="sidebar-label">CUSTOM ROLES</p><nav><button className={section === 'custom-roles' || section === 'custom-role-detail' ? 'active' : ''} type="button" onClick={() => onSectionChange('custom-roles')}><span>◎</span>Custom roles</button><button className={section === 'custom-channels' || section === 'custom-channel-detail' ? 'active' : ''} type="button" onClick={() => onSectionChange('custom-channels')}><span>#</span>Custom channels</button><button className={section === 'custom-role-settings' ? 'active' : ''} type="button" onClick={() => onSectionChange('custom-role-settings')}><span>⚙</span>Custom role setting</button></nav><p className="sidebar-label">BOT SETTINGS</p><nav><button className={section === 'settings' ? 'active' : ''} type="button" onClick={() => onSectionChange('settings')}><span>⚙</span>Settings</button></nav><div className="sidebar-footer">のらねこbot<br /><small>Connected</small></div></aside><main className="server-content"><div className="content-heading"><div><p className="discord-eyebrow">SERVER CONTROL</p><h1>{activeMenu}</h1><p>「{guild.name}」の設定を管理します。</p></div><span className="online-pill"><i /> Bot Online</span></div>{(section === 'custom-roles' || section === 'custom-role-detail') ? <CustomRolesPanel guildId={guild.id} roleId={roleId} onRoleOpen={onRoleOpen} onBackToRoles={() => onSectionChange('custom-roles')} /> : (section === 'custom-channels' || section === 'custom-channel-detail') ? <CustomChannelsPanel guildId={guild.id} channels={dashboard?.channels ?? []} channelId={channelId} onChannelOpen={onChannelOpen} onRoleOpen={onRoleOpen} onBackToChannels={() => onSectionChange('custom-channels')} /> : <><section className="welcome-panel"><div><p className="discord-eyebrow">WELCOME BACK</p><h2>{guild.name}へようこそ。</h2><p>左のメニューから管理したい項目を選択してください。</p></div><div className="welcome-mark">✦</div></section>{dashboardError && <p className="dashboard-error">{dashboardError}</p>}<div className="manage-stats"><article><span className="stat-icon role">◎</span><div><small>カスタムロール</small><strong>{dashboard?.customRoleCount ?? '--'}</strong></div><em>Roles</em></article><article><span className="stat-icon channel">#</span><div><small>カスタムロール用チャンネル</small><strong>{dashboard?.customRoleChannelCount ?? '--'}</strong></div><em>Role channels</em></article><article><span className="stat-icon member">♙</span><div><small>サーバーメンバー</small><strong>{guild.memberCount?.toLocaleString() ?? '--'}</strong></div><em>Members</em></article></div><section className="managed-channels"><div className="section-title-row"><div><p className="discord-eyebrow">CUSTOM ROLE CHANNELS</p><h2>カスタムロールで作成されたチャンネル</h2></div><span>{dashboard?.customRoleChannelCount ?? '--'} 件</span></div>{dashboard?.channels.length ? <div className="channel-list">{dashboard.channels.map((channel) => <div className="channel-row" key={channel.id}><span className="channel-hash">#</span><div><strong>{channel.name}</strong><small>ロール: {channel.customRoleName}</small></div></div>)}</div> : <p className="channel-empty">登録されているカスタムロール用チャンネルはありません。</p>}</section><section className="quick-actions"><h2>Quick actions</h2><div><button type="button" onClick={() => onSectionChange('custom-roles')}><span>◎</span>カスタムロールを管理 <b>→</b></button><button type="button" onClick={() => onSectionChange('custom-channels')}><span>#</span>カスタムチャンネルを管理 <b>→</b></button></div></section></>}</main></div></div>
}
