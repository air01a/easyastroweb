import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type NavButtonProps = {
  href: string;
  children: ReactNode;
  onClick?: () => void;
  selected: boolean;
};

export function NavButton({ href, children, onClick, selected }: NavButtonProps) {
  return (
    <Link
      to={href}
      onClick={onClick}
      className={
        selected
          ? "px-4 py-2 bg-red-500 rounded transition-colors"
          : "px-4 py-2 rounded hover:bg-white hover:text-gray-900 transition-colors"
      }
    >
      {children}
    </Link>
  );
}
