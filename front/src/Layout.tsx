import React from 'react';
import { Outlet } from "react-router-dom";
import NavBar from '../design-system/navbar/navbar'; // adapte le chemin si besoin



// On ne peut plus passer `params.locale`, donc on détecte le locale autrement (par ex. navigateur)
const RootLayout: React.FC = () => {
  const navbarItems = [
    { name: 'Accueil', href: '/', matcher: 'exact' },
    { name: 'Catalog', href: '/catalog' },
    { name: 'Plan', href: '/plan' },
    { name: 'Config', href: '/config', matcher: 'exact' },
    { name: 'Observatory', href:'/config/observatory',  matcher: 'exact'},
        { name: 'Telescope', href:'/config/telescope',  matcher: 'exact'}

  ];


  return (
      <div className="font-sans antialiased min-h-screen flex flex-col bg-gradient-to-br from-black to-sky-800 text-white">
        <NavBar menu={navbarItems} />
        <main className="flex-1 min-h-screen p-4 bg-gradient-to-br from-black-950 to-sky-800 h-full"><Outlet /> </main>
      </div>
  );
};

export default RootLayout;
