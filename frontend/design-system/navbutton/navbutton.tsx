import Link from "next/link";

export function NavButton({
  href,
  children,
  onClick,
  selected,
}: {
  href: string;
  children: React.ReactNode;
  onClick?: () => void;
  selected: boolean
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={selected? "px-4 py-2 bg-red-500 rounded transition-colors":"px-4 py-2 rounded hover:bg-white hover:text-gray-900 transition-colors"}
    >
      {children}
    </Link>
  );
}