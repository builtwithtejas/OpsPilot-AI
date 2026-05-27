"use client";

import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, AlertTriangle, BarChart3, Rocket, Server, Settings, Bot, Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

const NAV = [
  { name: "Dashboard",      icon: LayoutDashboard, href: "/"               },
  { name: "Agent",          icon: Bot,             href: "/agent"          },
  { name: "Incidents",      icon: AlertTriangle,   href: "/incidents"      },
  { name: "Analytics",      icon: BarChart3,        href: "/analytics"      },
  { name: "Deployments",    icon: Rocket,           href: "/deployments"    },
  { name: "Infrastructure", icon: Server,           href: "/infrastructure" },
  { name: "Settings",       icon: Settings,         href: "/settings"       },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const { theme, toggle } = useTheme();

  return (
    <div style={{ width: "220px", flexShrink: 0, background: "var(--sidebar-bg)", borderRight: "1px solid var(--border-accent)", padding: "24px 14px", display: "flex", flexDirection: "column", gap: "4px", position: "sticky", top: 0, height: "100vh", backdropFilter: "blur(20px)" }}>

      <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--accent)", marginBottom: "24px", paddingLeft: "10px" }}>
        OpsPilot
      </div>

      {NAV.map(item => {
        const Icon    = item.icon;
        const active  = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
        const isAgent = item.href === "/agent";
        return (
          <button key={item.href} onClick={() => router.push(item.href)}
            style={{ display: "flex", alignItems: "center", gap: "11px", padding: "11px 14px", borderRadius: "12px", cursor: "pointer", color: active ? "var(--accent)" : "var(--text-secondary)", border: active ? "1px solid var(--border-accent)" : "1px solid transparent", background: active ? "rgba(57,255,136,0.07)" : "transparent", textAlign: "left", width: "100%", transition: "all 0.15s", position: "relative" }}>
            <Icon size={18} />
            <span style={{ fontSize: "14px", fontWeight: active ? 700 : 500 }}>{item.name}</span>
            {isAgent && (
              <span style={{ marginLeft: "auto", fontSize: "10px", fontWeight: 700, padding: "2px 6px", borderRadius: "6px", background: "rgba(57,255,136,0.15)", color: "var(--accent)", border: "1px solid rgba(57,255,136,0.3)" }}>AI</span>
            )}
          </button>
        );
      })}

      {/* Theme toggle at bottom */}
      <div style={{ marginTop: "auto", paddingTop: "16px", borderTop: "1px solid var(--border)" }}>
        <button onClick={toggle} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px 14px", borderRadius: "12px", cursor: "pointer", color: "var(--text-tertiary)", border: "1px solid transparent", background: "transparent", width: "100%", fontSize: "13px", transition: "all 0.15s" }}>
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </div>
  );
}
