import { NavLink } from "react-router-dom";

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
};

const navItems = [
  { to: "/", label: "资产总览", icon: "fa-chart-pie" },
  { to: "/funds", label: "基金管理", icon: "fa-list" },
  { to: "/holdings", label: "资产管家", icon: "fa-comments" },
  { to: "/rebalance", label: "调仓计划", icon: "fa-rotate" },
  { to: "/cycle-targets", label: "周期权重", icon: "fa-sliders" },
  { to: "/settings", label: "组合参数", icon: "fa-gear" },
  { to: "/prompts", label: "提示词管理", icon: "fa-feather-pointed" },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <div className="brand">
          <i className="fa-solid fa-compass" />
          {!collapsed && <span>Financial Steward</span>}
        </div>
        <button className="icon-button" onClick={onToggle} aria-label="toggle sidebar">
          <i className={`fa-solid ${collapsed ? "fa-bars" : "fa-xmark"}`} />
        </button>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `nav-item ${isActive ? "active" : ""}`
            }
          >
            <i className={`fa-solid ${item.icon}`} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
