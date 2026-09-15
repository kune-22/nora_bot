import './Header.css'

export type HeaderSession = {
  user: { username: string; avatarUrl?: string }
}

type HeaderProps = {
  session: HeaderSession | null
  onTop: () => void
  onManage: () => void
  onLogout: () => void
}

function Brand({ onClick }: { onClick: () => void }) {
  return <button className="brand brand-button" type="button" onClick={onClick}><span className="brand-mark">N</span><span>のらねこbot</span></button>
}

export function Header({ session, onTop, onManage, onLogout }: HeaderProps) {
  return <header className="app-header"><Brand onClick={onTop} /><div className="header-actions"><nav className="app-nav" aria-label="メインナビゲーション"><button type="button" onClick={onTop}>TOP</button><button type="button" onClick={onManage}>MANAGE</button></nav><div className="header-account">{session ? <><span>{session.user.username}</span>{session.user.avatarUrl ? <img src={session.user.avatarUrl} alt="" /> : <span className="avatar-fallback">{session.user.username.slice(0, 1).toUpperCase()}</span>}<button className="logout-link" type="button" onClick={onLogout}>ログアウト</button></> : <button className="nav-login" type="button" onClick={onManage}>ログイン</button>}</div></div></header>
}
