import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Shield, ChevronRight, Moon, Smartphone, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

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

  const handleToggle = (id: string) => {
    setSettings(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-[#F8FAFC]">设置</h1>
        <p className="text-[#94A3B8]">管理你的账户和偏好设置</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="p-6 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#1D4ED8]"
      >
        <div className="flex items-center gap-4">
          <Avatar className="w-16 h-16 border-2 border-white/30">
            <AvatarFallback className="bg-white/20 text-white text-xl font-bold">R</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-white">Ruo</h2>
            <p className="text-blue-200">ruo@example.com</p>
          </div>
          <Button variant="secondary" size="sm" className="bg-white/20 text-white hover:bg-white/30">
            编辑资料
          </Button>
        </div>
      </motion.div>

      <div className="space-y-6">
        {settingSections.map((section, sectionIndex) => (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + sectionIndex * 0.1 }}
          >
            <h3 className="text-[#94A3B8] text-sm font-medium mb-3 px-1">{section.title}</h3>
            <div className="rounded-xl bg-[#1E293B] border border-[#334155] overflow-hidden">
              {section.items.map((item, itemIndex) => (
                <div key={item.id}>
                  <div className="flex items-center justify-between p-4 hover:bg-[#334155]/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-[#334155] flex items-center justify-center">
                        <item.icon className="w-4 h-4 text-[#94A3B8]" />
                      </div>
                      <span className="text-[#F8FAFC]">{item.label}</span>
                    </div>
                    {item.type === 'toggle' ? (
                      <Switch
                        checked={settings[item.id]}
                        onCheckedChange={() => handleToggle(item.id)}
                        className="data-[state=checked]:bg-[#2563EB]"
                      />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-[#94A3B8]" />
                    )}
                  </div>
                  {itemIndex < section.items.length - 1 && <Separator className="bg-[#334155]" />}
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="text-center py-6">
        <p className="text-[#94A3B8] text-sm">Ruo AI Control Center</p>
        <p className="text-[#475569] text-xs mt-1">版本 2.0.0</p>
      </motion.div>
    </div>
  );
}
