import { useEffect, useState } from 'react'

type Props = { guildId: string }
type Settings = { prefix: string }
const defaults: Settings = { prefix: 'stray?' }

export function BotSettingsPanel({ guildId }: Props) {
  const storageKey = `nora-bot-settings:${guildId}`
  const [settings, setSettings] = useState<Settings>(defaults)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(storageKey)
    if (stored) {
      try { setSettings({ ...defaults, ...JSON.parse(stored) }) } catch { /* ignore invalid local settings */ }
    }
  }, [storageKey])

  const update = <K extends keyof Settings>(key: K, value: Settings[K]) => setSettings((current) => ({ ...current, [key]: value }))
  const save = () => { localStorage.setItem(storageKey, JSON.stringify(settings)); setSaved(true); window.setTimeout(() => setSaved(false), 2200) }

  return <section className="bot-settings-panel">
    <div className="bot-settings-intro"><div><p className="discord-eyebrow">BOT SETTINGS</p><h2>Botの設定</h2><p>このサーバーでの、のらねこBotの動作を設定します。</p></div><span className="settings-badge">SERVER CONFIG</span></div>
    <div className="settings-group"><h3>コマンド設定</h3><label className="settings-field"><span>コマンドプレフィックス</span><input value={settings.prefix} onChange={(event) => update('prefix', event.target.value)} maxLength={10} /></label><small className="settings-help">例: stray?mention のように使用します。</small></div>
    <div className="settings-actions"><button type="button" onClick={save}>設定を保存</button>{saved && <span>保存しました。</span>}</div>
  </section>
}
