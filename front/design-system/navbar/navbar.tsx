import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { NavButton } from '../navbutton/navbutton';
import type { NavBarProps } from './navbar.type';
import { useLocation } from "react-router-dom";

export default function NavBar({menu}:NavBarProps) {
    const [menuOpen, setMenuOpen] = useState(false);
    const page=useLocation().pathname;

    const checkSelection = (href:string, page:string, type:string|undefined):boolean => {
        if (type=='exact') {
        return page==href;
        } else {
        return page.startsWith(href);
        }
    }
    const getMenu = () => {
         return menu.map((item, index) => {
            return (
                <NavButton
                    key={index}
                    href={item.href}
                    selected={checkSelection(item.href, page, item.matcher)}
                    onClick={()=>setMenuOpen(false)}
                >{item.name}</NavButton>
            );
        });
    }

  return (
    <div className="min-h-3 flex flex-col bg-gray-900 text-white">
      {/* Navigation */}
      <nav className="border-b border-white px-4 py-3 flex items-center justify-between">
        <div className="text-xl font-bold">EasyAstro</div>

        {/* Desktop Menu */}
        <div className="hidden md:flex gap-4">
          {getMenu()}
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Ouvrir le menu"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>

      {/* Mobile Menu */}
            {menuOpen && (
        <div className="fixed top-0 left-0 w-full h-full bg-gray-950 bg-opacity-95 flex flex-col items-center justify-center z-50">
          <button
            className="absolute top-4 right-4"
            onClick={() => setMenuOpen(false)}
            aria-label="Fermer le menu"
          >
            <X size={32} className="text-white" />
          </button>

          <div className="flex flex-col items-center gap-8 text-2xl">
            {getMenu()}
          </div>
        </div>
      )}
      
    </div>
  );
}
