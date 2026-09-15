import { useState } from 'react'
import './ManageServer.css'

export type ManagedGuild = { id: string; name: string; iconUrl?: string; memberCount?: number }

type Props = { guild: ManagedGuild; onBack: () => void }

const menuItems = [
  { id: 'overview', label: '概要', icon: '⌂' },
  { id: 'roles', label: 'カスタムロール', icon: '◎' },
  { id: 'channels', label: 'チャンネル権限', icon: '▣' },
]

export function ManageServer({ guild, onBack }: Props) {
  const [activeMenu, setActiveMenu] = useState('overview')
  return <div className="manage-layout">
    <aside className="manage-sidebar"><button className="server-switcher" type="button" onClick={onBack}>{guild.iconUrl ? <img src={guild.iconUrl} alt="" /> : <span>{guild.name.slice(0, 1)}</span>}<strong>{guild.name}</strong><small>サーバーを変更</small><b>⌄</b></button><p className="sidebar-label">SERVER MANAGEMENT</p><nav>{menuItems.map((item) => <button className={activeMenu === item.id ? 'active' : ''} key={item.id} type="button" onClick={() => setActiveMenu(item.id)}><i>{item.icon}</i>{item.label}</button>)}</nav><div className="sidebar-bottom"><span className="online-dot" /> Bot online</div></aside>
    <main className="manage-content"><div className="manage-breadcrumb">{guild.name} <span>/</span> {menuItems.find((item) => item.id === activeMenu)?.label}</div>{activeMenu === 'overview' && <><div className="manage-heading"><div><p className="discord-eyebrow">SERVER OVERVIEW</p><h1>{guild.name}の概要</h1><p>サーバーの設定と状態をここから確認できます。</p></div><div className="guild-large-icon">{guild.iconUrl ? <img src={guild.iconUrl} alt="" /> : guild.name.slice(0, 1)}</div></div><div className="manage-stats"><article><span>メンバー</span><strong>{guild.memberCount?.toLocaleString() ?? '--'}</strong><small>Discord members</small></article><article><span>カスタムロール</span><strong>--</strong><small>登録済みロール</small></article><article><span>管理チャンネル</span><strong>--</strong><small>権限設定済み</small></article></div><section className="quick-panel"><h2>クイック操作</h2><div><button type="button" onClick={() => setActiveMenu('roles')}><b>◎</b><span><strong>カスタムロールを管理</strong><small>作成・付与・削除を行います</small></span><em>→</em></button><button type="button" onClick={() => setActiveMenu('channels')}><b>▣</b><span><strong>チャンネル権限を管理</strong><small>ロールごとの閲覧権限を設定します</small></span><em>→</em></button></div></section></>}{activeMenu !== 'overview' && <section className="empty-manage"><p className="discord-eyebrow">{activeMenu === 'roles' ? 'CUSTOM ROLES' : 'CHANNEL PERMISSIONS'}</p><h1>{menuItems.find((item) => item.id === activeMenu)?.label}</h1><p>この画面の操作機能をここへ追加していきます。</p><div className="coming-soon">Coming soon</div></section>}</main>
  </div>
}
