import { useEffect, useState } from 'react'
import './App.css'
import { Header } from './Header'
import type { HeaderSession } from './Header'
import { ServerManagePage } from './ServerManagePage'
import type { DashboardSection, ManageGuild } from './ServerManagePage'

type Guild = ManageGuild
type Session = HeaderSession & { user: HeaderSession['user'] & { id: string }; guilds: Guild[] }
type Route =
  | { kind: 'top' }
  | { kind: 'servers' }
  | { kind: 'dashboard'; guildId: string; section: DashboardSection; roleId?: number; channelId?: string }
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const apiUrl = (path: string) => `${API_BASE_URL}${path}`

function routeFromLocation(): Route {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/'
  if (pathname === '/servers') return { kind: 'servers' }
  const dashboardMatch = pathname.match(/^\/dashboard\/([^/]+)\/(home|custom-roles|custom-roles\/settings|custom-roles\/channels(?:\/\d+)?|custom-roles\/\d+|settings)$/)
  if (dashboardMatch) {
    const sectionByPath: Record<string, DashboardSection> = {
      home: 'home',
      'custom-roles': 'custom-roles',
      'custom-roles/settings': 'custom-role-settings',
      'custom-roles/channels': 'custom-channels',
      settings: 'settings',
    }
    if (/^custom-roles\/channels\/\d+$/.test(dashboardMatch[2])) return { kind: 'dashboard', guildId: decodeURIComponent(dashboardMatch[1]), section: 'custom-channel-detail', channelId: dashboardMatch[2].split('/')[2] }
    if (/^custom-roles\/\d+$/.test(dashboardMatch[2])) return { kind: 'dashboard', guildId: decodeURIComponent(dashboardMatch[1]), section: 'custom-role-detail', roleId: Number(dashboardMatch[2].split('/')[1]) }
    return { kind: 'dashboard', guildId: decodeURIComponent(dashboardMatch[1]), section: sectionByPath[dashboardMatch[2]] }
  }
  return { kind: 'top' }
}

function LandingPage({ session, onManage, onTop, onLogout }: { session: Session | null; onManage: () => void; onTop: () => void; onLogout: () => void }) {
  const features = [{ icon: '◎', title: 'カスタムロール', description: 'サーバー内のロールを分かりやすく管理できます。' }, { icon: '▣', title: 'チャンネル権限', description: 'ロールに紐づくチャンネルの閲覧権限をまとめて操作できます。' }, { icon: '⌁', title: 'かんたん操作', description: 'Discordと連携して、必要な設定へすぐアクセスできます。' }]
  return <><Header session={session} onTop={onTop} onManage={onManage} onLogout={onLogout} /><section className="hero-section" id="top"><div className="hero-copy"><p className="eyebrow">DISCORD SERVER MANAGEMENT</p><h1>サーバー管理を、<br />もっと<span className="highlight-word">シンプル</span>に。</h1><p className="hero-description">のらねこbotは、カスタムロールとチャンネル権限を{`\n`}ひとつのダッシュボードから管理できるDiscord Botです。</p><div className="hero-actions"><button className="primary-button" type="button" onClick={onManage}>ダッシュボードを始める <span>→</span></button><a className="text-link" href="#features">機能を見る <span>↓</span></a></div></div><div className="hero-art" aria-hidden="true"><div className="orb orb-large" /><div className="orb orb-small" /><div className="dashboard-card"><div className="card-heading"><span className="status-dot" />サーバー管理</div><div className="card-server">Nora Server <span>•••</span></div><div className="metric-row"><span>カスタムロール</span><strong>24</strong></div><div className="metric-row"><span>管理チャンネル</span><strong>08</strong></div><div className="card-progress"><span /></div><div className="card-caption">すべて正常に動作中</div></div></div></section><section className="feature-section" id="features"><div className="section-heading"><p className="eyebrow">FEATURES</p><h2>必要な機能を、すぐに。</h2><p>複雑になりがちなサーバー管理を、直感的な操作にまとめました。</p></div><div className="feature-grid">{features.map((feature) => <article className="feature-card" key={feature.title}><div className="feature-icon">{feature.icon}</div><h3>{feature.title}</h3><p>{feature.description}</p><a href="#top">詳しく見る <span>↗</span></a></article>)}</div></section><section className="about-section" id="about"><div><p className="eyebrow">READY WHEN YOU ARE</p><h2>あなたのサーバーを、<br />あなたらしく。</h2></div><button className="primary-button" type="button" onClick={onManage}>Discordと接続する <span>→</span></button></section><footer className="footer"><span>© 2026 のらねこbot</span><span>Discord server management, made simple.</span></footer></>
}

function GuildSelectPage({ session, onTop, onManage, onLogout, onOpenGuild }: { session: Session; onTop: () => void; onManage: () => void; onLogout: () => void; onOpenGuild: (guild: Guild) => void }) {
  return <div className="dashboard-page" id="guilds"><Header session={session} onTop={onTop} onManage={onManage} onLogout={onLogout} /><section className="guild-page"><p className="eyebrow">YOUR DISCORD SERVERS</p><h1>管理するサーバーを選択</h1><p className="guild-lead">管理権限があり、のらねこbotが導入されているサーバーを選択してください。</p>{session.guilds.length === 0 ? <div className="empty-state">条件に一致するサーバーがありません。</div> : <div className="guild-grid">{session.guilds.map((guild) => <button className="guild-card" key={guild.id} type="button" onClick={() => onOpenGuild(guild)}>{guild.iconUrl ? <img src={guild.iconUrl} alt="" /> : <span className="guild-icon-fallback">{guild.name.slice(0, 1)}</span>}<span className="guild-info"><strong>{guild.name}</strong><small>{guild.memberCount ? `${guild.memberCount.toLocaleString()} メンバー` : 'Discordサーバー'}</small></span><span className="guild-paw">🐾</span></button>)}</div>}</section></div>
}

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [route, setRoute] = useState<Route>(() => routeFromLocation())
  const navigate = (path: string) => {
    window.history.pushState({}, '', path)
    setRoute(routeFromLocation())
  }
  useEffect(() => {
    const handlePopState = () => setRoute(routeFromLocation())
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])
  useEffect(() => { fetch(apiUrl('/api/auth/session'), { credentials: 'include' }).then((response) => response.ok ? response.json() : null).then((data) => setSession(data)).catch(() => setError('ログイン状態を確認できませんでした。')).finally(() => setLoading(false)) }, [])
  const startLogin = () => { window.location.href = apiUrl('/api/auth/discord') }
  const openManage = () => { session ? navigate('/servers') : startLogin() }
  const openGuild = (guild: Guild) => navigate(`/dashboard/${encodeURIComponent(guild.id)}/home`)
  const openDashboardSection = (guildId: string, section: DashboardSection) => {
    const pathBySection: Record<DashboardSection, string> = {
      home: 'home',
      'custom-roles': 'custom-roles',
      'custom-role-settings': 'custom-roles/settings',
      'custom-channels': 'custom-roles/channels',
      'custom-role-detail': 'custom-roles',
      'custom-channel-detail': 'custom-roles/channels',
      settings: 'settings',
    }
    navigate(`/dashboard/${encodeURIComponent(guildId)}/${pathBySection[section]}`)
  }
  const openRole = (guildId: string, roleId: number) => navigate(`/dashboard/${encodeURIComponent(guildId)}/custom-roles/${roleId}`)
  const openChannel = (guildId: string, channelId: string) => navigate(`/dashboard/${encodeURIComponent(guildId)}/custom-roles/channels/${channelId}`)
  const logout = async () => { await fetch(apiUrl('/api/auth/logout'), { method: 'POST', credentials: 'include' }); setSession(null); navigate('/') }
  if (loading) return <div className="loading-screen">読み込み中...</div>
  const selectedGuild = route.kind === 'dashboard' ? session?.guilds.find((guild) => guild.id === route.guildId) : undefined
  if (session && route.kind === 'dashboard' && selectedGuild) return <ServerManagePage session={session} guild={selectedGuild} section={route.section} roleId={route.roleId} channelId={route.channelId} onSectionChange={(section) => openDashboardSection(selectedGuild.id, section)} onRoleOpen={(roleId) => openRole(selectedGuild.id, roleId)} onChannelOpen={(channelId) => openChannel(selectedGuild.id, channelId)} onTop={() => navigate('/')} onManage={() => navigate('/servers')} onLogout={logout} />
  if (session && route.kind === 'servers') return <GuildSelectPage session={session} onTop={() => navigate('/')} onManage={openManage} onLogout={logout} onOpenGuild={openGuild} />
  return <><LandingPage session={session} onTop={() => navigate('/')} onManage={openManage} onLogout={logout} />{error && <div className="api-error">{error}</div>}</>
}

export default App
