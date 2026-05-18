import { useState } from "react";

const navItems = [
  { label: "Dashboard", emoji: "📊", href: "#dashboard" },
  { label: "Projects", emoji: "📁", href: "#projects" },
  { label: "Tasks", emoji: "✅", href: "#tasks" },
  { label: "Settings", emoji: "⚙️", href: "#settings" },
];

export default function Sidebar({ activeItem = "Dashboard" }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden flex items-center px-4 py-3 bg-gray-900 border-b border-gray-700">
        <button
          onClick={() => setOpen((prev) => !prev)}
          aria-label="Toggle sidebar"
          className="text-gray-400 hover:text-white focus:outline-none"
        >
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current mb-1" />
          <span className="block w-6 h-0.5 bg-current" />
        </button>
        <span className="ml-3 text-white font-semibold text-sm">Menu</span>
      </div>

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-40 w-60 bg-gray-900 flex flex-col
          transform transition-transform duration-200 ease-in-out
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:static md:translate-x-0 md:flex
        `}
      >
        {/* Logo / brand */}
        <div className="px-6 py-5 border-b border-gray-700">
          <span className="text-white font-bold text-lg tracking-tight">MyApp</span>
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ label, emoji, href }) => {
            const isActive = label === activeItem;
            return (
              <a
                key={label}
                href={href}
                onClick={() => setOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                  transition-colors duration-150
                  ${
                    isActive
                      ? "bg-indigo-600 text-white"
                      : "text-gray-400 hover:bg-gray-800 hover:text-white"
                  }
                `}
              >
                <span className="text-base leading-none">{emoji}</span>
                {label}
              </a>
            );
          })}
        </nav>
      </aside>

      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}
    </>
  );
}
