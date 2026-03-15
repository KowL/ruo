import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Shield, ChevronRight, Moon, Smartphone, Mail, Bot, Save, RotateCcw, Zap, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSettingsStore } from '@/store/settingsStore';
import { testConnection } from '@/api/openclaw';

const settingSections = [
  {
    title: '账户设置',
    items: [
      { id: 'profile', icon: User, label: '个人资料', type: 'link' as const },
      { id: 'security', icon: Shield, label: '账号安全', type: 'link' as const },
    ],
  },
  {
    title: '通知设置',
    items: [
      { id: 'push', icon: Smartphone, label: '推送通知', type: 'toggle' as const, value: true },
      { id: 'email', icon: Mail, label: '邮件通知', type: 'toggle' as const, value: false },
    ],
  },
  {
    title: '外观设置',
    items: [
      { id: 'darkMode', icon: Moon, label: '深色模式', type: 'toggle' as const, value: true },
    ],
  },
];

export function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, boolean>>({
    push: true,
    email: false,
    darkMode: true,
  });

  const { openclaw, setOpenClawConfig, resetOpenClawConfig } = useSettingsStore();
  const [gatewayWsUrl, setGatewayWsUrl] = useState(openclaw.gatewayWsUrl);
  const [token, setToken] = useState(openclaw.token);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [connectStatus, setConnectStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle');
  const [connectMessage, setConnectMessage] = useState('');

  useEffect(() => {
    setGatewayWsUrl(openclaw.gatewayWsUrl || '');
    setToken(openclaw.token || '');
  }, [openclaw]);

  const handleToggle = (id: string) => {
    setSettings(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSaveOpenClaw = () => {
    setSaveStatus('saving');
    setOpenClawConfig({
      gatewayWsUrl: gatewayWsUrl.trim(),
      token: token.trim(),
    });
    setTimeout(() => {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }, 500);
  };

  const handleResetOpenClaw = () => {
    resetOpenClawConfig();
    setGatewayWsUrl('ws://localhost:18789');
    setToken('');
    setConnectStatus('idle');
    setConnectMessage('');
  };

  const handleConnectOpenClaw = async () => {
    setOpenClawConfig({
      gatewayWsUrl: gatewayWsUrl.trim(),
      token: token.trim(),
    });

    setConnectStatus('connecting');
    setConnectMessage('');

    try {
      const result = await testConnection();
      if (result.status === 'success') {
        setConnectStatus('success');
        setConnectMessage('连接成功');
      } else {
        setConnectStatus('error');
        setConnectMessage(result.message || '连接失败');
      }
    } catch (e) {
      setConnectStatus('error');
      setConnectMessage('连接异常，请检查网关地址');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-foreground">设置</h1>
        <p className="text-muted-foreground">管理你的账户偏好与系统配置</p>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="p-8 rounded-2xl bg-gradient-to-br from-primary/95 to-primary border border-primary/20 shadow-lg shadow-primary/10 relative overflow-hidden"
      >
        {/* Glow decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>

        <div className="flex items-center gap-6 relative z-10">
          <Avatar className="w-20 h-20 border-4 border-white/20 shadow-xl">
            <AvatarFallback className="bg-white/10 text-white text-2xl font-bold">R</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-1">Ruo 用户</h2>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-white/20 rounded text-[10px] text-white font-medium uppercase tracking-wider">Pro Account</span>
              <p className="text-white/70 text-sm">ruo@example.com</p>
            </div>
          </div>
          <Button variant="secondary" className="bg-white text-primary hover:bg-white/90 shadow-sm font-medium">
            编辑资料
          </Button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-1 gap-8">
        {/* OpenClaw 设置 */}
        <section className="space-y-4">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider px-1">网关连接</h3>
          <Card className="bg-card border-border shadow-sm overflow-hidden">
            <CardHeader className="pb-4 bg-muted/30">
              <CardTitle className="text-foreground flex items-center gap-2 text-base">
                <Bot className="w-5 h-5 text-primary" />
                OpenClaw Gateway 配置
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="grid gap-5">
                <div className="grid gap-2">
                  <Label htmlFor="gatewayWsUrl" className="text-foreground/80 font-medium">Gateway WebSocket URL</Label>
                  <Input
                    id="gatewayWsUrl"
                    value={gatewayWsUrl}
                    onChange={(e) => setGatewayWsUrl(e.target.value)}
                    placeholder="ws://localhost:18789"
                    className="bg-background border-border focus:ring-primary/20 h-11"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="token" className="text-foreground/80 font-medium">Gateway Token</Label>
                  <Input
                    id="token"
                    type="password"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="请输入鉴权 Token"
                    className="bg-background border-border focus:ring-primary/20 h-11"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <Button
                  onClick={handleConnectOpenClaw}
                  disabled={connectStatus === 'connecting'}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground min-w-[100px]"
                >
                  {connectStatus === 'connecting' ? (
                    <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                  ) : connectStatus === 'success' ? (
                    <CheckCircle className="w-4 h-4 mr-2" />
                  ) : connectStatus === 'error' ? (
                    <XCircle className="w-4 h-4 mr-2" />
                  ) : (
                    <Zap className="w-4 h-4 mr-2" />
                  )}
                  {connectStatus === 'connecting' ? '连接中' : connectStatus === 'success' ? '已成功' : connectStatus === 'error' ? '失败' : '测试连接'}
                </Button>

                <Button
                  onClick={handleSaveOpenClaw}
                  disabled={saveStatus === 'saving'}
                  variant="outline"
                  className="border-border hover:bg-muted min-w-[100px]"
                >
                  {saveStatus === 'saving' ? (
                    <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                  ) : saveStatus === 'saved' ? (
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {saveStatus === 'saved' ? '已保存' : '保存设置'}
                </Button>

                <Button
                  onClick={handleResetOpenClaw}
                  variant="ghost"
                  className="text-muted-foreground hover:text-foreground"
                >
                  重置默认
                </Button>
              </div>

              {connectMessage && (
                <div className={`text-sm flex items-center gap-2 p-3 rounded-lg ${connectStatus === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-destructive/10 text-destructive'
                  }`}>
                  <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                  {connectMessage}
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        {/* 其他分类设置 */}
        <div className="space-y-8">
          {settingSections.map((section) => (
            <section key={section.title} className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider px-1">{section.title}</h3>
              <Card className="bg-card border-border shadow-sm overflow-hidden">
                <div className="divide-y divide-border">
                  {section.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-5 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                          <item.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-foreground font-medium">{item.label}</p>
                        </div>
                      </div>
                      {item.type === 'toggle' ? (
                        <Switch
                          checked={settings[item.id]}
                          onCheckedChange={() => handleToggle(item.id)}
                          className="data-[state=checked]:bg-primary"
                        />
                      ) : (
                        <Button variant="ghost" size="sm" className="text-muted-foreground">
                          <ChevronRight className="w-5 h-5" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </section>
          ))}
        </div>
      </div>

      <div className="text-center pt-8 pb-12 opacity-50">
        <div className="flex items-center justify-center gap-2 mb-1">
          <div className="w-1.5 h-1.5 rounded-full bg-primary/60"></div>
          <p className="text-sm font-medium tracking-tight">RUO AI CONTROL CENTER</p>
          <div className="w-1.5 h-1.5 rounded-full bg-primary/60"></div>
        </div>
        <p className="text-xs">Version 2.1.0 • Built with passion</p>
      </div>
    </div>
  );
}
