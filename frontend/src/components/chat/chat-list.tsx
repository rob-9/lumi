import type { Chat } from "@/lib/types";
import clsx from "clsx";
import { MessageSquare, Plus } from "lucide-react";

interface Props {
  chats: Chat[];
  activeChatId: string;
}

export function ChatList({ chats, activeChatId }: Props) {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-3">
        <a
          href="/"
          className="flex items-center gap-2 rounded-lg border border-[var(--sidebar-hover)] px-3 py-2 text-xs font-medium text-[var(--sidebar-text)] transition-all hover:bg-[var(--sidebar-hover)] hover:border-[var(--sidebar-text-muted)] active:scale-[0.98]"
        >
          <Plus size={14} className="transition-transform group-hover:rotate-90" />
          New chat
        </a>
      </div>

      <div className="px-3 space-y-0.5">
        {chats.map((chat, i) => (
          <a
            key={chat.id}
            href={`/chat/${chat.id}`}
            className={clsx(
              "flex items-start gap-2 rounded-lg px-3 py-2 transition-all duration-200 animate-fade-in",
              chat.id === activeChatId
                ? "bg-[var(--sidebar-active)] text-white active-indicator"
                : "text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover)] hover:translate-x-0.5"
            )}
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <MessageSquare size={14} className="mt-0.5 shrink-0 opacity-50" />
            <div className="min-w-0">
              <p className="truncate text-xs font-medium">{chat.title}</p>
              <p className="text-[10px] text-[var(--sidebar-text-muted)]">
                {chat.sublab.replace(/-/g, " ")}
              </p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
